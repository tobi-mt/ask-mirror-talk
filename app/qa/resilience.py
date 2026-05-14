"""
Resilience and Reliability Utilities for QA Service

Provides:
- Retry logic with exponential backoff for transient failures
- Circuit breaker pattern to prevent cascading failures
- Rate limit handling for API calls
- Graceful degradation strategies
"""

import time
import logging
import threading
from typing import Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation, requests allowed
    OPEN = "open"      # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Failures before opening circuit
    success_threshold: int = 2  # Successes to close from half-open
    timeout: float = 60.0  # Seconds before trying half-open
    
    
class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.
    
    When too many failures occur, the circuit "opens" and fails fast
    without making actual calls. After a timeout, it enters "half-open"
    to test if the service has recovered.
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.lock = threading.Lock()
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.
        
        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        with self.lock:
            if self.state == CircuitState.OPEN:
                # Check if timeout has passed to try half-open
                if (self.last_failure_time and 
                    time.time() - self.last_failure_time >= self.config.timeout):
                    logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    logger.warning(f"Circuit breaker '{self.name}' is OPEN, failing fast")
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is open. "
                        f"Service unavailable until {self.last_failure_time + self.config.timeout:.0f}"
                    )
        
        # Try to execute the function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call."""
        with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    logger.info(f"Circuit breaker '{self.name}' closing after {self.success_count} successes")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    self.last_failure_time = None
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                # Failed during testing - reopen circuit
                logger.warning(f"Circuit breaker '{self.name}' reopening after failure in HALF_OPEN")
                self.state = CircuitState.OPEN
                self.success_count = 0
            elif self.failure_count >= self.config.failure_threshold:
                # Too many failures - open circuit
                logger.error(
                    f"Circuit breaker '{self.name}' opening after {self.failure_count} failures"
                )
                self.state = CircuitState.OPEN
    
    def reset(self):
        """Manually reset circuit breaker to closed state."""
        with self.lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None
            logger.info(f"Circuit breaker '{self.name}' manually reset")


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retriable_exceptions: tuple = (Exception,),
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts (including first)
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff (2.0 = double each time)
        jitter: Add random jitter to prevent thundering herd
        retriable_exceptions: Tuple of exception types to retry
    
    Example:
        @retry_with_backoff(max_attempts=3, initial_delay=1.0)
        def call_api():
            return api.get_data()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            last_exception = None
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except retriable_exceptions as e:
                    attempt += 1
                    last_exception = e
                    
                    if attempt >= max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {attempt} attempts: {e}",
                            exc_info=True
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(initial_delay * (exponential_base ** (attempt - 1)), max_delay)
                    
                    # Add jitter to prevent thundering herd
                    if jitter:
                        import random
                        delay = delay * (0.5 + random.random())
                    
                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
            
            # This shouldn't be reached, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


class RateLimiter:
    """
    Token bucket rate limiter for API calls.
    
    Ensures we don't exceed rate limits by throttling requests.
    """
    
    def __init__(self, calls_per_minute: int = 60):
        """
        Args:
            calls_per_minute: Maximum calls allowed per minute
        """
        self.calls_per_minute = calls_per_minute
        self.tokens = calls_per_minute
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire a token to make a call.
        
        Args:
            timeout: Maximum time to wait for a token (None = wait forever)
        
        Returns:
            True if token acquired, False if timeout
        """
        start_time = time.time()
        
        while True:
            with self.lock:
                # Refill tokens based on elapsed time
                now = time.time()
                elapsed = now - self.last_refill
                refill_amount = elapsed * (self.calls_per_minute / 60.0)
                
                self.tokens = min(self.calls_per_minute, self.tokens + refill_amount)
                self.last_refill = now
                
                # Try to acquire token
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return True
            
            # Check timeout
            if timeout is not None:
                if time.time() - start_time >= timeout:
                    logger.warning("Rate limiter: timeout waiting for token")
                    return False
            
            # Wait a bit before trying again
            time.sleep(0.1)


# Global circuit breakers for different services
_openai_circuit_breaker = CircuitBreaker(
    "openai",
    CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=2,
        timeout=60.0
    )
)

_embedding_circuit_breaker = CircuitBreaker(
    "embedding",
    CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout=30.0
    )
)


def with_circuit_breaker(breaker_name: str):
    """
    Decorator to wrap function calls with a circuit breaker.
    
    Args:
        breaker_name: Name of the circuit breaker ('openai' or 'embedding')
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get the appropriate circuit breaker
            if breaker_name == "openai":
                breaker = _openai_circuit_breaker
            elif breaker_name == "embedding":
                breaker = _embedding_circuit_breaker
            else:
                # No circuit breaker configured, call directly
                logger.warning(f"Unknown circuit breaker: {breaker_name}")
                return func(*args, **kwargs)
            
            return breaker.call(func, *args, **kwargs)
        
        return wrapper
    return decorator


def get_circuit_breaker(name: str) -> Optional[CircuitBreaker]:
    """Get a circuit breaker by name."""
    if name == "openai":
        return _openai_circuit_breaker
    elif name == "embedding":
        return _embedding_circuit_breaker
    return None


def reset_circuit_breaker(name: str):
    """Manually reset a circuit breaker."""
    breaker = get_circuit_breaker(name)
    if breaker:
        breaker.reset()
    else:
        logger.warning(f"Circuit breaker '{name}' not found")


def is_transient_error(exception: Exception) -> bool:
    """
    Determine if an exception is likely transient (retryable).
    
    Transient errors include:
    - Network timeouts
    - Rate limit errors (429)
    - Server errors (500, 502, 503, 504)
    - Connection errors
    """
    error_str = str(exception).lower()
    error_type = type(exception).__name__
    
    # Check for common transient patterns
    transient_patterns = [
        'timeout',
        'connection',
        'rate limit',
        '429',
        '500',
        '502',
        '503',
        '504',
        'service unavailable',
        'gateway',
        'temporary',
        'transient',
    ]
    
    return any(pattern in error_str for pattern in transient_patterns)


def with_graceful_degradation(fallback_func: Callable):
    """
    Decorator that provides graceful degradation with a fallback function.
    
    If the main function fails, calls the fallback function instead.
    
    Args:
        fallback_func: Function to call if main function fails
    
    Example:
        def fallback_answer(question):
            return {"answer": "Service temporarily unavailable", "citations": []}
        
        @with_graceful_degradation(fallback_answer)
        def generate_answer(question):
            return expensive_llm_call(question)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"{func.__name__} failed, using fallback: {e}",
                    exc_info=True
                )
                try:
                    return fallback_func(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(
                        f"Fallback function also failed: {fallback_error}",
                        exc_info=True
                    )
                    raise e  # Raise original error
        
        return wrapper
    return decorator
