import pytest
from circuit_breaker import CircuitBreaker, CircuitBreakerRegistry, CircuitState


class TestCircuitBreaker:
    @pytest.mark.asyncio
    async def test_closed_state_by_default(self):
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=10.0)
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_successful_call_resets_failures(self):
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=10.0)

        async def succeed():
            return "ok"

        async def fail():
            raise Exception("fail")

        with pytest.raises(Exception):
            await cb.call(fail)
        result = await cb.call(succeed)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_opens_after_threshold_failures(self):
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=60.0)

        async def fail():
            raise Exception("fail")

        with pytest.raises(Exception):
            await cb.call(fail)
        assert cb.state == CircuitState.CLOSED

        with pytest.raises(Exception):
            await cb.call(fail)
        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_open_circuit_raises_error(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=60.0)

        async def fail():
            raise Exception("fail")

        with pytest.raises(Exception):
            await cb.call(fail)
        assert cb.state == CircuitState.OPEN

        async def succeed():
            return "ok"

        with pytest.raises(Exception) as exc:
            await cb.call(succeed)
        assert 'OPEN' in str(exc.value)

    @pytest.mark.asyncio
    async def test_fallback_called_when_open(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=60.0)

        async def fail():
            raise Exception("fail")

        with pytest.raises(Exception):
            await cb.call(fail)

        async def fallback():
            return "fallback_value"

        async def succeed():
            return "ok"

        result = await cb.call(succeed, fallback=fallback)
        assert result == "fallback_value"

    @pytest.mark.asyncio
    async def test_registry_returns_same_instance(self):
        cb1 = CircuitBreakerRegistry.get("shared", failure_threshold=3, recovery_timeout=30.0)
        cb2 = CircuitBreakerRegistry.get("shared")
        assert cb1 is cb2
        assert cb1.name == "shared"
