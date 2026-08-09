
import Foundation
import CoreGraphics

struct FFmpegCommandBuilder {
    
    func buildPlan(state: BlendState, probe: ProbeService, settings: AppSettings) async throws -> FilterPlan {
        guard let v1 = state.video1URL, let v2 = state.video2URL else {
            throw NSError(domain: "Inputs", code: 1, userInfo: [NSLocalizedDescriptionKey:"Missing input URLs"])
        }
        
        // Probe video1 (reference size + color), and audio presence for both
        let p1 = try await probe.inspect(url: v1, ffprobePath: settings.ffprobePathOrDefault() ?? "/usr/bin/ffprobe")
        let p2 = try await probe.inspect(url: v2, ffprobePath: settings.ffprobePathOrDefault() ?? "/usr/bin/ffprobe")
        
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
            // Balanced preset for minterpolate; can be made selectable
            lines.append("[vset]minterpolate=fps=\(state.targetFPS):mi_mode=mci:me_mode=bidir[v]")
        } else {
            lines.append("[vpre]null[v]")
        }
        
        // audio
        var audioMap: String? = nil
        if state.mixAudio && (hasA1 || hasA2) {
            if hasA1 && hasA2 {
                let rev = state.reverseSecond ? "areverse," : ""
                lines.append("[0:a]volume=\(fmt(state.opacity))[a0]")
                lines.append("[1:a]\(rev)volume=\(fmt(state.opacity))[a1]")
                // normalize SR + layout, avoid clipping if requested
                lines.append("[a0]aformat=sample_rates=48000:channel_layouts=stereo[a0f]")
                lines.append("[a1]aformat=sample_rates=48000:channel_layouts=stereo[a1f]")
                let norm = state.normalizeAmix ? ":normalize=1" : ""
                lines.append("[a0f][a1f]amix=inputs=2:duration=\(state.audioDuration.rawValue)\(norm)[amixed]")
                if state.enableSlowMo && state.slowFactor < 0.999 {
                    lines.append(atemposChain(input: "[amixed]", factor: state.slowFactor))
                    audioMap = "[aout]"
                } else { audioMap = "[amixed]" }
            } else if hasA1 {
                lines.append("[0:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=\(fmt(state.opacity))[aonly]")
                if state.enableSlowMo && state.slowFactor < 0.999 {
                    lines.append(atemposChain(input: "[aonly]", factor: state.slowFactor))
                    audioMap = "[aout]"
                } else { audioMap = "[aonly]" }
            } else {
                let rev = state.reverseSecond ? "areverse," : ""
                lines.append("[1:a]\(rev)aformat=sample_rates=48000:channel_layouts=stereo,volume=\(fmt(state.opacity))[aonly]")
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
