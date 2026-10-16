import pytest

from bot import load_list, parse_numbered_lines


def test_strips_numbered_prefixes():
    assert parse_numbered_lines("1. bs\n2. bullshit\n12.  ass\n") == ["bs", "bullshit", "ass"]


def test_skips_blank_and_whitespace_lines():
    text = "\n1. bs\n\n   \n2. ass\n\n"
    assert parse_numbered_lines(text) == ["bs", "ass"]


def test_keeps_insult_ending_period():
    assert parse_numbered_lines("1. You are a potato.\n") == ["You are a potato."]


def test_keeps_inner_numbers_and_periods():
    assert parse_numbered_lines("3. You scored 2. Out of 10.\n") == ["You scored 2. Out of 10."]


def test_line_without_prefix_is_kept():
    assert parse_numbered_lines("bs\n") == ["bs"]


def test_handles_windows_line_endings():
    assert parse_numbered_lines("1. bs\r\n2. ass\r\n") == ["bs", "ass"]


def test_load_list_handles_bom(tmp_path):
    path = tmp_path / "words.txt"
    path.write_text("1. bs\n2. ass\n", encoding="utf-8-sig")
    assert load_list(path, "Trigger words") == ["bs", "ass"]


def test_load_list_missing_file_exits(tmp_path):
    with pytest.raises(SystemExit, match="not found"):
        load_list(tmp_path / "missing.txt", "Insults")


def test_load_list_empty_file_exits(tmp_path):
    path = tmp_path / "empty.txt"
    path.write_text("\n   \n", encoding="utf-8")
    with pytest.raises(SystemExit, match="no entries"):
        load_list(path, "Insults")
