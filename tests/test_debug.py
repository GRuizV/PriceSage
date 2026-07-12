from datetime import datetime, timezone

from pricesage.storage.debug import dump_failure


def test_returns_none_when_no_body(tmp_path):
    assert dump_failure("cruz_verde", None, debug_dir=tmp_path) is None
    assert dump_failure("cruz_verde", "", debug_dir=tmp_path) is None
    assert list(tmp_path.iterdir()) == []  # nothing written


def test_writes_body_verbatim_with_timestamped_name(tmp_path):
    when = datetime(2026, 7, 12, 19, 56, 55, tzinfo=timezone.utc)
    path = dump_failure("cruz_verde", '{"error": "not found"}', when=when, debug_dir=tmp_path)
    assert path.name == "cruz_verde_20260712_195655.json"
    assert path.read_text(encoding="utf-8") == '{"error": "not found"}'


def test_extension_guessing(tmp_path):
    json_path = dump_failure("v", '  [1, 2, 3]', debug_dir=tmp_path)
    html_path = dump_failure("v", "<!DOCTYPE html><html></html>", debug_dir=tmp_path)
    text_path = dump_failure("v", "just some text", debug_dir=tmp_path)
    assert json_path.suffix == ".json"
    assert html_path.suffix == ".html"
    assert text_path.suffix == ".txt"
