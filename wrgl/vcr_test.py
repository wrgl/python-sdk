from typing import Callable
import functools

import vcr


def use_vcr(f: Callable) -> Callable:
    @functools.wraps(f)
    def run_test(*args, **kwargs):
        with vcr.use_cassette(
            f"fixtures/vcr_cassettes/{f.__module__}/{f.__qualname__.replace('.', '/')}.yaml",
            record_mode="once",
        ):
            f(*args, **kwargs)

    return run_test
