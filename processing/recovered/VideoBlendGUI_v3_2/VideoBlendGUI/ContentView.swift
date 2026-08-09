
import SwiftUI
import AppKit
import UniformTypeIdentifiers

@MainActor
struct ContentView: View {
    @EnvironmentObject var vm: BlendViewModel
    @EnvironmentObject var settings: AppSettings
    
    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Video Blend GUI (FFmpeg) — v3.2")
                .font(.title2).bold()
            
            GroupBox("Source Videos") {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        fileRow(title: "Video 1 (forward)", url: vm.state.video1URL)
                        Button("Choose…") { pickFile(for: 1) }
                    }
                    HStack {
                        fileRow(title: "Video 2 (reverse?)", url: vm.state.video2URL)
                        Button("Choose…") { pickFile(for: 2) }
                    }
                    Toggle("Reverse second video", isOn: $vm.state.reverseSecond)
                    Toggle("Mix audio", isOn: $vm.state.mixAudio)
                    HStack {
                        Text("Opacity: \(String(format: "%.2f", vm.state.opacity))")
                        Slider(value: $vm.state.opacity, in: 0...1)
                    }
                    HStack {
                        Picker("Enhancement", selection: $vm.state.enhancement) {
                            ForEach(Enhancement.allCases, id: \.self) { e in
                                Text(e.label).tag(e)
                            }
                        }.pickerStyle(.segmented)
                        Spacer()
                    }
                }
            }
            
            GroupBox("Slow-motion & Interpolation (optional)") {
                VStack(alignment: .leading, spacing: 8) {
                    Toggle("Enable slow-motion with frame interpolation", isOn: $vm.state.enableSlowMo)
                    HStack {
                        Text("Playback speed: \(String(format: "%.2fx", vm.state.slowFactor))")
                        Slider(value: $vm.state.slowFactor, in: 0.25...1.0, step: 0.05)
                        Text("1.0x = normal").foregroundStyle(.secondary)
                    }
                    HStack {
                        Text("Target FPS:")
                        Stepper("\(vm.state.targetFPS) fps", value: $vm.state.targetFPS, in: 24...120, step: 6)
                        Text("Used by minterpolate").foregroundStyle(.secondary)
                    }
                }
            }
            
            GroupBox("Encoding") {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Encoder")
                        Picker("", selection: $vm.state.encoder) {
                            ForEach(VideoEncoder.allCases, id: \.self) { e in
                                Text(e.uiLabel).tag(e)
                            }
                        }.frame(width: 200)
                        
                        if vm.state.encoder == .x264 {
                            Text("CRF: \(Int(vm.state.crf))")
                            Slider(value: $vm.state.crf, in: 16...28, step: 1)
                            Text("Preset")
                            Picker("", selection: $vm.state.preset) {
                                ForEach(Preset.allCases, id: \.self) { p in
                                    Text(p.rawValue).tag(p)
                                }
                            }.frame(width: 140)
                        } else if vm.state.encoder == .prores {
                            Text("Profile")
                            Picker("", selection: $vm.state.proresProfile) {
                                ForEach(ProResProfile.allCases, id: \.self) { pr in
                                    Text(pr.label).tag(pr)
                                }
                            }.frame(width: 160)
                            Toggle("4:4:4 10-bit", isOn: $vm.state.prores444)
                        }
                    }
                    HStack {
                        Text("Audio timeline: ")
                        Picker("", selection: $vm.state.audioDuration) {
                            ForEach(AudioDuration.allCases, id: \.self) { d in
                                Text(d.rawValue).tag(d)
                            }
                        }.frame(width: 160)
                        Toggle("Normalize audio mix", isOn: $vm.state.normalizeAmix)
                        Spacer()
                    }
                }
            }
            
            GroupBox("Output") {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text(vm.state.outputURL?.path(percentEncoded: false) ?? "No file selected")
                            .lineLimit(1).truncationMode(.middle)
                        Spacer()
                        Button("Save As…") { chooseOutput() }
                    }
                    if let c = vm.colorMetaDescription {
                        Text("Color tags (from Video 1): \(c)")
                            .font(.footnote).foregroundStyle(.secondary)
                    }
                }
            }
            
            HStack {
                Button(vm.isRunning ? "Working…" : "Run") {
                    Task { await vm.run() }
                }
                .disabled(!vm.canRun || vm.isRunning)
                
                Button("Cancel") { vm.cancel() }
                    .disabled(!vm.isRunning)
                
                Button("Clear Log") { vm.log = "" }
                Spacer()
                
                if let size = vm.detectedSize {
                    Text("Ref size: \(Int(size.width))×\(Int(size.height))")
                        .foregroundStyle(.secondary)
                }
            }
            
            ScrollView {
                Text(vm.log)
                    .font(.system(.footnote, design: .monospaced))
                    .frame(maxWidth: .infinity, alignment: .topLeading)
            }
            .background(Color(NSColor.textBackgroundColor))
            .border(Color.secondary, width: 1)
        }
        .padding(16)
        .onChange(of: vm.state.video1URL) { _ in Task { await vm.probeAll() } }
        .onChange(of: vm.state.video2URL) { _ in Task { await vm.probeAll() } }
    }
    
    @ViewBuilder
    func fileRow(title: String, url: URL?) -> some View {
        HStack {
            Text(title).frame(width: 200, alignment: .leading)
            Text(url?.path(percentEncoded: false) ?? "—")
                .lineLimit(1).truncationMode(.middle)
            Spacer()
        }
    }
    
    func pickFile(for idx: Int) {
        let p = NSOpenPanel()
        p.allowedContentTypes = [.movie, .mpeg4Movie, .quickTimeMovie]
        p.canChooseFiles = true; p.canChooseDirectories = false
        p.allowsMultipleSelection = false
        if p.runModal() == .OK, let url = p.url {
            if idx == 1 { vm.state.video1URL = url } else { vm.state.video2URL = url }
        }
    }
    
    func chooseOutput() {
        let s = NSSavePanel()
        if vm.state.encoder == .prores {
            s.allowedContentTypes = [.movie, .quickTimeMovie]
        } else {
            s.allowedContentTypes = [.mpeg4Movie, .movie]
        }
        s.nameFieldStringValue = vm.suggestedFileName()
        if s.runModal() == .OK { vm.state.outputURL = s.url }
    }
}
