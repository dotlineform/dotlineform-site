
import SwiftUI
import AppKit

@MainActor
final class BlendViewModel: ObservableObject {
    @Published var state = BlendState()
    @Published var log: String = ""
    @Published var isRunning: Bool = false
    @Published var detectedSize: CGSize? = nil
    @Published var colorMetaDescription: String? = nil
    
    private let probe = ProbeService()
    private let builder = FFmpegCommandBuilder()
    private var currentProcess: Process? = nil
    
    let settings: AppSettings
    init(settings: AppSettings) { self.settings = settings }
    
    var canRun: Bool { state.video1URL != nil && state.video2URL != nil }
    
    func run() async {
        guard let v1 = state.video1URL else { append("❌ Select Video 1"); return }
        guard state.video2URL != nil else { append("❌ Select Video 2"); return }
        
        do {
            isRunning = true; defer { isRunning = false }
            
            let ffmpeg = settings.ffmpegPathOrDefault()
            let ffprobe = settings.ffprobePathOrDefault()
            try verifyExecutable(ffmpeg, label: "FFmpeg")
            try verifyExecutable(ffprobe, label: "FFprobe")
            
            try await probeAll()
            
            let outURL = state.outputURL ?? v1.deletingLastPathComponent()
                .appendingPathComponent(suggestedFileName())
            state.outputURL = outURL
            
            let plan = try await builder.buildPlan(state: state, probe: probe, settings: settings)
            append("▶️ Filter graph:\n\(plan.filter.replacingOccurrences(of: ";", with: ";\n"))\n")
            let args = buildArgs(plan: plan, outURL: outURL)
            try await runProcess(launchPath: ffmpeg, arguments: args)
            append("✅ Done: \(outURL.path)")
            revealInFinder(outURL)
        } catch {
            append("❌ \(error.localizedDescription)")
        }
    }
    
    func cancel() {
        currentProcess?.terminate()
        append("⏹️ Cancel requested")
    }
    
    func probeAll() async throws {
        guard let v1 = state.video1URL else { return }
        let ffprobe = settings.ffprobePathOrDefault()
        let streams = try await probe.inspect(url: v1, ffprobePath: ffprobe)
        detectedSize = probe.size(from: streams)
        let meta = probe.colorMetadata(from: streams)
        colorMetaDescription = meta.flatMap { m in
            var parts: [String] = []
            if let s = m.space { parts.append("space=\(s)") }
            if let p = m.primaries { parts.append("primaries=\(p)") }
            if let t = m.trc { parts.append("trc=\(t)") }
            if let r = m.range { parts.append("range=\(r)") }
            return parts.joined(separator: ", ")
        }
    }
    
    private func buildArgs(plan: FilterPlan, outURL: URL) -> [String] {
        var args: [String] = ["-hide_banner", "-y",
                              "-i", state.video1URL!.path,
                              "-i", state.video2URL!.path,
                              "-filter_complex", plan.filter,
                              "-map", plan.videoMap]
        
        if let a = plan.audioMap { args += ["-map", a] } else { args += ["-an"] }
        
        switch state.encoder {
        case .x264:
            args += ["-c:v", state.encoder.rawValue,
                     "-crf", "\(Int(state.crf))",
                     "-preset", state.preset.rawValue,
                     "-pix_fmt", "yuv420p"]
        case .h264_videotoolbox:
            args += ["-c:v", state.encoder.rawValue,
                     "-b:v", "0",
                     "-allow_sw", "1",
                     "-pix_fmt", "yuv420p"]
        case .x265:
            args += ["-c:v", state.encoder.rawValue,
                     "-crf", "\(Int(state.crf))",
                     "-preset", state.preset.rawValue,
                     "-pix_fmt", "yuv420p"]
        case .hevc_videotoolbox:
            args += ["-c:v", state.encoder.rawValue,
                     "-b:v", "0",
                     "-allow_sw", "1",
                     "-pix_fmt", "yuv420p"]
        case .prores:
            args += ["-c:v", state.encoder.rawValue,
                     "-profile:v", "\(state.proresProfile.rawValue)",
                     "-pix_fmt", state.prores444 ? "yuv444p10le" : "yuv422p10le"]
        }
        
        if plan.audioMap != nil {
            args += ["-c:a", "aac", "-b:a", "192k"]
        }
        
        if let meta = plan.colorMeta {
            let mapped = ColorTokenMapper.map(meta: meta)
            if let r = mapped.range { args += ["-color_range", r] }
            if let s = mapped.space { args += ["-colorspace", s] }
            if let t = mapped.trc { args += ["-color_trc", t] }
            if let p = mapped.primaries { args += ["-color_primaries", p] }
        }
        
        args += ["-movflags", "+faststart", outURL.path]
        return args
    }
    
    private func runProcess(launchPath: String, arguments: [String]) async throws {
        try await withCheckedThrowingContinuation { cont in
            let p = Process()
            currentProcess = p
            p.launchPath = launchPath
            p.arguments = arguments
            let pipe = Pipe()
            p.standardError = pipe
            p.standardOutput = pipe
            
            pipe.fileHandleForReading.readabilityHandler = { [weak self] h in
                if let s = String(data: h.availableData, encoding: .utf8), !s.isEmpty {
                    Task { @MainActor in self?.append(s) }
                }
            }
            p.terminationHandler = { [weak self] proc in
                pipe.fileHandleForReading.readabilityHandler = nil
                self?.currentProcess = nil
                if proc.terminationStatus == 0 { cont.resume() }
                else {
                    cont.resume(throwing: NSError(domain:"FFmpeg", code: Int(proc.terminationStatus),
                                                 userInfo:[NSLocalizedDescriptionKey:"Exit \(proc.terminationStatus)"]))
                }
            }
            do { try p.run() } catch { cont.resume(throwing: error) }
        }
    }
    
    func suggestedFileName() -> String {
        let base = "blend_fwd_rev_\(timestamp())"
        switch state.encoder {
        case .prores: return base + ".mov"
        default: return base + ".mp4"
        }
    }
    
    func timestamp() -> String {
        let f = DateFormatter(); f.dateFormat = "yyyyMMdd-HHmmss"
        return f.string(from: Date())
    }
    
    func append(_ s: String) { log.append(s.hasSuffix("\n") ? s : s + "\n") }
    func revealInFinder(_ url: URL) { NSWorkspace.shared.activateFileViewerSelecting([url]) }
    
    func verifyExecutable(_ p: String, label: String) throws {
        guard FileManager.default.isExecutableFile(atPath: p) else {
            throw NSError(domain: "Paths", code: 1,
                          userInfo: [NSLocalizedDescriptionKey:
                            "\(label) not executable at path: \(p). Set a valid path in Preferences (⌘,)."])
        }
    }
}
