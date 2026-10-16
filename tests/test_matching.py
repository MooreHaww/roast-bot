import pytest

from bot import build_trigger_pattern, find_trigger

PATTERN = build_trigger_pattern(["bs", "bullshit", "ass"])


@pytest.mark.parametrize("text", ["bs", "BS", "Bs", "bS", "BULLSHIT", "BullShit", "ASS"])
def test_case_insensitive(text):
    assert find_trigger(PATTERN, text) == text.lower()


@pytest.mark.parametrize("text", [
    "absolutely",
    "class",
    "bass",
    "assume",
    "jobs",
    "bullshitting",
    "bs123",
    "bs_",
])
def test_no_substring_matches(text):
    assert find_trigger(PATTERN, text) is None


@pytest.mark.parametrize("text, expected", [
    ("bullshit!", "bullshit"),
    ("that's (bs)", "bs"),
    ("bs, honestly", "bs"),
    ('he said "ass."', "ass"),
    ("what?BS?", "bs"),
    ("...bullshit...", "bullshit"),
])
def test_punctuation_around_word(text, expected):
    assert find_trigger(PATTERN, text) == expected


def test_word_inside_sentence():
    assert find_trigger(PATTERN, "that is absolutely bs and you know it") == "bs"


def test_multiple_triggers_returns_one():
    assert find_trigger(PATTERN, "bs bs bullshit ass") in {"bs", "bullshit", "ass"}


def test_no_trigger():
    assert find_trigger(PATTERN, "a perfectly polite message") is None
    assert find_trigger(PATTERN, "") is None


def test_regex_characters_are_escaped():
    pattern = build_trigger_pattern(["f*ck", "a.b"])
    assert find_trigger(pattern, "oh f*ck") == "f*ck"
    assert find_trigger(pattern, "fck") is None
    assert find_trigger(pattern, "ffffck") is None
    assert find_trigger(pattern, "axb") is None
    assert find_trigger(pattern, "a.b") == "a.b"
