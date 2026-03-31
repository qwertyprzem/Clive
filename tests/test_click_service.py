from clive.core.services.click import ClickService


def test_parse_extra_args_pairs_and_booleans():
    service = ClickService()
    parsed = service.parse_extra_args(["--foo", "bar", "--flag", "yes", "positional"])
    assert parsed == {"foo": "bar", "flag": "yes"}


def test_is_help_requested_variants():
    service = ClickService()
    assert service.is_help_requested(["--help"])
    assert service.is_help_requested(["-h"])
    assert service.is_help_requested(["help"])
    assert not service.is_help_requested(["run", "deploy"])
