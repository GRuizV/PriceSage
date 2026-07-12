from pricesage.main import configure_logging, in_ci


def test_in_ci_detects_github_actions(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    assert in_ci() is False

    monkeypatch.setenv("CI", "true")
    assert in_ci() is True

    monkeypatch.setenv("CI", "false")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert in_ci() is True


def test_configure_logging_runs_both_modes():
    # Should not raise in either mode; explicit flag overrides CI detection.
    configure_logging(diagnose=False)
    configure_logging(diagnose=True)
