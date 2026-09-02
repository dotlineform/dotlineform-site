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
            try AboutBridgeResult.rotated(
                by: AboutRotation(quarterTurns: 1)
            ).javaScriptObject() as? [String: Any]
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

    @Test func serviceBuildsAndAcceptsOnlyTheRotationContract() throws {
        let baseURL = try #require(URL(string: "https://example.com/"))
        let request = try WorkOnTheDecayedClient.makeRequest(baseURL: baseURL)
        let requestURL = try #require(request.url)
        let httpBody = try #require(request.httpBody)
        let requestBody = try #require(
            try JSONSerialization.jsonObject(with: httpBody)
                as? [String: Any]
        )

        #expect(request.url?.absoluteString == "https://example.com/v1/rotate-symbol")
        #expect(request.httpMethod == "POST")
        #expect(request.value(forHTTPHeaderField: "Content-Type") == "application/json")
        #expect(request.timeoutInterval == 12)
        #expect(requestBody["action"] as? String == "rotate-symbol")
        #expect(requestBody.count == 1)

        let response = try #require(
            HTTPURLResponse(
                url: requestURL,
                statusCode: 200,
                httpVersion: nil,
                headerFields: ["Content-Type": "application/json"]
            )
        )
        let rotation = try WorkOnTheDecayedClient.rotation(
            data: Data(#"{"quarterTurns":1}"#.utf8),
            response: response
        )

        #expect(rotation == AboutRotation(quarterTurns: 1))
        #expect(throws: AboutRotationServiceError.self) {
            try WorkOnTheDecayedClient.rotation(
                data: Data(#"{"quarterTurns":1,"unexpected":true}"#.utf8),
                response: response
            )
        }
        #expect(throws: AboutRotationServiceError.self) {
            try WorkOnTheDecayedClient.rotation(
                data: Data(#"{"quarterTurns":2}"#.utf8),
                response: response
            )
        }
    }

    @Test func serviceTranslatesBoundedFailures() throws {
        let url = try #require(URL(string: "https://example.com/v1/rotate-symbol"))
        let rejection = try #require(
            HTTPURLResponse(
                url: url,
                statusCode: 400,
                httpVersion: nil,
                headerFields: ["Content-Type": "application/json"]
            )
        )

        #expect(throws: AboutRotationServiceError.self) {
            try WorkOnTheDecayedClient.rotation(
                data: Data(#"{"error":{"code":"invalid-request"}}"#.utf8),
                response: rejection
            )
        }
        #expect(
            WorkOnTheDecayedClient.serviceError(from: URLError(.cancelled))
                == .cancelled
        )
        #expect(
            WorkOnTheDecayedClient.serviceError(from: URLError(.timedOut))
                == .timedOut
        )
        #expect(
            WorkOnTheDecayedClient.serviceError(from: URLError(.cannotConnectToHost))
                == .unavailable
        )
    }

    @Test func bridgeMapsServiceFailuresToPageOwnedResults() throws {
        let timeout = try #require(
            try AboutBridgeResult.serviceFailure(
                AboutRotationServiceError.timedOut
            ).javaScriptObject() as? [String: Any]
        )
        let invalidResponse = try #require(
            try AboutBridgeResult.serviceFailure(
                AboutRotationServiceError.invalidResponse
            ).javaScriptObject() as? [String: Any]
        )

        #expect(timeout["state"] as? String == "failed")
        #expect(timeout["message"] as? String == "The rotation service took too long to respond.")
        #expect(timeout.count == 2)
        #expect(invalidResponse["state"] as? String == "failed")
        #expect(invalidResponse["message"] as? String == "The rotation service returned an invalid response.")
        #expect(invalidResponse.count == 2)
    }

    @Test func localServiceRemainsAvailableForTests() async throws {
        let rotation = try await LocalAboutRotationService().rotateSymbol()

        #expect(rotation == AboutRotation(quarterTurns: 1))
    }

}
