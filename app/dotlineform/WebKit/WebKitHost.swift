//
//  WebKitHost.swift
//  dotlineform
//

import SwiftUI
import WebKit

struct WebKitHost: View {
    let pageURL: URL
    let rotationService: any AboutRotationService

    var body: some View {
        PlatformWebView(
            pageURL: pageURL,
            rotationService: rotationService
        )
    }
}

private final class WebKitHostCoordinator: NSObject, WKScriptMessageHandlerWithReply {
    private static let messageHandlerName = "about"

    private let rotationService: any AboutRotationService
    private var loadedURL: URL?

    init(rotationService: any AboutRotationService) {
        self.rotationService = rotationService
    }

    func makeWebView() -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.userContentController.addScriptMessageHandler(
            self,
            contentWorld: .page,
            name: Self.messageHandlerName
        )
        return WKWebView(frame: .zero, configuration: configuration)
    }

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

    func userContentController(
        _ userContentController: WKUserContentController,
        didReceive message: WKScriptMessage,
        replyHandler: @escaping @MainActor @Sendable (Any?, String?) -> Void
    ) {
        do {
            guard message.name == Self.messageHandlerName else {
                throw AboutBridgeContractError.invalidRequest
            }

            let request = try AboutBridgeRequest.decode(messageBody: message.body)
            switch request.action {
            case .rotateSymbol:
                Task { @MainActor [rotationService] in
                    let result: AboutBridgeResult

                    do {
                        let rotation = try await rotationService.rotateSymbol()
                        result = .rotated(by: rotation)
                    } catch {
                        result = .serviceFailure(error)
                    }

                    Self.reply(with: result, using: replyHandler)
                }
            }
        } catch {
            Self.reply(with: .invalidRequest, using: replyHandler)
        }
    }

    private static func reply(
        with result: AboutBridgeResult,
        using replyHandler: @escaping @MainActor @Sendable (Any?, String?) -> Void
    ) {
        do {
            replyHandler(try result.javaScriptObject(), nil)
        } catch {
            replyHandler(nil, "The application could not encode its bridge response.")
        }
    }
}

#if os(macOS)
private struct PlatformWebView: NSViewRepresentable {
    let pageURL: URL
    let rotationService: any AboutRotationService

    func makeCoordinator() -> WebKitHostCoordinator {
        WebKitHostCoordinator(rotationService: rotationService)
    }

    func makeNSView(context: Context) -> WKWebView {
        let webView = context.coordinator.makeWebView()
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
    let rotationService: any AboutRotationService

    func makeCoordinator() -> WebKitHostCoordinator {
        WebKitHostCoordinator(rotationService: rotationService)
    }

    func makeUIView(context: Context) -> WKWebView {
        let webView = context.coordinator.makeWebView()
        context.coordinator.load(pageURL, in: webView)
        return webView
    }

    func updateUIView(_ webView: WKWebView, context: Context) {
        context.coordinator.load(pageURL, in: webView)
    }
}
#endif
