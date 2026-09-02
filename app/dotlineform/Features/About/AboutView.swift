//
//  AboutView.swift
//  dotlineform
//

import SwiftUI

enum AboutPage {
    nonisolated static func url(in bundle: Bundle = .main) -> URL? {
        bundle.url(forResource: "about", withExtension: "html")
    }
}

struct AboutView: View {
    private let pageURL: URL?

    init(bundle: Bundle = .main) {
        pageURL = AboutPage.url(in: bundle)
    }

    var body: some View {
        if let pageURL {
            WebKitHost(pageURL: pageURL)
        } else {
            ContentUnavailableView(
                "About Page Unavailable",
                systemImage: "doc.questionmark",
                description: Text("The bundled about.html resource is missing.")
            )
        }
    }
}

#Preview {
    AboutView()
}
