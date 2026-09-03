//
//  WorkOnTheDecayedClient.swift
//  dotlineform
//

import Foundation

nonisolated struct WorkOnTheDecayedClient: AboutRotationService {
    private struct RequestBody: Encodable {
        let action = "rotate-symbol"
    }

    private struct ResponseBody: Decodable {
        let quarterTurns: Int
    }

    private static let acceptedErrorCodes = Set([
        "invalid-json",
        "invalid-request",
        "request-too-large",
        "unsupported-media-type",
    ])

    let baseURL: URL
    let session: URLSession

    init(baseURL: URL, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
    }

    func rotateSymbol() async throws -> AboutRotation {
        let request = try Self.makeRequest(baseURL: baseURL)

        do {
            let (data, response) = try await session.data(for: request)
            return try Self.rotation(data: data, response: response)
        } catch let error as AboutRotationServiceError {
            throw error
        } catch {
            throw Self.serviceError(from: error)
        }
    }

    static func makeRequest(baseURL: URL) throws -> URLRequest {
        let endpoint = baseURL.appendingPathComponent("v1/rotate-symbol")
        var request = URLRequest(url: endpoint, timeoutInterval: 12)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(RequestBody())
        return request
    }

    static func rotation(data: Data, response: URLResponse) throws -> AboutRotation {
        guard
            let response = response as? HTTPURLResponse,
            response.mimeType == "application/json"
        else {
            throw AboutRotationServiceError.invalidResponse
        }

        guard response.statusCode == 200 else {
            if (400..<500).contains(response.statusCode) {
                try validateErrorResponse(data)
                throw AboutRotationServiceError.rejected
            }

            throw AboutRotationServiceError.unavailable
        }

        let object = try jsonObject(data)
        guard
            object.count == 1,
            object.keys.first == "quarterTurns"
        else {
            throw AboutRotationServiceError.invalidResponse
        }

        let body: ResponseBody
        do {
            body = try JSONDecoder().decode(ResponseBody.self, from: data)
        } catch {
            throw AboutRotationServiceError.invalidResponse
        }

        guard body.quarterTurns == 1 else {
            throw AboutRotationServiceError.invalidResponse
        }

        return AboutRotation(quarterTurns: body.quarterTurns)
    }

    static func serviceError(from error: Error) -> AboutRotationServiceError {
        if error is CancellationError {
            return .cancelled
        }

        guard let urlError = error as? URLError else {
            return .unavailable
        }

        switch urlError.code {
        case .cancelled:
            return .cancelled
        case .timedOut:
            return .timedOut
        default:
            return .unavailable
        }
    }

    private static func validateErrorResponse(_ data: Data) throws {
        let object = try jsonObject(data)
        guard
            object.count == 1,
            let error = object["error"] as? [String: Any],
            error.count == 1,
            let code = error["code"] as? String,
            acceptedErrorCodes.contains(code)
        else {
            throw AboutRotationServiceError.invalidResponse
        }
    }

    private static func jsonObject(_ data: Data) throws -> [String: Any] {
        do {
            guard
                let object = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            else {
                throw AboutRotationServiceError.invalidResponse
            }

            return object
        } catch let error as AboutRotationServiceError {
            throw error
        } catch {
            throw AboutRotationServiceError.invalidResponse
        }
    }
}
