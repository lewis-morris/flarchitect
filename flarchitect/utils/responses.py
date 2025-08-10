from typing import Any

from marshmallow import Schema, ValidationError

from flarchitect.schemas.utils import dump_schema_if_exists
from flarchitect.utils.core_utils import get_count


class CustomResponse:
    """
    Custom response class to be used for serializing output.
    """

    # todo Not really sure why this is here anymore - needs really looking at. Was a use for it once, but no loger it seems.

    def __init__(
        self,
        value: list | Any | None = None,
        count: int | None = 1,
        error: list | dict | Any | None = None,
        status_code: int | None = 200,
        next_url: str | None = None,
        previous_url: str | None = None,
        many: bool | None = False,
        response_ms: float | None = None,
    ):
        self.response_ms = response_ms
        self.value = value
        self.count = count
        self.error = error
        self.status_code = status_code
        self.next_url = next_url
        self.previous_url = previous_url
        self.many = many


def serialize_output_with_mallow(
    output_schema: type[Schema], data: Any
) -> CustomResponse:
    """
    Utility function to serialise output using a given Marshmallow schema.

    Args:
        output_schema (Type[Schema]):
            The Marshmallow schema to be used for serialisation.
        data (Any): The data to be serialised.

    Returns:
        CustomResponse: The serialised data wrapped in a CustomResponse object.
    """

    try:
        is_list = isinstance(data, list) or (
            isinstance(data, dict)
            and (
                "value" in data or ("query" in data and isinstance(data["query"], list))
            )
        )
        dump_data = data.get("query", data) if isinstance(data, dict) else data
        value = dump_schema_if_exists(output_schema, dump_data, is_list)
        count = get_count(data, value)

        # Added this is the create_response function as errors were
        # missing the response time
        # response_ms = (time.time() - g.start_time) * 1000
        # if g.get("start_time") else "n/a"

        return CustomResponse(
            value=value,
            count=count,
            next_url=data.get("next_url") if isinstance(data, dict) else None,
            previous_url=data.get("previous_url") if isinstance(data, dict) else None,
            # response_ms=response_ms,
            many=is_list,
        )

    except ValidationError as err:
        return CustomResponse(
            value=None, count=None, error=err.messages, status_code=500
        )


def check_serialise_method_and_return(
    result: dict,
    schema: "AutoSchema",
    model_columns: list[str],
    schema_columns: list[str],
) -> list[dict] | Any:
    """
    Checks if the serialization matches the schema or model columns.
    If not, returns the raw result.

    Args:
        result (Dict): The result dictionary.
        schema (AutoSchema): The schema used for serialization.
        model_columns (List[str]): The model columns.
        schema_columns (List[str]): The schema columns.

    Returns:
        Union[List[Dict], Any]: Serialized data or the original result.
    """
    output_list = result.pop("dictionary", [])
    if output_list:
        output_keys = list(output_list[0].keys())
        if any(x not in model_columns for x in output_keys) or any(
            x not in schema_columns for x in output_keys
        ):
            return output_list

    return serialize_output_with_mallow(schema, result)
