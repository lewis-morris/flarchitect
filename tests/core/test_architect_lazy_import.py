import sys
import types

import flarchitect.core.architect as architect


def test_lazy_user_loader_import():
    sentinel = object()
    captured: dict[str, tuple[tuple, dict]] = {}

    stub = types.ModuleType("flarchitect.authentication.jwt")

    def fake_get_user_from_token(*args, **kwargs):
        captured["call"] = (args, kwargs)
        return sentinel

    stub.get_user_from_token = fake_get_user_from_token
    original = sys.modules.get("flarchitect.authentication.jwt")

    try:
        sys.modules["flarchitect.authentication.jwt"] = stub
        result = architect._get_user_from_token("token", secret_key="secret")
    finally:
        if original is not None:
            sys.modules["flarchitect.authentication.jwt"] = original
        else:
            sys.modules.pop("flarchitect.authentication.jwt", None)

    assert "call" in captured
    assert captured["call"] == (("token",), {"secret_key": "secret"})
    assert result is sentinel
