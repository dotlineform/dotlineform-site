//
//  AppConfiguration.swift
//  dotlineform
//

import Foundation

nonisolated enum AppConfiguration {
    static let workOnTheDecayedBaseURL: URL = {
        guard let url = URL(
            string: "https://work-on-the-decayed-334553986819.europe-west2.run.app/"
        ) else {
            preconditionFailure("The retained Work On The Decayed URL is invalid.")
        }

        return url
    }()
}
