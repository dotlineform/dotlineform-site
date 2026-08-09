import SwiftUI

@main
struct VideoBlendGUIApp: App {
    @StateObject private var vm = BlendViewModel()
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(vm)
                .frame(minWidth: 820, minHeight: 700)
        }
    }
}
