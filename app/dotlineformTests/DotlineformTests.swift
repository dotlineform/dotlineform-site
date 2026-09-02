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

    @Test func bridgeAcceptsOnlyTheRotateSymbolAction() throws {
        let request = try AboutBridgeRequest.decode(
            messageBody: ["action": "rotate-symbol"]
        )

        #expect(request == AboutBridgeRequest(action: .rotateSymbol))
        #expect(throws: AboutBridgeContractError.self) {
            try AboutBridgeRequest.decode(
                messageBody: ["action": "unknown"]
            )
        }
        #expect(throws: AboutBridgeContractError.self) {
            try AboutBridgeRequest.decode(
                messageBody: [
                    "action": "rotate-symbol",
                    "unexpected": true,
                ]
            )
        }
    }

    @Test func bridgeReturnsBoundedSuccessAndFailureResults() throws {
        let success = try #require(
            try AboutBridgeResult.rotated.javaScriptObject() as? [String: Any]
        )
        let failure = try #require(
            try AboutBridgeResult.invalidRequest.javaScriptObject() as? [String: Any]
        )

        #expect(success["state"] as? String == "succeeded")
        #expect(success["quarterTurns"] as? Int == 1)
        #expect(success.count == 2)
        #expect(failure["state"] as? String == "failed")
        #expect(failure["message"] as? String == "The page sent an invalid rotate-symbol request.")
        #expect(failure.count == 2)
    }

}
