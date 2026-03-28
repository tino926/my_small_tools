"""Core class for handling individual asynchronous database operations."""

import threading
import logging
from typing import Callable, Any, Optional
from functools import wraps

# Try to import Clock from kivy, with fallback
try:
    from kivy.clock import Clock  # type: ignore
except Exception:
    class _FallbackClock:
        @staticmethod
        def schedule_once(func, dt=0):
            try:
                func(dt)
            except TypeError:
                func()
    Clock = _FallbackClock()

from mmex_reader.async_pool import async_pool

logger = logging.getLogger(__name__)

class AsyncDatabaseOperation:
    """Handles asynchronous database operations with UI callbacks."""

    def __init__(
        self,
        target_func: Optional[Callable] = None,
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None,
        success_callback: Optional[Callable] = None,
        error_callback: Optional[Callable] = None,
        start_callback: Optional[Callable] = None,
        complete_callback: Optional[Callable] = None,
        timeout: Optional[float] = None,
    ) -> None:
        self.is_running = False
        self.current_thread = None
        self._completed = False
        self._timeout = timeout
        self._timeout_timer = None
        self._future = None
        self._target_func = target_func
        self._args = args or ()
        self._kwargs = kwargs or {}
        self._success_cb = success_callback
        self._error_cb = error_callback
        self._start_cb = start_callback
        self._complete_cb = complete_callback

    def _schedule_cb(self, cb: Optional[Callable], *cb_args, **cb_kwargs) -> None:
        if not cb:
            return

        def _wrapper(dt):
            try:
                cb(*cb_args, **cb_kwargs)
            except Exception as e:
                logger.exception(f"Error in scheduled callback {getattr(cb, '__name__', cb)}: {e}")

        Clock.schedule_once(_wrapper, 0)

    def execute_async(
        self,
        operation: Callable,
        on_success: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        on_start: Optional[Callable] = None,
        on_complete: Optional[Callable] = None,
        *args,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> "AsyncDatabaseOperation":
        if self.is_running:
            logger.warning("Another async operation is already running")
            return self

        self.is_running = True
        self._completed = False
        self._schedule_cb(on_start)

        def _on_timeout():
            if self.is_running and not self._completed:
                logger.warning("Async operation timed out")
                self.is_running = False
                self._schedule_cb(on_error, "Operation timed out")
                self._schedule_cb(on_complete)

        op_timeout = timeout if timeout is not None else self._timeout
        if op_timeout and op_timeout > 0:
            try:
                self._timeout_timer = threading.Timer(op_timeout, _on_timeout)
                self._timeout_timer.daemon = True
                self._timeout_timer.start()
            except Exception as e:
                logger.exception(f"Failed to start timeout timer: {e}")

        def worker() -> None:
            try:
                result = operation(*args, **kwargs)
                if self.is_running and not self._completed:
                    self._schedule_cb(on_success, result)
            except Exception as e:
                error_msg = str(e)
                logger.exception(f"Async operation failed: {error_msg}")
                self._schedule_cb(on_error, error_msg)
            finally:
                self.is_running = False
                self._completed = True
                if self._timeout_timer:
                    self._timeout_timer.cancel()
                    self._timeout_timer = None
                self._schedule_cb(on_complete)

        self._future = async_pool.submit(worker)
        return self

    def start(self) -> Optional["AsyncDatabaseOperation"]:
        if not callable(self._target_func):
            logger.error("No target_func provided")
            return
        return self.execute_async(
            self._target_func,
            on_success=self._success_cb,
            on_error=self._error_cb,
            on_start=self._start_cb,
            on_complete=self._complete_cb,
            *self._args,
            timeout=self._timeout,
            **self._kwargs,
        )

    def cancel(self) -> None:
        if self._future:
            self._future.cancel()
        if self.is_running:
            self.is_running = False
            if self._timeout_timer:
                self._timeout_timer.cancel()
                self._timeout_timer = None


def async_database_operation(on_success=None, on_error=None, on_start=None, on_complete=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            success_cb = kwargs.pop('on_success', on_success)
            error_cb = kwargs.pop('on_error', on_error)
            start_cb = kwargs.pop('on_start', on_start)
            complete_cb = kwargs.pop('on_complete', on_complete)
            async_op = AsyncDatabaseOperation()
            async_op.execute_async(
                func,
                on_success=success_cb,
                on_error=error_cb,
                on_start=start_cb,
                on_complete=complete_cb,
                *args, **kwargs
            )
            return async_op
        return wrapper
    return decorator
