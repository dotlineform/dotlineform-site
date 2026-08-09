
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
    case prores = "prores_ks"
    
    var uiLabel: String {
        switch self {
        case .x264: return "H.264 (libx264)"
        case .h264_videotoolbox: return "H.264 (VideoToolbox)"
        case .prores: return "ProRes (prores_ks)"
        }
    }
}

enum ProResProfile: Int, CaseIterable, Codable {
    case proxy = 0, lt = 1, standard = 2, hq = 3, _4444 = 4, _4444xq = 5
    
    var label: String {
        switch self {
        case .proxy: return "Proxy"
        case .lt: return "LT"
        case .standard: return "Standard"
        case .hq: return "HQ"
        case ._4444: return "4444"
        case ._4444xq: return "4444 XQ"
        }
    }
}

struct BlendState: Codable, Equatable {
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
    var proresProfile: ProResProfile = .hq
    var prores444: Bool = false
    var outputURL: URL?
}

struct FilterPlan {
    let filter: String
    let videoMap: String
    let audioMap: String?
    let colorMeta: ColorMetadata?
}

struct ColorMetadata {
    var range: String?
    var space: String?
    var trc: String?
    var primaries: String?
}
