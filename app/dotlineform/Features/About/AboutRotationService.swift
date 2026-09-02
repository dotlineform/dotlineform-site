//
//  AboutRotationService.swift
//  dotlineform
//

nonisolated struct AboutRotation: Equatable, Sendable {
    let quarterTurns: Int
}

nonisolated protocol AboutRotationService: Sendable {
    func rotateSymbol() async throws -> AboutRotation
}

nonisolated enum AboutRotationServiceError: Error, Equatable, Sendable {
    case cancelled
    case timedOut
    case rejected
    case invalidResponse
    case unavailable
}

nonisolated struct LocalAboutRotationService: AboutRotationService {
    let rotation: AboutRotation

    init(rotation: AboutRotation = AboutRotation(quarterTurns: 1)) {
        self.rotation = rotation
    }

    func rotateSymbol() async throws -> AboutRotation {
        rotation
    }
}
