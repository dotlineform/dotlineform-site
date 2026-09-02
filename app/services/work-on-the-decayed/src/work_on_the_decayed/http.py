"""Flask HTTP adapter for the provider-neutral rotation operation."""

from typing import Final

from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge

from .operation import InvalidRotationRequest, RotateSymbolRequest, rotate_symbol


ROTATE_SYMBOL_PATH: Final = "/v1/rotate-symbol"
MAX_REQUEST_BYTES: Final = 1_024


def _error_response(code: str, status: int) -> tuple[object, int]:
    return jsonify({"error": {"code": code}}), status


def create_app() -> Flask:
    """Create the WSGI application without cloud-provider dependencies."""

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_REQUEST_BYTES

    @app.post(ROTATE_SYMBOL_PATH)
    def rotate_symbol_route() -> tuple[object, int] | object:
        if not request.is_json:
            return _error_response("unsupported-media-type", 415)

        try:
            payload = request.get_json(cache=False)
        except BadRequest:
            return _error_response("invalid-json", 400)

        try:
            operation_request = RotateSymbolRequest.from_payload(payload)
        except InvalidRotationRequest:
            return _error_response("invalid-request", 400)

        return jsonify(rotate_symbol(operation_request).to_payload())

    @app.errorhandler(RequestEntityTooLarge)
    def request_too_large(_error: RequestEntityTooLarge) -> tuple[object, int]:
        return _error_response("request-too-large", 413)

    return app
