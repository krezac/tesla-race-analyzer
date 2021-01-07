import logging
from functools import wraps
from time import perf_counter
from contextlib import contextmanager

logger = logging.getLogger(__name__)


# function_timer is a function wrapper to time its execution length
def function_timer():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with function_timer_block(func.__qualname__):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# function_timer_block is a context manager to allow timing of specific blocks of code
@contextmanager
def function_timer_block(name):

    start_time = perf_counter()

    try:
        yield
    finally:
        elapsed_time = perf_counter() - start_time
        logger.info('{0} took {1:.5f} seconds'.format(name, elapsed_time))
