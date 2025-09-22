from flarchitect.utils import general as general_utils


def test_update_dict_if_flag_true_and_pretty_print():
    out: dict[str, object] = {}
    general_utils.update_dict_if_flag_true(out, True, "status_code", 200, "snake")
    assert out.get("status_code") == 200
    general_utils.update_dict_if_flag_true(out, False, "ignored", 1, "snake")
    assert "ignored" not in out

    # when requesting camel case the converted key should change
    general_utils.update_dict_if_flag_true(out, True, "response_ms", 15, "camel")
    assert "responseMs" in out and out["responseMs"] == 15

    # callable conversion should also be honoured
    general_utils.update_dict_if_flag_true(out, True, "mixed_key", 1, lambda key: key.upper())
    assert out["MIXED_KEY"] == 1

    s = general_utils.pretty_print_dict({"a": 1})
    assert isinstance(s, str) and "'a': 1" in s


def test_make_base_dict_respects_configuration(monkeypatch):
    config_values = {
        "API_FIELD_CASE": "camel",
        "API_DUMP_DATETIME": True,
        "API_DUMP_VERSION": False,
        "API_VERSION": "2.0",
        "API_DUMP_STATUS_CODE": True,
        "API_DUMP_RESPONSE_MS": False,
        "API_DUMP_TOTAL_COUNT": True,
        "API_DUMP_NULL_NEXT_URL": True,
        "API_DUMP_NULL_PREVIOUS_URL": False,
        "API_DUMP_NULL_ERRORS": False,
    }

    def fake_get_config(key: str, default=None, **_kwargs):
        return config_values.get(key, default)

    monkeypatch.setattr(general_utils, "get_config_or_model_meta", fake_get_config)

    base = general_utils.make_base_dict()
    assert base["value"] == "..."
    assert base["datetime"] == "2024-01-01T00:00:00.0000+00:00"
    assert "apiVersion" not in base  # disabled via flag
    assert base["statusCode"] == 200
    assert "responseMs" not in base
    assert base["totalCount"] == 10
    assert base["nextUrl"] == "/api/example/url"
    assert "previousUrl" not in base
    assert "errors" not in base
