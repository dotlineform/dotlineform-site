"""Provider-neutral Work On The Decayed behavior and payload contract."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Self


class InvalidRotationRequest(ValueError):
    """The operation request does not match the finite JSON contract."""


class RotationAction(StrEnum):
    """Actions accepted by the first cloud operation."""

    ROTATE_SYMBOL = "rotate-symbol"


@dataclass(frozen=True, slots=True)
class RotateSymbolRequest:
    """Validated input for one symbol rotation."""

    action: RotationAction

    @classmethod
    def from_payload(cls, payload: object) -> Self:
        if not isinstance(payload, dict) or set(payload) != {"action"}:
            raise InvalidRotationRequest

        raw_action = payload["action"]
        if not isinstance(raw_action, str):
            raise InvalidRotationRequest

        try:
            action = RotationAction(raw_action)
        except ValueError as error:
            raise InvalidRotationRequest from error

        return cls(action=action)


@dataclass(frozen=True, slots=True)
class RotationResult:
    """Bounded result returned by the provider-neutral operation."""

    quarter_turns: int

    def to_payload(self) -> dict[str, int]:
        return {"quarterTurns": self.quarter_turns}


ONE_QUARTER_TURN: Final = RotationResult(quarter_turns=1)


def rotate_symbol(operation_request: RotateSymbolRequest) -> RotationResult:
    """Return the single accepted rotation without transport or provider state."""

    if operation_request.action is not RotationAction.ROTATE_SYMBOL:
        raise InvalidRotationRequest

    return ONE_QUARTER_TURN
