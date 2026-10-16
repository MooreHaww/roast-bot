import random

import pytest

from bot import ShuffleBag

ITEMS = ["a", "b", "c", "d", "e"]


def draw_rounds(bag, size, rounds):
    return [[bag.next() for _ in range(size)] for _ in range(rounds)]


@pytest.mark.parametrize("seed", range(50))
def test_each_round_uses_every_item_once(seed):
    bag = ShuffleBag(ITEMS, rng=random.Random(seed))
    for round_ in draw_rounds(bag, len(ITEMS), 20):
        assert sorted(round_) == sorted(ITEMS)


@pytest.mark.parametrize("seed", range(50))
def test_new_round_never_starts_with_previous_last(seed):
    bag = ShuffleBag(ITEMS, rng=random.Random(seed))
    rounds = draw_rounds(bag, len(ITEMS), 50)
    for prev, cur in zip(rounds, rounds[1:]):
        assert cur[0] != prev[-1]


@pytest.mark.parametrize("seed", range(50))
def test_two_items_alternate_across_rounds(seed):
    bag = ShuffleBag(["x", "y"], rng=random.Random(seed))
    draws = [bag.next() for _ in range(40)]
    assert all(a != b for a, b in zip(draws, draws[1:]))


@pytest.mark.parametrize("seed", range(50))
def test_duplicate_items_still_avoid_repeat_at_boundary(seed):
    items = ["a", "a", "b"]
    bag = ShuffleBag(items, rng=random.Random(seed))
    rounds = draw_rounds(bag, len(items), 30)
    for prev, cur in zip(rounds, rounds[1:]):
        assert sorted(cur) == sorted(items)
        assert cur[0] != prev[-1]


def test_single_item_repeats():
    bag = ShuffleBag(["only"])
    assert [bag.next() for _ in range(3)] == ["only"] * 3


def test_empty_bag_rejected():
    with pytest.raises(ValueError):
        ShuffleBag([])
