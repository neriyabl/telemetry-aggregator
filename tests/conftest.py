# Pytest configuration and shared utilities
import time


def time_it(func, *args, **kwargs):
    """Helper to time function execution."""
    start = time.perf_counter()
    result = func(*args, **kwargs)
    return result, time.perf_counter() - start


async def async_time_it(coro_func, *args, **kwargs):
    """Helper to time async function execution."""
    start = time.perf_counter()
    result = await coro_func(*args, **kwargs)
    return result, time.perf_counter() - start


def assert_performance(duration, max_time, operation):
    """Helper to assert performance with clear error message."""
    assert duration < max_time, (
        f"{operation} took {duration:.3f}s, expected < {max_time}s"
    )


def generate_switch_ids(count):
    """Generate switch IDs."""
    return [f"sw{i:04d}" for i in range(1, count + 1)]


def generate_csv_data(switch_count):
    """Generate test CSV data."""
    lines = ["switch_id,bandwidth_gbps,latency_ms,packet_errors,last_update_epoch"]
    timestamp = time.time()
    for i in range(1, switch_count + 1):
        lines.append(f"sw{i:04d},50.5,2.1,0,{timestamp}")
    return "\n".join(lines)
