"""Focused checks for the provider-neutral rotation operation."""

import pytest

from work_on_the_decayed.operation import (
    InvalidRotationRequest,
    RotateSymbolRequest,
    RotationAction,
    rotate_symbol,
)


def test_rotate_symbol_returns_one_bounded_quarter_turn() -> None:
    operation_request = RotateSymbolRequest.from_payload({"action": "rotate-symbol"})

    assert operation_request.action is RotationAction.ROTATE_SYMBOL
    assert rotate_symbol(operation_request).to_payload() == {"quarterTurns": 1}


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {},
        {"action": 1},
        {"action": "unknown"},
        {"action": "rotate-symbol", "unexpected": True},
    ],
)
def test_rotate_symbol_rejects_every_other_request_shape(payload: object) -> None:
    with pytest.raises(InvalidRotationRequest):
        RotateSymbolRequest.from_payload(payload)
