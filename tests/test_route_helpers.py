from flarchitect.core.routes import _global_pre_process, _post_process, _pre_process, _route_function_factory


class _Service:
    class Model:
        pass

    model = Model


def test_global_pre_process_no_hook_returns_kwargs():
    service = _Service()
    assert _global_pre_process(service, None, test=1) == {"test": 1}


def test_pre_and_post_process_helpers():
    service = _Service()

    def pre_hook(*, model, **kwargs):
        kwargs["pre"] = True
        return kwargs

    def post_hook(*, model, output, **kwargs):
        return {"output": output + 1}

    processed = _pre_process(service, pre_hook, test=1)
    assert processed["pre"] is True
    assert _post_process(service, post_hook, 1, **processed) == 2


def test_route_function_factory_runs_hooks():
    service = _Service()

    def global_hook(*, model, **kwargs):
        kwargs["global"] = True
        return kwargs

    def pre_hook(*, model, **kwargs):
        kwargs["pre"] = True
        return kwargs

    def post_hook(*, model, output, **kwargs):
        return {"output": output + 1}

    def action(**action_kwargs):
        return action_kwargs["lookup_val"]

    route = _route_function_factory(
        service,
        action,
        many=False,
        global_pre_hook=global_hook,
        pre_hook=pre_hook,
        post_hook=post_hook,
        get_field=None,
        join_model=None,
        output_schema=None,
    )

    assert route(1) == 2
