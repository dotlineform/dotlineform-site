
import Foundation
import CoreGraphics

struct FFmpegCommandBuilder {
    
    func buildPlan(state: BlendState, probe: ProbeService, settings: AppSettings) async throws -> FilterPlan {
        guard let v1 = state.video1URL, let v2 = state.video2URL else {
            throw NSError(domain: "Inputs", code: 1, userInfo: [NSLocalizedDescriptionKey:"Missing input URLs"])
        }
        
        let p1 = try await probe.inspect(url: v1, ffprobePath: settings.ffprobePathOrDefault())
        let p2 = try await probe.inspect(url: v2, ffprobePath: settings.ffprobePathOrDefault())
        
        guard let size = probe.size(from: p1) else {
            throw NSError(domain: "Probe", code: 2, userInfo: [NSLocalizedDescriptionKey:"Could not read size from video1"])
        }
        let hasA1 = probe.hasAudio(from: p1)
        let hasA2 = probe.hasAudio(from: p2)
        let colorMeta = probe.colorMetadata(from: p1)
        
        let w = Int(size.width), h = Int(size.height)
        var lines: [String] = []
        
        // video2 preprocess
        let maybeReverse = state.reverseSecond ? "reverse," : ""
        lines.append("[1:v]\(maybeReverse)scale=\(w):\(h):force_original_aspect_ratio=decrease,pad=\(w):\(h):(ow-iw)/2:(oh-ih)/2[revv]")
        
        // blend
        lines.append("[0:v][revv]blend=all_mode=overlay:all_opacity=\(fmt(state.opacity))[blended]")
        
        // enhancement
        lines.append(enhanceChain(enh: state.enhancement, input: "[blended]", out: "[vpre]"))
        
        // slow-mo (optional)
        if state.enableSlowMo && state.slowFactor < 0.999 {
            lines.append("[vpre]setpts=\(fmt(1.0 / state.slowFactor))*PTS[vset]")
            let mi = state.interpQuality.minterpolateString(targetFPS: state.targetFPS)
            lines.append("[vset]\(mi)[v]")
        } else {
            lines.append("[vpre]null[v]")
        }
        
        // audio
        var audioMap: String? = nil
        if state.mixAudio && (hasA1 || hasA2) {
            // Determine target audio format
            let fmtA = targetAudioFormat(preserve: state.preserveAudioFormat, p1: p1, p2: p2, hasA1: hasA1, hasA2: hasA2)
            let aformat = "aformat=sample_rates=\(fmtA.sampleRate):channel_layouts=\(fmtA.layout)"
            
            if hasA1 && hasA2 {
                let rev = state.reverseSecond ? "areverse," : ""
                lines.append("[0:a]\(aformat),volume=\(fmt(state.opacity))[a0]")
                lines.append("[1:a]\(rev)\(aformat),volume=\(fmt(state.opacity))[a1]")
                let norm = state.normalizeAmix ? ":normalize=1" : ""
                lines.append("[a0][a1]amix=inputs=2:duration=\(state.audioDuration.rawValue)\(norm)[amixed]")
                if state.enableSlowMo && state.slowFactor < 0.999 {
                    lines.append(atemposChain(input: "[amixed]", factor: state.slowFactor))
                    audioMap = "[aout]"
                } else { audioMap = "[amixed]" }
            } else if hasA1 {
                lines.append("[0:a]\(aformat),volume=\(fmt(state.opacity))[aonly]")
                if state.enableSlowMo && state.slowFactor < 0.999 {
                    lines.append(atemposChain(input: "[aonly]", factor: state.slowFactor))
                    audioMap = "[aout]"
                } else { audioMap = "[aonly]" }
            } else {
                let rev = state.reverseSecond ? "areverse," : ""
                lines.append("[1:a]\(rev)\(aformat),volume=\(fmt(state.opacity))[aonly]")
                if state.enableSlowMo && state.slowFactor < 0.999 {
                    lines.append(atemposChain(input: "[aonly]", factor: state.slowFactor))
                    audioMap = "[aout]"
                } else { audioMap = "[aonly]" }
            }
        }
        
        return FilterPlan(filter: lines.joined(separator: ";"),
                          videoMap: "[v]",
                          audioMap: audioMap,
                          colorMeta: colorMeta)
    }
    
    private func targetAudioFormat(preserve: Bool, p1: FFProbeStreams, p2: FFProbeStreams, hasA1: Bool, hasA2: Bool) -> (sampleRate: Int, layout: String) {
        if !preserve { return (48000, "stereo") }
        // Try to preserve if both inputs agree. Otherwise return safe default 48k stereo.
        func meta(_ p: FFProbeStreams) -> (Int?, String?) {
            if let s = p.streams.first(where: { $0.codec_type == "audio" }) {
                let sr = Int(s.sample_rate ?? "")
                let layout = s.channel_layout
                return (sr, layout)
            }
            return (nil, nil)
        }
        let a1 = hasA1 ? meta(p1) : (nil, nil)
        let a2 = hasA2 ? meta(p2) : (nil, nil)
        if let sr1 = a1.0, let lay1 = a1.1, hasA2 == false {
            return (sr1, lay1)
        }
        if let sr2 = a2.0, let lay2 = a2.1, hasA1 == false {
            return (sr2, lay2)
        }
        if let sr1 = a1.0, let lay1 = a1.1, let sr2 = a2.0, let lay2 = a2.1, sr1 == sr2, lay1 == lay2 {
            return (sr1, lay1)
        }
        return (48000, "stereo")
    }
    
    private func enhanceChain(enh: Enhancement, input: String, out: String) -> String {
        switch enh {
        case .normalize:
            return "\(input)normalize=blackpt=0.02:whitept=0.98\(out)"
        case .histEq:
            return "\(input)histeq=strength=0.8:intensity=0.3\(out)"
        case .eqPreset:
            return "\(input)eq=contrast=1.2:brightness=0.02:saturation=1.05\(out)"
        case .none:
            return "\(input)null\(out)"
        }
    }
    
    private func fmt(_ x: Double) -> String { String(format: Locale(identifier:"en_US_POSIX"), "%.6f", x) }
    
    private func atemposChain(input: String, factor: Double) -> String {
        var remain = factor, inLabel = input, idx = 0, parts: [String] = []
        while remain <= 0.49 {
            let out = idx == 0 ? "[a_t0]" : "[a_t\(idx)]"
            parts.append("\(inLabel)atempo=0.5\(out)")
            inLabel = out; idx += 1; remain /= 0.5
        }
        if abs(remain - 1.0) > 1e-6 {
            parts.append("\(inLabel)atempo=\(fmt(remain))[aout]")
        } else {
            parts.append("\(inLabel)anull[aout]")
        }
        return parts.joined(separator: ";")
    }
}
