
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
    case x265 = "libx265"
    case hevc_videotoolbox = "hevc_videotoolbox"
    case prores = "prores_ks"
    
    var uiLabel: String {
        switch self {
        case .x264: return "H.264 (libx264)"
        case .h264_videotoolbox: return "H.264 (VideoToolbox)"
        case .x265: return "HEVC (libx265)"
        case .hevc_videotoolbox: return "HEVC (VideoToolbox)"
        case .prores: return "ProRes (prores_ks)"
        }
    }
    
    var usesCRF: Bool {
        switch self {
        case .x264, .x265: return TrueLiteral()
        default: return false
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

enum InterpQuality: String, CaseIterable, Codable {
    case fast, balanced, high
    
    var label: String {
        switch self {
        case .fast: return "Fast"
        case .balanced: return "Balanced"
        case .high: return "High"
        }
    }
    
    func minterpolateString(targetFPS: Int) -> String {
        switch self {
        case .fast: return "minterpolate=fps=\(targetFPS)"
        case .balanced: return "minterpolate=fps=\(targetFPS):mi_mode=mci:me_mode=bidir"
        case .high: return "minterpolate=fps=\(targetFPS):mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
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
    var interpQuality: InterpQuality = .balanced
    var normalizeAmix: Bool = true
    var preserveAudioFormat: Bool = false
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

// small helper for Python templating conflicts
func TrueLiteral() -> Bool { return true }
