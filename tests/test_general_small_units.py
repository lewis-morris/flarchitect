from flarchitect.utils.general import pretty_print_dict, update_dict_if_flag_true


def test_update_dict_if_flag_true_and_pretty_print():
    out = {}
    update_dict_if_flag_true(out, True, "status_code", 200, "snake")
    assert out.get("status_code") == 200
    update_dict_if_flag_true(out, False, "ignored", 1, "snake")
    assert "ignored" not in out

    s = pretty_print_dict({"a": 1})
    assert isinstance(s, str) and "'a': 1" in s

