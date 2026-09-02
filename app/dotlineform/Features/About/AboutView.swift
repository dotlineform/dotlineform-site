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
    private let rotationService: any AboutRotationService

    init(
        bundle: Bundle = .main,
        rotationService: any AboutRotationService
    ) {
        pageURL = AboutPage.url(in: bundle)
        self.rotationService = rotationService
    }

    var body: some View {
        if let pageURL {
            WebKitHost(
                pageURL: pageURL,
                rotationService: rotationService
            )
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
    AboutView(rotationService: LocalAboutRotationService())
}
