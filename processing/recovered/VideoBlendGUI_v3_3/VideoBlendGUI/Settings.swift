
import Foundation
import SwiftUI

final class AppSettings: ObservableObject {
    @AppStorage("customFFmpegPath") var customFFmpegPath: String = ""
    @AppStorage("customFFprobePath") var customFFprobePath: String = ""
    
    func ffmpegPathOrDefault() -> String {
        let c = customFFmpegPath.trimmingCharacters(in: .whitespacesAndNewlines)
        if !c.isEmpty, FileManager.default.isExecutableFile(atPath: c) { return c }
        for p in ["/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"] {
            if FileManager.default.isExecutableFile(atPath: p) { return p }
        }
        return "/usr/bin/ffmpeg"
    }
    
    func ffprobePathOrDefault() -> String {
        let c = customFFprobePath.trimmingCharacters(in: .whitespacesAndNewlines)
        if !c.isEmpty, FileManager.default.isExecutableFile(atPath: c) { return c }
        for p in ["/opt/homebrew/bin/ffprobe", "/usr/local/bin/ffprobe"] {
            if FileManager.default.isExecutableFile(atPath: p) { return p }
        }
        return "/usr/bin/ffprobe"
    }
}

struct PreferencesView: View {
    @EnvironmentObject var settings: AppSettings
    @State private var tmpFFmpeg: String = ""
    @State private var tmpFFprobe: String = ""
    @State private var feedback: String = ""
    
    var body: some View {
        Form {
            Section("Custom Binary Paths (optional)") {
                HStack {
                    Text("FFmpeg")
                    TextField("/opt/homebrew/bin/ffmpeg", text: $tmpFFmpeg)
                    Button("Browse…") { browse { url in tmpFFmpeg = url.path } }
                }
                HStack {
                    Text("FFprobe")
                    TextField("/opt/homebrew/bin/ffprobe", text: $tmpFFprobe)
                    Button("Browse…") { browse { url in tmpFFprobe = url.path } }
                }
                HStack {
                    Spacer()
                    Button("Save") { save() }
                }
                if !feedback.isEmpty {
                    Text(feedback).font(.footnote).foregroundColor(.secondary)
                }
            }
        }
        .padding()
        .onAppear {
            tmpFFmpeg = settings.customFFmpegPath
            tmpFFprobe = settings.customFFprobePath
        }
    }
    
    func browse(pick: @escaping (URL)->Void) {
        let p = NSOpenPanel()
        p.canChooseFiles = true; p.canChooseDirectories = false
        p.allowsMultipleSelection = false
        if p.runModal() == .OK, let url = p.url { pick(url) }
    }
    
    func save() {
        var msgs: [String] = []
        if !tmpFFmpeg.isEmpty && !FileManager.default.isExecutableFile(atPath: tmpFFmpeg) {
            msgs.append("FFmpeg path not executable")
        }
        if !tmpFFprobe.isEmpty && !FileManager.default.isExecutableFile(atPath: tmpFFprobe) {
            msgs.append("FFprobe path not executable")
        }
        if msgs.isEmpty {
            settings.customFFmpegPath = tmpFFmpeg
            settings.customFFprobePath = tmpFFprobe
            feedback = "Saved."
        } else {
            feedback = msgs.joined(separator: " · ")
        }
    }
}
