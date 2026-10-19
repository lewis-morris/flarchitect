"""Schema preparation for partial updates."""

from copy import deepcopy

from marshmallow import Schema


def _prepare_patch_schema(input_schema: Schema | None) -> Schema | None:
    """Prepare a patch schema with all fields optional.

    Args:
        input_schema (Optional[Schema]): The input schema to prepare the patch schema for.

    Returns:
        Optional[Schema]: The prepared patch schema with all fields set to optional.
    """
    if not input_schema:
        return None

    # Initialise a dictionary to hold the new class's fields
    class_fields = {}

    # Iterate over all fields in the input schema
    items = input_schema.fields.items() if hasattr(input_schema, "fields") else input_schema().fields.items()

    for field_name, field_obj in items:
        # Deepcopy the field to avoid mutating the original field
        new_field = deepcopy(field_obj)

        # Set the field to be optional
        new_field.required = False
        new_field.allow_none = True

        # Add the modified field to the class fields
        class_fields[field_name] = new_field

    # Preserve the Meta class if it exists
    Meta = getattr(input_schema.__class__, "Meta", None)
    if Meta:
        class_fields["Meta"] = Meta

    # Dynamically create a new schema class with the modified fields
    PatchSchemaClass = type(
        f"Patch{input_schema.__class__.__name__}",
        (Schema,),  # Inherit directly from Schema to avoid field conflicts
        class_fields,
    )

    return PatchSchemaClass()
