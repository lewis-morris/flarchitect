from flarchitect.plugins import PluginBase, PluginManager


class P1(PluginBase):
    def spec_build_completed(self, spec_dict):
        return {**spec_dict, "x": 1}


def test_plugin_manager_from_config_single_and_invalid():
    # single class entry
    mgr = PluginManager.from_config(P1)
    out = mgr.spec_build_completed({})
    assert out == {"x": 1}

    # invalid entry should be skipped and not raise
    mgr = PluginManager.from_config(object())
    assert isinstance(mgr, PluginManager)
    assert mgr.spec_build_completed({}) is None


class PNoChange(PluginBase):
    def spec_build_completed(self, spec_dict):
        return None  # explicitly no change


def test_plugin_manager_no_change_returns_none():
    mgr = PluginManager([PNoChange()])
    assert mgr.spec_build_completed({"a": 1}) is None
