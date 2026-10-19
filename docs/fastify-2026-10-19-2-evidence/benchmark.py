"""Run from repo root with PYTHONPATH=. and project dependencies installed."""

import hashlib
import json
import random
import statistics
import string
import timeit
from datetime import datetime, timezone
from unittest.mock import patch

from flask import Flask

from flarchitect.utils import core_utils, response_helpers

CASES = ("camel", "pascal", "snake", "screaming_snake", "kebab", "screaming_kebab", "unknown")
rng = random.Random(42)
NAMES = ["", "___", "HTTPResponse2XX", "_private_key", "naïve café", "status_code", "total_count", "next_url", "previous_url"]
NAMES += ["".join(rng.choices(string.ascii_letters + string.digits + "_- ", k=rng.randrange(1, 80))) for _ in range(200)]
converted = [[name, case, core_utils.convert_case(name, case)] for name in NAMES for case in CASES]
app = Flask(__name__)


class FixedDatetime:
    @staticmethod
    def now(tz):
        return datetime(2026, 10, 19, tzinfo=timezone.utc)


def response():
    return response_helpers.create_response(value={"untouched_key": [1, 2]}, count=2, next_url="/next", response_ms=12.5)


def timing(fn, number):
    return statistics.median(timeit.repeat(fn, number=number, repeat=5)) / number * 1e6


snapshots = []
with patch.object(response_helpers, "datetime", FixedDatetime):
    for case in CASES:
        for content in ("application/json", "application/xml"):
            for callback in (False, True):
                app.config.update(API_FIELD_CASE=case, API_FINAL_CALLBACK=(lambda data: dict(data, callback_marker=True)) if callback else None)
                with app.test_request_context("/", headers={"Accept": content}):
                    resp = response()
                    snapshots.append([case, content, callback, resp.status_code, resp.content_type, resp.get_data(as_text=True)])
    app.config.update(API_FIELD_CASE="snake", API_FINAL_CALLBACK=None)
    with app.test_request_context("/"):
        with patch.object(response_helpers, "get_config_or_model_meta", wraps=response_helpers.get_config_or_model_meta) as spy:
            response()
            case_calls = sum(call.args[0] == "API_FIELD_CASE" for call in spy.call_args_list)
        response_us = timing(response, 1000)
result = {
    "conversion_sha256": hashlib.sha256(json.dumps(converted).encode()).hexdigest(),
    "responses_sha256": hashlib.sha256(json.dumps(snapshots).encode()).hexdigest(),
    "response_field_case_lookups": case_calls,
    "repeated_name_us": timing(lambda: core_utils.convert_case("total_count", "camel"), 10000),
    "mixed_names_7_cases_us": timing(lambda: [core_utils.convert_case(n, c) for n in NAMES for c in CASES], 20),
    "response_us": response_us,
    "responses": snapshots,
}
print(json.dumps(result, indent=2))
