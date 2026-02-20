from budget_program.services import AllocationTarget, compute_allocation_amounts, validate_allocation_total


def test_validate_sum_to_100():
    assert validate_allocation_total([50, 30, 20])
    assert not validate_allocation_total([50, 30, 19.99])


def test_allocation_remainder_goes_to_largest_percent():
    targets = [
        AllocationTarget("account", "a1", 50),
        AllocationTarget("debt", "d1", 30),
        AllocationTarget("account", "a2", 20),
    ]
    allocations = compute_allocation_amounts(100.01, targets)
    values = [amt for _, amt in allocations]
    assert round(sum(values), 2) == 100.01
    assert values[0] == 50.01
    assert values[1] == 30.0
    assert values[2] == 20.0
