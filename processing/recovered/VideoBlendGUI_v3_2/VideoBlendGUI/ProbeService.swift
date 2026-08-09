
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
    // Color metadata keys (names follow ffprobe JSON)
    let color_range: String?
    let color_space: String?
    let color_transfer: String?
    let color_primaries: String?
}

struct ProbeService {
    // Non-blocking: run ffprobe off the main actor/thread
    nonisolated func inspect(url: URL, ffprobePath: String) async throws -> FFProbeStreams {
        try await withCheckedThrowingContinuation { cont in
            DispatchQueue.global(qos: .userInitiated).async {
                do {
                    let data = try shellData(path: ffprobePath, args: [
                        "-v","error",
                        "-print_format","json",
                        "-show_streams",
                        url.path
                    ])
                    let streams = try JSONDecoder().decode(FFProbeStreams.self, from: data)
                    cont.resume(returning: streams)
                } catch {
                    cont.resume(throwing: error)
                }
            }
        }
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
    
    func colorMetadata(from streams: FFProbeStreams) -> ColorMetadata? {
        guard let s = streams.streams.first(where: { $0.codec_type == "video" }) else { return nil }
        return ColorMetadata(range: s.color_range, space: s.color_space, trc: s.color_transfer, primaries: s.color_primaries)
    }
    
    // MARK: - Tools
    
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
