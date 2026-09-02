//
//  DotlineformTests.swift
//  dotlineformTests
//
//  Created by Michael Davies on 02/09/2026.
//

import Foundation
import Testing
@testable import dotlineform

struct DotlineformTests {

    @Test func aboutPageIsBundled() throws {
        let pageURL = try #require(AboutPage.url())

        #expect(pageURL.lastPathComponent == "about.html")
    }

}
