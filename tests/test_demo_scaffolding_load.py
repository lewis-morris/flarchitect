import re

from flask import Flask

from demo.scaffolding.load import app_factory


def test_app_factory_outputs_docs_url(capsys):
    app = app_factory()
    assert isinstance(app, Flask)
    captured = capsys.readouterr().out
    assert re.search(r"Documentation available at", captured)
