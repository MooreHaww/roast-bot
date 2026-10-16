import logging
import os
import random

import pytest

from bot import ReloadingList, Roaster, ShuffleBag


def write(path, text, encoding="utf-8"):
    """Write the file and bump its mtime so the change is always detectable."""
    path.write_text(text, encoding=encoding)
    stat = path.stat()
    write.tick = getattr(write, "tick", 0) + 1
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + write.tick * 1_000_000_000))


@pytest.fixture
def files(tmp_path):
    triggers = tmp_path / "trigger-words.txt"
    insults = tmp_path / "insults.txt"
    write(triggers, "1. heck\n")
    write(insults, "1. Old one.\n2. Old two.\n")
    return triggers, insults


def test_unchanged_file_is_not_reloaded(files):
    triggers, _ = files
    lst = ReloadingList(triggers, "Trigger words")
    assert lst.refresh() is False
    assert lst.items == ["heck"]


def test_changed_file_is_reloaded(files):
    triggers, _ = files
    lst = ReloadingList(triggers, "Trigger words")
    write(triggers, "1. heck\n2. darn\n")
    assert lst.refresh() is True
    assert lst.items == ["heck", "darn"]


def test_empty_file_keeps_old_list_and_warns(files, caplog):
    triggers, _ = files
    lst = ReloadingList(triggers, "Trigger words")
    write(triggers, "\n  \n")
    with caplog.at_level(logging.WARNING, logger="roast-bot"):
        assert lst.refresh() is False
    assert lst.items == ["heck"]
    assert "empty" in caplog.text


def test_bad_encoding_keeps_old_list_and_warns(files, caplog):
    triggers, _ = files
    lst = ReloadingList(triggers, "Trigger words")
    triggers.write_bytes(b"1. \xff\xfe\xfa\n")
    os.utime(triggers, ns=(0, lst._mtime + 5_000_000_000))
    with caplog.at_level(logging.WARNING, logger="roast-bot"):
        assert lst.refresh() is False
    assert lst.items == ["heck"]
    assert "Could not reload" in caplog.text


def test_deleted_file_keeps_old_list_and_warns_once(files, caplog):
    triggers, _ = files
    lst = ReloadingList(triggers, "Trigger words")
    triggers.unlink()
    with caplog.at_level(logging.WARNING, logger="roast-bot"):
        assert lst.refresh() is False
        assert lst.refresh() is False
    assert lst.items == ["heck"]
    assert caplog.text.count("unavailable") == 1


def test_recovers_after_failed_reload(files):
    triggers, _ = files
    lst = ReloadingList(triggers, "Trigger words")
    write(triggers, "")
    lst.refresh()
    write(triggers, "1. darn\n")
    assert lst.refresh() is True
    assert lst.items == ["darn"]


def test_roaster_picks_up_new_trigger_words(files):
    triggers, insults = files
    roaster = Roaster(ReloadingList(triggers, "Trigger words"), ReloadingList(insults, "Insults"))
    assert roaster.match("oh darn") is None
    write(triggers, "1. heck\n2. darn\n")
    assert roaster.match("oh darn") == "darn"


def test_roaster_picks_up_new_insults_without_restart(files):
    triggers, insults = files
    roaster = Roaster(ReloadingList(triggers, "Trigger words"), ReloadingList(insults, "Insults"),
                      rng=random.Random(1))
    assert roaster.next_insult() in {"Old one.", "Old two."}
    write(insults, "1. New one.\n2. New two.\n3. New three.\n")
    new = [roaster.next_insult() for _ in range(6)]
    assert set(new) == {"New one.", "New two.", "New three."}


def test_roaster_keeps_insults_when_reload_is_empty(files):
    triggers, insults = files
    roaster = Roaster(ReloadingList(triggers, "Trigger words"), ReloadingList(insults, "Insults"))
    write(insults, "")
    assert roaster.next_insult() in {"Old one.", "Old two."}


@pytest.mark.parametrize("seed", range(50))
def test_set_items_never_repeats_last_insult(seed):
    bag = ShuffleBag(["a", "b"], rng=random.Random(seed))
    last = bag.next()
    bag.set_items(["a", "b", "c"])
    assert bag.next() != last


def test_set_items_rejects_empty():
    with pytest.raises(ValueError):
        ShuffleBag(["a"]).set_items([])
