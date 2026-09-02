//
//  WebKitHost.swift
//  dotlineform
//

import SwiftUI
import WebKit

struct WebKitHost: View {
    let pageURL: URL

    var body: some View {
        PlatformWebView(pageURL: pageURL)
    }
}

private final class WebKitHostCoordinator {
    private var loadedURL: URL?

    func load(_ pageURL: URL, in webView: WKWebView) {
        guard loadedURL != pageURL else {
            return
        }

        loadedURL = pageURL
        webView.loadFileURL(
            pageURL,
            allowingReadAccessTo: pageURL.deletingLastPathComponent()
        )
    }
}

#if os(macOS)
private struct PlatformWebView: NSViewRepresentable {
    let pageURL: URL

    func makeCoordinator() -> WebKitHostCoordinator {
        WebKitHostCoordinator()
    }

    func makeNSView(context: Context) -> WKWebView {
        let webView = WKWebView(frame: .zero)
        context.coordinator.load(pageURL, in: webView)
        return webView
    }

    func updateNSView(_ webView: WKWebView, context: Context) {
        context.coordinator.load(pageURL, in: webView)
    }
}
#elseif os(iOS)
private struct PlatformWebView: UIViewRepresentable {
    let pageURL: URL

    func makeCoordinator() -> WebKitHostCoordinator {
        WebKitHostCoordinator()
    }

    func makeUIView(context: Context) -> WKWebView {
        let webView = WKWebView(frame: .zero)
        context.coordinator.load(pageURL, in: webView)
        return webView
    }

    func updateUIView(_ webView: WKWebView, context: Context) {
        context.coordinator.load(pageURL, in: webView)
    }
}
#endif
