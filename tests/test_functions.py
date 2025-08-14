import pytest

from flarchitect.utils.core_utils import (
    convert_camel_to_snake,
    convert_case,
    convert_kebab_to_snake,
    convert_snake_to_camel,
    dict_to_xml,
    get_count,
)
from flarchitect.utils.general import (
    pluralize_last_word,
    validate_flask_limiter_rate_limit_string,
    xml_to_dict,
)


class TestValidateRateLimitString:
    #  Valid rate limit string with integer and "per" followed by allowed time unit
    def test_valid_rate_limit_string(self):
        # Arrange
        rate_limit_str = "10 per minute"

        # Act
        result = validate_flask_limiter_rate_limit_string(rate_limit_str)
        # Arrange
        rate_limit_str_two = "10 per 5 minutes"

        # Act
        result_two = validate_flask_limiter_rate_limit_string(rate_limit_str_two)

        # Assert
        assert result is True
        assert result_two is True

    #  Empty string
    def test_empty_string(self):
        # Arrange
        rate_limit_str = ""

        # Act
        result = validate_flask_limiter_rate_limit_string(rate_limit_str)

        # Assert
        assert not result


class TestConvertCase:
    #  The function correctly converts a string to camelCase.
    def test_convert_to_camel_case(self):
        # Arrange
        s = "hello_world"
        target_case = "camel"
        expected_result = "helloWorld"

        # Act
        result = convert_case(s, target_case)

        # Assert
        assert result == expected_result

    #  The function correctly converts a string to PascalCase.
    def test_convert_to_pascal_case(self):
        # Arrange
        s = "hello_world"
        target_case = "pascal"
        expected_result = "HelloWorld"

        # Act
        result = convert_case(s, target_case)

        # Assert
        assert result == expected_result

    #  The function correctly converts a string to snake_case.
    def test_convert_to_snake_case(self):
        # Arrange
        s = "HelloWorld"
        target_case = "snake"
        expected_result = "hello_world"

        # Act
        result = convert_case(s, target_case)

        # Assert
        assert result == expected_result

    #  The function correctly converts a string to SCREAMING_SNAKE_CASE.
    def test_convert_to_screaming_snake_case(self):
        # Arrange
        s = "HelloWorld"
        target_case = "screaming_snake"
        expected_result = "HELLO_WORLD"

        # Act
        result = convert_case(s, target_case)

        # Assert
        assert result == expected_result

    #  The function correctly handles an empty string.
    def test_handle_empty_string(self):
        # Arrange
        s = ""
        target_case = "camel"
        expected_result = ""

        # Act
        result = convert_case(s, target_case)

        # Assert
        assert result == expected_result

    #  The function correctly handles a string with only one word.
    def test_handle_single_word_string(self):
        # Arrange
        s = "hello"
        target_case = "pascal"
        expected_result = "Hello"

        # Act
        result = convert_case(s, target_case)

        # Assert
        assert result == expected_result

    #  The function correctly handles a string with only uppercase letters.
    def test_handle_uppercase_string(self):
        # Arrange
        s = "HELLO_WORLD"
        target_case = "snake"
        expected_result = "hello_world"

        # Act
        result = convert_case(s, target_case)

        # Assert
        assert result == expected_result

    #  The function correctly handles a string with only lowercase letters.
    def test_handle_lowercase_string(self):
        # Arrange
        s = "hello_world"
        target_case = "screaming_snake"
        expected_result = "HELLO_WORLD"

        # Act
        result = convert_case(s, target_case)

        # Assert
        assert result == expected_result

    def test_unknown_case_returns_original(self):
        """Unknown ``target_case`` returns the original string."""

        assert convert_case("hello", "unknown") == "hello"

    def test_handles_non_alphanumeric_string(self) -> None:
        """Strings lacking letters or numbers remain unchanged."""

        s = "___"
        assert convert_case(s, "camel") == s


class TestPluralizeLastWord:
    #  pluralizes last word in camelCase
    def test_pluralize_last_word_camel_case(self):
        # Arrange
        converted_name = "camelCase"

        # Act
        result = pluralize_last_word(converted_name)

        # Assert
        assert result == "camelCases"

    #  pluralizes last word in PascalCase
    def test_pluralize_last_word_pascal_case(self):
        # Arrange
        converted_name = "PascalCase"

        # Act
        result = pluralize_last_word(converted_name)

        # Assert
        assert result == "PascalCases"

    #  pluralizes last word in snake_case
    def test_pluralize_last_word_snake_case(self):
        # Arrange
        converted_name = "snake_case"

        # Act
        result = pluralize_last_word(converted_name)

        # Assert
        assert result == "snake_cases"

    #  pluralizes last word in SCREAMING_SNAKE_CASE
    def test_pluralize_last_word_screaming_snake_case(self):
        # Arrange
        converted_name = "SCREAMING_SNAKE_CASE"

        # Act
        result = pluralize_last_word(converted_name)

        # Assert
        assert result == "SCREAMING_SNAKE_CASES"

    #  input with only one word returns the plural of that word
    def test_pluralize_last_word_single_word(self):
        # Arrange
        converted_name = "word"

        # Act
        result = pluralize_last_word(converted_name)

        # Assert
        assert result == "words"

    #  input with only non-alphabetic characters returns the same input


