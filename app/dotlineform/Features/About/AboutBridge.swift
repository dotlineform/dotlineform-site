//
//  AboutBridge.swift
//  dotlineform
//

import Foundation

nonisolated enum AboutBridgeAction: String, Codable, Equatable, Sendable {
    case rotateSymbol = "rotate-symbol"
}

nonisolated struct AboutBridgeRequest: Codable, Equatable, Sendable {
    let action: AboutBridgeAction

    static func decode(messageBody: Any) throws -> Self {
        guard
            let object = messageBody as? [String: Any],
            object.count == 1,
            let rawAction = object["action"] as? String,
            let action = AboutBridgeAction(rawValue: rawAction)
        else {
            throw AboutBridgeContractError.invalidRequest
        }

        return Self(action: action)
    }
}

nonisolated struct AboutBridgeResult: Codable, Equatable, Sendable {
    enum State: String, Codable, Equatable, Sendable {
        case succeeded
        case failed
    }

    let state: State
    let quarterTurns: Int?
    let message: String?

    static let rotated = Self(
        state: .succeeded,
        quarterTurns: 1,
        message: nil
    )

    static let invalidRequest = Self(
        state: .failed,
        quarterTurns: nil,
        message: "The page sent an invalid rotate-symbol request."
    )

    func javaScriptObject() throws -> Any {
        let data = try JSONEncoder().encode(self)
        return try JSONSerialization.jsonObject(with: data)
    }
}

nonisolated enum AboutBridgeContractError: Error {
    case invalidRequest
}
