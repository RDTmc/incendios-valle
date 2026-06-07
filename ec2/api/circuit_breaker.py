import asyncio
import time
from enum import Enum


class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout: float = 30.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                return CircuitState.HALF_OPEN
        return self._state

    async def call(self, coro_factory, fallback=None):
        current_state = self.state

        if current_state == CircuitState.OPEN:
            return await self._handle_open(fallback)

        try:
            result = await coro_factory()
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            if fallback:
                return await fallback()
            raise

    async def _handle_open(self, fallback):
        if fallback:
            return await fallback()
        raise Exception(f"CircuitBreaker '{self.name}' is OPEN")

    async def _on_success(self):
        async with self._lock:
            self._failure_count = 0
            self._state = CircuitState.CLOSED

    async def _on_failure(self):
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN


class CircuitBreakerRegistry:
    _breakers: dict[str, CircuitBreaker] = {}

    @classmethod
    def get(cls, name: str, failure_threshold: int = 3, recovery_timeout: float = 30.0) -> CircuitBreaker:
        if name not in cls._breakers:
            cls._breakers[name] = CircuitBreaker(name, failure_threshold, recovery_timeout)
        return cls._breakers[name]
