import Foundation

struct BlendState {
    var video1URL: URL?
    var video2URL: URL?
    var reverseSecond = true
    var mixAudio = true
    var opacity = 0.5
    var enhancement: Enhancement = .normalize
    var crf = 20
    var preset: Preset = .medium
    var audioDuration: AudioDuration = .shortest
    var enableSlowMo = false
    var slowFactor = 0.5
    var targetFPS = 60
    var outputURL: URL?
}