class TestXml:
    def test_simple_dict(self):
        # Arrange
        input_dict = {"person": {"name": "John", "age": 30}}
        expected_xml = '<?xml version="1.0" encoding="UTF-8" ?><root><person><name>John</name><age>30</age></person></root>'

        # Act
        result = dict_to_xml(input_dict)

        # Assert
        assert result == expected_xml

    def test_nested_dict(self):
        # Arrange
        input_dict = {"person": {"name": "John", "address": {"city": "New York", "zip": "10001"}}}
        expected_xml = '<?xml version="1.0" encoding="UTF-8" ?><root><person><name>John</name><address><city>New York</city><zip>10001</zip></address></person></root>'

        # Act
        result = dict_to_xml(input_dict)

        # Assert
        assert result == expected_xml

    def test_list_in_dict(self):
        # Arrange
        input_dict = {"fruits": {"fruit": ["apple", "banana", "cherry"]}}
        expected_xml = '<?xml version="1.0" encoding="UTF-8" ?><root><fruits><fruit><item>apple</item><item>banana</item><item>cherry</item></fruit></fruits></root>'

        # Act
        result = dict_to_xml(input_dict)

        # Assert
        assert result == expected_xml

    def test_root_tag_for_multiple_keys(self):
        # Arrange
        input_dict = {"name": "John", "age": 30}
        expected_xml = '<?xml version="1.0" encoding="UTF-8" ?><root><name>John</name><age>30</age></root>'

        # Act
        result = dict_to_xml(input_dict)

        # Assert
        assert result == expected_xml


class TestXmlDict:
    def test_simple_xml_to_dict(self):
        # Arrange
        xml_data = """<?xml version='1.0' encoding='UTF-8' standalone='no'?><person><name>John</name><age>30</age></person>"""  # noqa: E501
        expected_dict = {"person": {"name": "John", "age": "30"}}

        # Act
        result = xml_to_dict(xml_data)

        # Assert
        assert result == expected_dict

    def test_nested_xml_to_dict(self):
        # Arrange
        xml_data = """<?xml version='1.0' encoding='UTF-8' standalone='no'?><person><name>John</name><address><city>New York</city><zip>10001</zip></address></person>"""  # noqa: E501
        expected_dict = {"person": {"name": "John", "address": {"city": "New York", "zip": "10001"}}}

        # Act
        result = xml_to_dict(xml_data)

        # Assert
        assert result == expected_dict

    def test_xml_with_list_to_dict(self):
        # Arrange
        xml_data = """<?xml version='1.0' encoding='UTF-8' standalone='no'?><fruits><fruit>apple</fruit><fruit>banana</fruit><fruit>cherry</fruit></fruits>"""  # noqa: E501
        expected_dict = {"fruits": {"fruit": ["apple", "banana", "cherry"]}}

        # Act
        result = xml_to_dict(xml_data)

        # Assert
        assert result == expected_dict

    def test_xml_with_empty_elements(self):
        # Arrange
        xml_data = """<?xml version='1.0' encoding='UTF-8' standalone='no'?><person><name>John</name><nickname/><age>30</age></person>"""  # noqa: E501
        expected_dict = {"person": {"name": "John", "nickname": None, "age": "30"}}

        # Act
        result = xml_to_dict(xml_data)

        # Assert
        assert result == expected_dict

    def test_invalid_xml(self):
        # Arrange
        invalid_xml = """<person><name>John</name><age>30</person>"""  # Malformed XML (unmatched tags)  # noqa: E501

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid XML data provided"):
            xml_to_dict(invalid_xml)

    def test_bytes_input_xml(self):
        # Arrange
        xml_data = b"""<?xml version='1.0' encoding='UTF-8' standalone='no'?><person><name>John</name><age>30</age></person>"""  # noqa: E501
        expected_dict = {"person": {"name": "John", "age": "30"}}

        # Act
        result = xml_to_dict(xml_data)

        # Assert
        assert result == expected_dict


class TestGetCount:
    """Tests for :func:`flarchitect.utils.core_utils.get_count`."""

    def test_prefers_total_count(self):
        """Return value from ``total_count`` when present."""

        result = {"total_count": 5}
        assert get_count(result, [1, 2]) == 5

    def test_list_value(self):
        """Return length of list when ``total_count`` absent."""

        result: dict[str, int] = {}
        assert get_count(result, [1, 2, 3]) == 3

    def test_single_value(self):
        """Return ``1`` for a non-list truthy value."""

        result: dict[str, int] = {}
        assert get_count(result, {"a": 1}) == 1

    def test_no_value(self):
        """Return ``0`` when value is falsy."""

        result: dict[str, int] = {}
        assert get_count(result, None) == 0


class TestCaseHelperFunctions:
    """Tests for helper functions wrapping :func:`convert_case`."""

    def test_wrapper_conversions(self):
        """Wrapper functions should delegate to :func:`convert_case`."""

        assert convert_snake_to_camel("hello_world") == "helloWorld"
        assert convert_camel_to_snake("helloWorld") == "hello_world"
        assert convert_kebab_to_snake("hello-world") == "hello_world"
