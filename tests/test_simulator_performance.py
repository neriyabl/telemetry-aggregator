import pytest

from src.telemetry_simulator.service import create_initial_state

from .conftest import assert_performance, generate_switch_ids, time_it


@pytest.mark.parametrize("count,max_time", [(10_000, 0.1), (100, 0.01)])
def test_state_creation_performance(count, max_time):
    """Test state creation performance with different counts."""

    def create_states():
        return [create_initial_state() for _ in range(count)]

    states, duration = time_it(create_states)
    assert len(states) == count
    assert all(s.bandwidth_gbps >= 5.0 for s in states)
    assert_performance(duration, max_time, f"Creating {count} states")


def test_snapshot_creation_performance():
    """Test snapshot creation performance."""
    from src.telemetry_simulator.service import create_initial_snapshot

    switch_ids = generate_switch_ids(100)
    snapshot, duration = time_it(create_initial_snapshot, switch_ids)

    assert len(snapshot) == 100
    assert_performance(duration, 0.05, "Creating 100-switch snapshot")


def test_state_update_performance():
    """Test state update performance."""
    from src.telemetry_simulator.service import (
        create_initial_state,
        update_switch_state,
    )

    state = create_initial_state()

    def update_states():
        current = state
        for _ in range(1000):
            current = update_switch_state(current)
        return current

    final_state, duration = time_it(update_states)
    assert final_state.bandwidth_gbps >= 0.0
    assert_performance(duration, 0.1, "Updating state 1000 times")


def test_csv_generation_performance():
    """Test CSV generation performance."""
    import time

    from src.telemetry_simulator.service import create_initial_snapshot, snapshot_to_csv

    switch_ids = generate_switch_ids(100)
    snapshot = create_initial_snapshot(switch_ids)

    csv_data, duration = time_it(snapshot_to_csv, snapshot, time.time())

    assert "switch_id" in csv_data
    assert len(csv_data.split("\n")) == 102
    assert_performance(duration, 0.01, "CSV generation for 100 switches")
