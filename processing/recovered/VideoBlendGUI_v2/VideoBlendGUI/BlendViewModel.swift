
import SwiftUI
import AppKit

@MainActor
final class BlendViewModel: ObservableObject {
    @Published var state = BlendState()
    @Published var log: String = ""
    @Published var isRunning: Bool = false
    @Published var detectedSize: CGSize? = nil
    
    private let probe = ProbeService()
    private let builder = FFmpegCommandBuilder()
    private var currentProcess: Process? = nil
    
    var canRun: Bool { state.video1URL != nil && state.video2URL != nil }
    
    func run() async {
        guard let v1 = state.video1URL else { append("❌ Select Video 1"); return }
        guard let v2 = state.video2URL else { append("❌ Select Video 2"); return }
        
        do {
            isRunning = true; defer { isRunning = false }
            try await probeAll()
            
            // Validate output path
            let outURL = state.outputURL ?? v1.deletingLastPathComponent()
                .appendingPathComponent("blend_fwd_rev_\(timestamp()).mp4")
            state.outputURL = outURL
            
            let plan = try await builder.buildPlan(state: state, probe: probe)
            append("▶️ Filter graph:\n\(plan.filter)\n")
            let args = buildArgs(plan: plan, outURL: outURL)
            try await runProcess(launchPath: ffmpegPath(), arguments: args)
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
        let streams = try await probe.inspect(url: v1)
        detectedSize = probe.size(from: streams)
        append("ℹ️ Video1 size \(detectedSize.map { "\(Int($0.width))x\(Int($0.height))" } ?? "unknown")")
    }
    
    // MARK: - Args
    
    private func buildArgs(plan: FilterPlan, outURL: URL) -> [String] {
        var args: [String] = ["-hide_banner", "-y",
                              "-i", state.video1URL!.path,
                              "-i", state.video2URL!.path,
                              "-filter_complex", plan.filter,
                              "-map", plan.videoMap]
        
        if let a = plan.audioMap {
            args += ["-map", a]
        } else {
            args += ["-an"]
        }
        
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
        }
        
        if plan.audioMap != nil {
            args += ["-c:a", "aac", "-b:a", "192k"]
        }
        
        args += ["-movflags", "+faststart", outURL.path]
        return args
    }
    
    // MARK: - FFmpeg paths
    
    private func ffmpegPath() -> String {
        for c in ["/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"] {
            if FileManager.default.isExecutableFile(atPath: c) { return c }
        }
        return "/usr/bin/ffmpeg" // fallback; user can adjust PATH
    }
    
    // MARK: - Process
    
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
    
    // MARK: - Utils
    
    func timestamp() -> String {
        let f = DateFormatter(); f.dateFormat = "yyyyMMdd-HHmmss"
        return f.string(from: Date())
    }
    
    func append(_ s: String) {
        log.append(s.hasSuffix("\n") ? s : s + "\n")
    }
    
    func revealInFinder(_ url: URL) {
        NSWorkspace.shared.activateFileViewerSelecting([url])
    }
}
