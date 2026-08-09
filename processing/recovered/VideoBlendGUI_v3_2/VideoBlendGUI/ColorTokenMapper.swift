
import Foundation

struct ColorTokenMapper {
    static func map(meta: ColorMetadata) -> ColorMetadata {
        func mapSpace(_ s: String?) -> String? {
            guard let s else { return nil }
            switch s.lowercased() {
            case "bt709": return "bt709"
            case "bt2020nc", "bt2020ncl": return "bt2020ncl"
            case "bt2020c", "bt2020cl": return "bt2020cl"
            default: return nil // skip unknowns
            }
        }
        func mapTrc(_ t: String?) -> String? {
            guard let t else { return nil }
            switch t.lowercased() {
            case "bt709": return "bt709"
            case "smpte2084": return "smpte2084"
            case "arib-std-b67", "hlg": return "arib-std-b67"
            case "iec61966-2-1", "srgb": return "iec61966-2-1"
            case "iec61966-2-4": return "iec61966-2-4"
            default: return nil
            }
        }
        func mapPrimaries(_ p: String?) -> String? {
            guard let p else { return nil }
            switch p.lowercased() {
            case "bt709": return "bt709"
            case "bt2020": return "bt2020"
            default: return nil
            }
        }
        func mapRange(_ r: String?) -> String? {
            guard let r else { return nil }
            switch r.lowercased() {
            case "tv", "mpeg": return "tv"
            case "pc", "jpeg": return "pc"
            default: return nil
            }
        }
        return ColorMetadata(range: mapRange(meta.range),
                             space: mapSpace(meta.space),
                             trc: mapTrc(meta.trc),
                             primaries: mapPrimaries(meta.primaries))
    }
}
