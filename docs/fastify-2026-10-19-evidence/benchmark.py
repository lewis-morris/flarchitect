import hashlib
import json
import statistics
import timeit
from unittest.mock import patch

from flask import Flask
from marshmallow import fields
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from flarchitect.schemas import bases
from flarchitect.utils import config_helpers

app = Flask(__name__)
app.config.update(API_SERIALIZATION_IGNORE_DETACHED=True, API_FIELD_CASE="snake")


class RecordSchema(bases.Base):
    id = fields.Integer()
    name = fields.String()
    a = fields.Integer()
    b = fields.Integer()
    c = fields.Integer()
    d = fields.Integer()
    e = fields.Integer()
    f = fields.Integer()


class ModelBase(DeclarativeBase):
    pass


class Record(ModelBase):
    __tablename__ = "benchmark_record"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)


class ModelSchema(bases.AutoSchema):
    class Meta:
        model = Record


rows = [dict(id=i, name=f"row-{i}", a=i, b=i, c=i, d=i, e=i, f=i) for i in range(1000)]
schema = RecordSchema(many=True)


def timing(fn, number):
    return statistics.median(timeit.repeat(fn, number=number, repeat=5)) / number * 1000


result = {}
with app.test_request_context("/records?page=2"):
    dumped = schema.dump(rows)
    result["dump_sha256"] = hashlib.sha256(json.dumps(dumped, sort_keys=True).encode()).hexdigest()
    with patch.object(bases, "get_config_or_model_meta", wraps=bases.get_config_or_model_meta) as spy:
        schema.dump(rows)
        result["dump_config_calls"] = spy.call_count
    result["dump_1000_rows_ms"] = timing(lambda: schema.dump(rows), 10)
    with patch.object(bases.AutoSchema, "_field_cache_config_fingerprint", autospec=True, side_effect=bases.AutoSchema._field_cache_config_fingerprint) as spy:
        model_schema = ModelSchema()
        result["filtered_schema_fingerprints"] = spy.call_count
    result["model_dump"] = model_schema.dump(Record(id=1, name="example"))
    result["filtered_schema_ms"] = timing(ModelSchema, 100)
    config_helpers.get_config_or_model_meta("API_FIELD_CASE")
    with patch.object(config_helpers, "_method_based_keys", wraps=config_helpers._method_based_keys) as spy:
        for _ in range(100):
            assert config_helpers.get_config_or_model_meta("API_FIELD_CASE") == "snake"
        result["cached_lookup_key_builds_per_100"] = spy.call_count
    result["cached_config_lookup_ms"] = timing(lambda: config_helpers.get_config_or_model_meta("API_FIELD_CASE"), 10000)
print(json.dumps(result, indent=2))
