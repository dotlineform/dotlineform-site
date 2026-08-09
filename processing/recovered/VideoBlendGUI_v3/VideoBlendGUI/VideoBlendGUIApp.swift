import SwiftUI

@main
struct VideoBlendGUIApp: App {
    @StateObject private var vm = BlendViewModel()
    @StateObject private var settings = AppSettings()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(vm)
                .environmentObject(settings)
                .frame(minWidth: 860, minHeight: 720)
        }
        Settings {
            PreferencesView()
                .environmentObject(settings)
                .frame(width: 520, height: 260)
        }
    }
}
