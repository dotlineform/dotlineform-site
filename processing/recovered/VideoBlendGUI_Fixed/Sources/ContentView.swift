
import SwiftUI
import AppKit
import UniformTypeIdentifiers

@MainActor
struct ContentView: View {
    // Inputs
    @State private var video1URL: URL?
    @State private var video2URL: URL?
    @State private var reverseSecond = true
    @State private var mixAudio = true
    @State private var opacity: Double = 0.5
    @State private var enhancement: Enhancement = .normalize

    // Encoding
    @State private var crf: Double = 20
    @State private var preset: Preset = .medium
    @State private var audioDuration: AudioDuration = .shortest

    // Slow motion / interpolation
    @State private var enableSlowMo = false
    @State private var slowFactor: Double = 0.5      // 0.25x … 1.0x (playback speed)
    @State private var targetFPS: Int = 60           // output fps for minterpolate

    // Output
    @State private var outputURL: URL?

    // Status
    @State private var isRunning = false
    @State private var logText = ""
    @State private var detectedSize: CGSize? // from video1
    @State private var hasA1 = false
    @State private var hasA2 = false

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Video Blend GUI (FFmpeg)")
                .font(.title2).bold()

            GroupBox("Source Videos") {
                VStack(alignment: .leading, spacing: 10) {
                    HStack {
                        fileRow(title: "Video 1 (forward)", url: $video1URL)
                        Button("Choose…") { pickFile(for: 1) }
                    }
                    HStack {
                        fileRow(title: "Video 2 (reverse?)", url: $video2URL)
                        Button("Choose…") { pickFile(for: 2) }
                    }
                    Toggle("Reverse second video", isOn: $reverseSecond)
                    Toggle("Mix audio", isOn: $mixAudio)
                    HStack {
                        Text("Opacity: \(String(format: "%.2f", opacity))")
                        Slider(value: $opacity, in: 0...1)
                    }
                    HStack {
                        Picker("Enhancement", selection: $enhancement) {
                            ForEach(Enhancement.allCases, id: \.self) { e in
                                Text(e.label).tag(e)
                            }
                        }
                        .pickerStyle(.segmented)
                        Spacer()
                    }
                }
            }

            GroupBox("Slow-motion & Interpolation (optional)") {
                VStack(alignment: .leading, spacing: 10) {
                    Toggle("Enable slow-motion with frame interpolation", isOn: $enableSlowMo)
                    HStack {
                        Text("Playback speed: \(String(format: "%.2fx", slowFactor))")
                        Slider(value: $slowFactor, in: 0.25...1.0, step: 0.05)
                        Text("1.0x = normal")
                    }
                    HStack {
                        Text("Target FPS:")
                        Stepper("\(targetFPS) fps", value: $targetFPS, in: 24...120, step: 6)
                        Text("Used by minterpolate")
                            .foregroundStyle(.secondary)
                    }
                }
            }

            GroupBox("Encoding") {
                VStack(alignment: .leading, spacing: 10) {
                    HStack {
                        Text("CRF (quality): \(Int(crf))")
                        Slider(value: $crf, in: 16...28, step: 1)
                        Text("Preset")
                        Picker("", selection: $preset) {
                            ForEach(Preset.allCases, id: \.self) { p in
                                Text(p.rawValue).tag(p)
                            }
                        }
                        .frame(width: 140)
                    }
                    HStack {
                        Text("Audio timeline: ")
                        Picker("", selection: $audioDuration) {
                            ForEach(AudioDuration.allCases, id: \.self) { d in
                                Text(d.rawValue).tag(d)
                            }
                        }
                        .frame(width: 160)
                        Spacer()
                    }
                }
            }

            GroupBox("Output") {
                VStack(alignment: .leading, spacing: 10) {
                    HStack {
                        Text(outputURL?.path(percentEncoded: false) ?? "No file selected")
                            .lineLimit(1)
                            .truncationMode(.middle)
                        Spacer()
                        Button("Save As…") { chooseOutput() }
                    }
                }
            }

            HStack {
                Button(isRunning ? "Working…" : "Run") {
                    Task { await run() }
                }
                .disabled(!canRun || isRunning)

                Button("Clear Log") { logText = "" }
                Spacer()

                if let detectedSize {
                    Text("Ref size: \(Int(detectedSize.width))×\(Int(detectedSize.height))")
                        .foregroundStyle(.secondary)
                }
            }

