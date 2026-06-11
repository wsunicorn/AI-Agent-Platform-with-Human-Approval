import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


class RetryExhaustedError(RuntimeError):
    def __init__(self, attempts: int, last_error: BaseException) -> None:
        super().__init__(f"Operation failed after {attempts} attempts: {last_error}")
        self.attempts = attempts
        self.last_error = last_error


class OperationTimeoutError(TimeoutError):
    pass


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    timeout_seconds: float = 15.0
    initial_backoff_seconds: float = 0.25
    backoff_multiplier: float = 2.0

    async def run(self, operation: Callable[[], Awaitable[T]]) -> tuple[T, int]:
        attempts = 0
        last_error: BaseException | None = None

        while attempts < max(self.max_attempts, 1):
            attempts += 1
            try:
                result = await asyncio.wait_for(operation(), timeout=self.timeout_seconds)
                return result, attempts
            except TimeoutError:
                last_error = OperationTimeoutError(
                    f"Operation timed out after {self.timeout_seconds} seconds"
                )
            except Exception as error:
                last_error = error

            if attempts < max(self.max_attempts, 1):
                await asyncio.sleep(
                    self.initial_backoff_seconds
                    * (self.backoff_multiplier ** max(attempts - 1, 0))
                )

        if last_error is None:
            last_error = RuntimeError("Operation failed without an exception")
        raise RetryExhaustedError(attempts, last_error)
