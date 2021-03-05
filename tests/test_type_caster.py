import pytest

from data_utils.file_utils.fixed_width.type_caster import TypeCaster


def test_none_cast_data_types():
    """if value is None the func should return None"""
    result = TypeCaster.cast_data_types(None, value=None, data_type="", pic_clause="", field_name="")
    assert result is None


def test_parse_decimal_field_random():
    """should return the original value with "{" removed if non decimal value is passed """
    value = 'fail4sure{'
    result = TypeCaster._parse_decimal_field(value=value, field_name='TRANSACTION_AMOUNT', pic_clause='-9(7).9(2)')
    assert result == 'fail4sure'


def test_parse_decimal_field_decimal_value():
    """if input str is a float value then func should return float"""
    value = '-0000123.45'
    result = TypeCaster._parse_decimal_field(value=value, field_name='TRANSACTION_AMOUNT', pic_clause='-9(7).9(2)')
    assert result == -0000123.45


def test_integer_val_parse_decimal_field():
    """if input is integer value should cast into decimal value based on pic clause"""
    value = '-000012345'
    result = TypeCaster._parse_decimal_field(value=value, field_name='TRANSACTION_AMOUNT', pic_clause='-9(7).9(2)')
    assert result == -0000123.45


def test_parse_time_field():
    """string should be sliced to time format hh:mm:ss"""
    assert TypeCaster._parse_time_field("hhmmss") == "hh:mm:ss"
    assert TypeCaster._parse_time_field("235000") == "23:50:00"


def test_parse_date_string():
    """date time stings should be converted to date formats"""
    assert TypeCaster._parse_date_string('03/28/21') == '2021-03-28'
    assert TypeCaster._parse_date_string('20210328') == '2021-03-28'
    assert TypeCaster._parse_date_string('03282021') == '2021-03-28'
    assert TypeCaster._parse_date_string('00010101') == '0001-01-01'


def test_parse_expiration_date():
    """func should return date string with last date of month from input date string if date format is not mentioned"""
    assert TypeCaster._parse_expiration_date('21-03-01', '%y-%m-%d') == '2021-03-01'
    assert TypeCaster._parse_expiration_date('03/21') == '2021-03-31'
    assert TypeCaster._parse_expiration_date('032021') == '2021-03-31'