            ScrollView {
                Text(logText)
                    .font(.system(.footnote, design: .monospaced))
                    .frame(maxWidth: .infinity, alignment: .topLeading)
            }
            .background(Color(NSColor.textBackgroundColor))
            .border(Color.secondary, width: 1)
        }
        .padding(16)
        .onChange(of: video1URL) { _ in Task { await probeAll() } }
        .onChange(of: video2URL) { _ in Task { await probeAll() } }
    }

    // MARK: - Derived

    var canRun: Bool {
        video1URL != nil && video2URL != nil
    }

    // MARK: - UI Helpers

    @ViewBuilder
    func fileRow(title: String, url: Binding<URL?>) -> some View {
        HStack {
            Text(title).frame(width: 180, alignment: .leading)
            Text(url.wrappedValue?.path(percentEncoded: false) ?? "—")
                .lineLimit(1)
                .truncationMode(.middle)
            Spacer()
        }
    }

    func pickFile(for idx: Int) {
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [.movie, .mpeg4Movie, .quickTimeMovie]
        panel.canChooseDirectories = false
        panel.canChooseFiles = true
        panel.allowsMultipleSelection = false
        if panel.runModal() == .OK, let url = panel.url {
            if idx == 1 { video1URL = url } else { video2URL = url }
        }
    }

    func chooseOutput() {
        let save = NSSavePanel()
        save.allowedContentTypes = [.mpeg4Movie]
        save.nameFieldStringValue = "blend_fwd_rev_\(timestamp()).mp4"
        if save.runModal() == .OK {
            outputURL = save.url
        }
    }

    // MARK: - Core

    func ffmpegPath() -> String? {
        // Search common locations then PATH
        let candidates = [
            "/opt/homebrew/bin/ffmpeg",
            "/usr/local/bin/ffmpeg"
        ]
        for c in candidates where FileManager.default.isExecutableFile(atPath: c) {
            return c
        }
        if let which = try? shell("/usr/bin/which", ["ffmpeg"]).trimmingCharacters(in: .whitespacesAndNewlines),
           !which.isEmpty {
            return which
        }
        return nil
    }

    func ffprobePath() -> String? {
        let candidates = [
            "/opt/homebrew/bin/ffprobe",
            "/usr/local/bin/ffprobe"
        ]
        for c in candidates where FileManager.default.isExecutableFile(atPath: c) {
            return c
        }
        if let which = try? shell("/usr/bin/which", ["ffprobe"]).trimmingCharacters(in: .whitespacesAndNewlines),
           !which.isEmpty {
            return which
        }
        return nil
    }

    func run() async {
        guard let ffmpeg = ffmpegPath() else {
            appendLog("❌ FFmpeg not found. Install with: brew install ffmpeg")
            return
        }
        guard ffprobePath() != nil else {
            appendLog("❌ FFprobe not found. Install with: brew install ffmpeg")
            return
        }
        guard let v1 = video1URL, let v2 = video2URL else { return }

        isRunning = true
        defer { isRunning = false }

        // Probe dimensions & audio presence
        await probeAll()
        guard let size = detectedSize else {
            appendLog("❌ Could not read dimensions from Video 1.")
            return
        }

        // Output path
        let outURL = outputURL ?? v1.deletingLastPathComponent()
            .appendingPathComponent("blend_fwd_rev_\(timestamp()).mp4")
        self.outputURL = outURL

        let w = Int(size.width), h = Int(size.height)

        // Build video chain:
        // Optional reverse on [1:v], then scale/pad to match [0:v] size
        let preReverse = reverseSecond ? "reverse," : ""
        let videoStage1 = "[1:v]" + preReverse + "scale=\(w):\(h):force_original_aspect_ratio=decrease,pad=\(w):\(h):(ow-iw)/2:(oh-ih)/2[revv]"

        // Blend forward [0:v] with [revv]
        let blend = "[0:v][revv]blend=all_mode=overlay:all_opacity=\(fmt(opacity))[blended]"

        // Enhancement to [blended] -> [vpre]
        let enhance = enhancement.filterChain(outputLabel: "vpre")

        // Optional slow motion: setpts + minterpolate (else pass-through via null)
        let slowMoVideoChain: String
        if enableSlowMo && slowFactor < 0.999 {
            let setpts = "setpts=\(fmt(1.0 / slowFactor))*PTS"
            slowMoVideoChain = "[vpre]\(setpts)[vset];[vset]minterpolate=fps=\(targetFPS)[v]"
        } else {
            slowMoVideoChain = "[vpre]null[v]"
        }

        // --- Audio path (robust to missing streams) ---
        var audioChain = ""
        var audioOutLabel: String? = nil

        if mixAudio {
            if hasA1 && hasA2 {
                // Mix forward (video1) + (video2 possibly reversed)
                let audioPre = reverseSecond ? "areverse," : ""
                audioChain  = "[0:a]volume=\(fmt(opacity))[a0];"
                audioChain += "[1:a]" + audioPre + "volume=\(fmt(opacity))[a1];"
                audioChain += "[a0][a1]amix=inputs=2:duration=\(audioDuration.rawValue)[amixed]"
                if enableSlowMo && slowFactor < 0.999 {
                    audioChain += ";\(atemposChain(input: "[amixed]", factor: slowFactor))"
                    audioOutLabel = "aout"
                } else {
                    audioOutLabel = "amixed"
                }
            } else if hasA1 {
                audioChain  = "[0:a]volume=\(fmt(opacity))[aonly]"
                if enableSlowMo && slowFactor < 0.999 {
                    audioChain += ";\(atemposChain(input: "[aonly]", factor: slowFactor))"
                    audioOutLabel = "aout"
                } else {
                    audioOutLabel = "aonly"
                }
            } else if hasA2 {
                let audioPre = reverseSecond ? "areverse," : ""
                audioChain  = "[1:a]" + audioPre + "volume=\(fmt(opacity))[aonly]"
                if enableSlowMo && slowFactor < 0.999 {
                    audioChain += ";\(atemposChain(input: "[aonly]", factor: slowFactor))"
                    audioOutLabel = "aout"
                } else {
                    audioOutLabel = "aonly"
                }
            }
        }

        // Compose filter graph as a single string (semicolon-separated)
        let filterComplex = [videoStage1, blend, enhance, slowMoVideoChain, audioChain]
            .filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
            .joined(separator: ";")

        appendLog("▶️ Running FFmpeg…")
        appendLog(filterComplex)

        // Build args
        var args = [
            "-hide_banner", "-y",
            "-i", v1.path,
            "-i", v2.path,
            "-filter_complex", filterComplex,
            "-map", "[v]"
        ]
        if let aLabel = audioOutLabel {
            args += ["-map", "[\(aLabel)]", "-c:a", "aac", "-b:a", "192k"]
        } else {
            args += ["-an"]
        }
        args += [
            "-c:v", "libx264", "-crf", "\(Int(crf))",
            "-preset", preset.rawValue,
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            outURL.path
        ]

        do {
            try await runProcess(launchPath: ffmpeg, arguments: args)
            appendLog("✅ Done: \(outURL.path)")
            revealInFinder(outURL)
        } catch {
            appendLog("❌ FFmpeg failed: \(error.localizedDescription)")
        }
    }

    func probeAll() async {
        detectedSize = nil
        hasA1 = false
        hasA2 = false

        guard let ffprobe = ffprobePath() else { return }
        if let v1 = video1URL {
            if let sz = try? probeSize(ffprobe: ffprobe, url: v1) {
                detectedSize = sz
                appendLog("ℹ️ Video1 size \(Int(sz.width))x\(Int(sz.height))")
            }
            hasA1 = (try? hasAudio(ffprobe: ffprobe, url: v1)) ?? false
        }
        if let v2 = video2URL {
            hasA2 = (try? hasAudio(ffprobe: ffprobe, url: v2)) ?? false
        }
    }

    // MARK: - FFprobe helpers

    func probeSize(ffprobe: String, url: URL) throws -> CGSize {
        let out = try shell(ffprobe, [
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0:s= "
        ] + [url.path])
        let comps = out.trimmingCharacters(in: .whitespacesAndNewlines).split(separator: " ")
        if comps.count == 2, let w = Int(comps[0]), let h = Int(comps[1]) {
            return CGSize(width: w, height: h)
        }
        throw NSError(domain: "Probe", code: 1, userInfo: [NSLocalizedDescriptionKey: "No size"])
    }

    func hasAudio(ffprobe: String, url: URL) throws -> Bool {
        // Returns 0 if an audio stream exists, non-zero otherwise
        let status = try shellStatus(ffprobe, [
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=codec_type",
            "-of", "csv=p=0"
        ] + [url.path])
        return status == 0
    }

    // MARK: - Process utils

    func runProcess(launchPath: String, arguments: [String]) async throws {
        try await withCheckedThrowingContinuation { cont in
            let task = Process()
            task.launchPath = launchPath
            task.arguments = arguments

            let pipe = Pipe()
            task.standardError = pipe
            task.standardOutput = pipe

            pipe.fileHandleForReading.readabilityHandler = { handle in
                if let str = String(data: handle.availableData, encoding: .utf8), !str.isEmpty {
                    DispatchQueue.main.async { self.appendLog(str) }
                }
            }

            task.terminationHandler = { p in
                pipe.fileHandleForReading.readabilityHandler = nil
                if p.terminationStatus == 0 {
                    cont.resume()
                } else {
                    cont.resume(throwing: NSError(domain: "FFmpeg",
                                                  code: Int(p.terminationStatus),
                                                  userInfo: [NSLocalizedDescriptionKey: "Exit \(p.terminationStatus)"]))
                }
            }

            do { try task.run() } catch { cont.resume(throwing: error) }
        }
    }

    @discardableResult
    func shell(_ launch: String, _ args: [String]) throws -> String {
        let task = Process()
        task.launchPath = launch
        task.arguments = args
        let outPipe = Pipe()
        task.standardOutput = outPipe
        task.standardError = Pipe()
        try task.run()
        task.waitUntilExit()
        let data = outPipe.fileHandleForReading.readDataToEndOfFile()
        return String(data: data, encoding: .utf8) ?? ""
    }

    func shellStatus(_ launch: String, _ args: [String]) throws -> Int32 {
        let task = Process()
        task.launchPath = launch
        task.arguments = args
        task.standardOutput = Pipe()
        task.standardError = Pipe()
        try task.run()
        task.waitUntilExit()
        return task.terminationStatus
    }

    // MARK: - Helpers

    func fmt(_ x: Double) -> String { String(format: "%.6f", x) }

    /// Build a chain of `atempo` steps to achieve the target slowFactor (0.25–1.0).
    /// `atempo` supports 0.5–2.0 per step. For slowing below 0.5, chain multiple 0.5s.
    func atemposChain(input: String, factor: Double) -> String {
        var remain = factor
        var labels: [String] = []
        var currentIn = input
        var idx = 0

        while remain <= 0.49 {
            let out = (idx == 0) ? "[a_t0]" : "[a_t\(idx)]"
            labels.append("\(currentIn)atempo=0.5\(out)")
            currentIn = out
            remain /= 0.5
            idx += 1
        }
        if abs(remain - 1.0) > 1e-6 {
            labels.append("\(currentIn)atempo=\(fmt(remain))[aout]")
        } else {
            labels.append("\(currentIn)anull[aout]")
        }
        return labels.joined(separator: ";")
    }

    func timestamp() -> String {
        let f = DateFormatter()
        f.dateFormat = "yyyyMMdd-HHmmss"
        return f.string(from: Date())
    }

    func appendLog(_ s: String) {
        logText.append(s.hasSuffix("\n") ? s : s + "\n")
    }

    func revealInFinder(_ url: URL) {
        NSWorkspace.shared.activateFileViewerSelecting([url])
    }
}

// MARK: - Models

enum Enhancement: CaseIterable {
    case normalize, histEq, eqPreset, none

    var label: String {
        switch self {
        case .normalize: return "Normalize"
        case .histEq:    return "HistEq"
        case .eqPreset:  return "EQ"
        case .none:      return "None"
        }
    }

    /// Returns a filter chain applying enhancement to [blended], output label [outputLabel].
    func filterChain(outputLabel: String) -> String {
        switch self {
        case .normalize:
            // auto-levels with small headroom to avoid clipping
            return "[blended]normalize=blackpt=0.02:whitept=0.98[\(outputLabel)]"
        case .histEq:
            // modest histogram equalization
            return "[blended]histeq=strength=0.8:intensity=0.3[\(outputLabel)]"
        case .eqPreset:
            // gentle contrast/brightness/saturation tweak
            return "[blended]eq=contrast=1.2:brightness=0.02:saturation=1.05[\(outputLabel)]"
        case .none:
            // pass-through via null filter
            return "[blended]null[\(outputLabel)]"
        }
    }
}

enum Preset: String, CaseIterable {
    case ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
}

enum AudioDuration: String, CaseIterable {
    case shortest, longest, first
}
