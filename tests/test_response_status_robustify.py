"""Response transport status must agree with its requested status in every format."""

import pytest
from flask import Flask

from flarchitect.utils.decorators import standardise_response
from flarchitect.utils.response_helpers import create_response


@pytest.mark.parametrize("mimetype", ["application/json", "application/xml", "text/xml"])
@pytest.mark.parametrize("status", [200, 201, 400, 404, 500])
def test_status_is_preserved_for_every_response_format(mimetype, status):
    app = Flask(__name__)
    app.config["API_XML_AS_TEXT"] = mimetype == "text/xml"
    with app.test_request_context(headers={"Accept": mimetype}):
        response = create_response(value="example", status=status)
        assert response.status_code == status
        assert response.mimetype == mimetype


def test_xml_error_response_invokes_error_callback():
    app = Flask(__name__)
    calls = []
    app.config["API_ERROR_CALLBACK"] = lambda error, status, value: calls.append(status)

    @app.route("/missing")
    @standardise_response
    def missing():
        return {"reason": "missing"}, 404

    response = app.test_client().get("/missing", headers={"Accept": "application/xml"})
    assert response.status_code == 404
    assert calls == [404]
