import SwiftUI

@main
struct VideoBlendGUIApp: App {
    @StateObject private var settings: AppSettings
    @StateObject private var vm: BlendViewModel
    
    init() {
        let s = AppSettings()
        _settings = StateObject(wrappedValue: s)
        _vm = StateObject(wrappedValue: BlendViewModel(settings: s))
    }
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(vm)
                .environmentObject(settings)
                .frame(minWidth: 880, minHeight: 760)
        }
        Settings {
            PreferencesView()
                .environmentObject(settings)
                .frame(width: 520, height: 260)
        }
    }
}
