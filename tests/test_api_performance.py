import pytest

from src.telemetry_api.ingestion import parse_counters_csv

from .conftest import assert_performance, async_time_it, generate_csv_data, time_it


@pytest.mark.parametrize("switch_count,max_time", [(100, 0.01), (10_000, 0.1)])
def test_csv_parsing_performance(switch_count, max_time):
    """Test CSV parsing performance with different sizes."""

    csv_data = generate_csv_data(switch_count)

    def parse_csv():
        return parse_counters_csv(csv_data)

    (data, last_update_ts, metric_names), duration = time_it(parse_csv)

    assert len(data) == switch_count
    assert len(metric_names) == 3
    assert_performance(duration, max_time, f"Parsing {switch_count}-switch CSV")


@pytest.mark.asyncio
async def test_snapshot_storage_performance():
    """Test snapshot storage and retrieval performance."""
    import time

    from src.telemetry_api.schemas import Snapshot
    from src.telemetry_api.store import get_snapshot, set_snapshot

    test_data = {
        f"sw{i:04d}": {"bandwidth_gbps": 50.0, "latency_ms": 2.0} for i in range(1, 101)
    }

    snapshot = Snapshot(
        data=test_data,
        metric_names=["bandwidth_gbps", "latency_ms"],
        last_update_ts=time.time(),
        etag="test-etag",
    )

    # Test both operations
    async def store_and_retrieve():
        await set_snapshot(snapshot)
        return await get_snapshot()

    retrieved, duration = await async_time_it(store_and_retrieve)

    assert retrieved is not None
    assert len(retrieved.data) == 100
    assert_performance(duration, 0.002, "Store and retrieve snapshot")
