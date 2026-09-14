from biomass.split import split_chips

IDS = [f"chip{i:04d}" for i in range(1000)]


def test_disjoint_and_complete():
    s = split_chips(IDS, seed=1)
    parts = [set(v) for v in s.values()]
    assert sum(len(p) for p in parts) == len(IDS)
    assert set.union(*parts) == set(IDS)
    assert not (parts[0] & parts[1]) and not (parts[0] & parts[2]) and not (parts[1] & parts[2])


def test_proportions_within_tolerance():
    s = split_chips(IDS, seed=1)
    assert abs(len(s["train"]) / 1000 - 0.7) < 0.01
    assert abs(len(s["val"]) / 1000 - 0.15) < 0.01
    assert abs(len(s["test"]) / 1000 - 0.15) < 0.01


def test_deterministic_under_seed_and_input_order():
    assert split_chips(IDS, seed=3) == split_chips(IDS[::-1], seed=3)
    assert split_chips(IDS, seed=3) != split_chips(IDS, seed=4)
