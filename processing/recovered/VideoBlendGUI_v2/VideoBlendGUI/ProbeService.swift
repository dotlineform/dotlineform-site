
import Foundation
import CoreGraphics

struct FFProbeStreams: Decodable {
    let streams: [FFStream]
}
struct FFStream: Decodable {
    let codec_type: String?
    let width: Int?
    let height: Int?
    let r_frame_rate: String?
}

struct ProbeService {
    func inspect(url: URL) async throws -> FFProbeStreams {
        let data = try shellData(path: ffprobePath(), args: [
            "-v","error",
            "-print_format","json",
            "-show_streams",
            url.path
        ])
        return try JSONDecoder().decode(FFProbeStreams.self, from: data)
    }
    
    func size(from streams: FFProbeStreams) -> CGSize? {
        if let s = streams.streams.first(where: { $0.codec_type == "video" }),
           let w = s.width, let h = s.height {
            return CGSize(width: w, height: h)
        }
        return nil
    }
    
    func hasAudio(from streams: FFProbeStreams) -> Bool {
        streams.streams.contains { $0.codec_type == "audio" }
    }
    
    // MARK: - Tools
    
    private func ffprobePath() -> String {
        for c in ["/opt/homebrew/bin/ffprobe", "/usr/local/bin/ffprobe"] {
            if FileManager.default.isExecutableFile(atPath: c) { return c }
        }
        return "/usr/bin/ffprobe"
    }
    
    private func shellData(path: String, args: [String]) throws -> Data {
        let p = Process()
        p.launchPath = path
        p.arguments = args
        let out = Pipe()
        p.standardOutput = out
        p.standardError = Pipe()
        try p.run()
        p.waitUntilExit()
        return out.fileHandleForReading.readDataToEndOfFile()
    }
}
