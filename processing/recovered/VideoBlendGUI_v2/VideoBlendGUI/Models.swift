
import Foundation
import CoreGraphics

enum Enhancement: CaseIterable, Codable {
    case normalize, histEq, eqPreset, none
    
    var label: String {
        switch self {
        case .normalize: return "Normalize"
        case .histEq:    return "HistEq"
        case .eqPreset:  return "EQ"
        case .none:      return "None"
        }
    }
}

enum Preset: String, CaseIterable, Codable {
    case ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
}

enum AudioDuration: String, CaseIterable, Codable {
    case shortest, longest, first
}

enum VideoEncoder: String, CaseIterable, Codable {
    case x264 = "libx264"
    case h264_videotoolbox = "h264_videotoolbox"
}

struct BlendState: Codable {
    var video1URL: URL?
    var video2URL: URL?
    var reverseSecond: Bool = true
    var mixAudio: Bool = true
    var opacity: Double = 0.5
    var enhancement: Enhancement = .normalize
    var crf: Double = 20
    var preset: Preset = .medium
    var audioDuration: AudioDuration = .shortest
    var enableSlowMo: Bool = false
    var slowFactor: Double = 0.5
    var targetFPS: Int = 60
    var normalizeAmix: Bool = true
    var encoder: VideoEncoder = .x264
    var outputURL: URL?
}

struct FilterPlan {
    let filter: String
    let videoMap: String
    let audioMap: String?
}
