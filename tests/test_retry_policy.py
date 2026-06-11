import asyncio

import pytest

from app.services.retry import OperationTimeoutError, RetryExhaustedError, RetryPolicy


@pytest.mark.asyncio
async def test_retry_policy_retries_until_success() -> None:
    attempts = 0
    policy = RetryPolicy(
        max_attempts=3,
        timeout_seconds=1,
        initial_backoff_seconds=0,
    )

    async def operation() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise RuntimeError("temporary failure")
        return "ok"

    result, used_attempts = await policy.run(operation)

    assert result == "ok"
    assert used_attempts == 2


@pytest.mark.asyncio
async def test_retry_policy_wraps_timeout() -> None:
    policy = RetryPolicy(
        max_attempts=1,
        timeout_seconds=0.01,
        initial_backoff_seconds=0,
    )

    async def operation() -> str:
        await asyncio.sleep(0.1)
        return "late"

    with pytest.raises(RetryExhaustedError) as exc_info:
        await policy.run(operation)

    assert isinstance(exc_info.value.last_error, OperationTimeoutError)
