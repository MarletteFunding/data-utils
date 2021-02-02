import logging
import re
from array import array
from datetime import datetime
from typing import Union

import pendulum

from data_utils.file_utils.fixed_width.file_spec import FileSpec

logger = logging.getLogger(__name__)


class TypeCaster:
    def __init__(self, file_spec: FileSpec):
        self.spec = file_spec

    def cast_data_types(self, value: str, data_type: str, pic_clause: str, field_name: str) -> Union[str, int]:
        """Best effort try to cast data types to the types specified in the layout spec."""
        if data_type == "N" and "." not in pic_clause and "V" not in pic_clause:
            try:
                value = int(value.replace("{", ""))
            except ValueError:
                logger.debug(f"{field_name} value with type N cannot be cast to int: {value}")
        elif data_type == "N" and ("." in pic_clause or "V" in pic_clause):
            value = self._parse_decimal_field(value, field_name, pic_clause)
        elif data_type == "D":
            value = self._parse_date_field(value, field_name, pic_clause)
        elif data_type == "T":
            value = self._parse_time_field(value)

        # Cast empty strings to null
        value = None if value == "" else value

        return value

    @staticmethod
    def _parse_decimal_field(value: str, field_name: str, pic_clause: str) -> Union[str, None]:
        """Uses decimal-based pic_clause to try and convert string to float."""
        parts = re.findall(r'\((.*?) *\)', pic_clause)
        try:
            value = value.replace("{", "")
            if "." in value:
                value = float(value)
            else:
                value = float(f"{value[:int(parts[0])]}.{value[int(parts[0]):]}")
        except ValueError:
            logger.debug(
                f"{field_name} value with type N and decimal pic cannot be cast to float: {value}")

        return value

    def _parse_date_field(self, value: str, field_name: str, pic_clause: str) -> Union[str, None]:
        """Tries to parse a myriad of inconsistent TSYS date formats to a consistent ISO8601 date string."""
        if len(value) == 8:  # e.g. 20200813
            try:
                value = self._parse_date_string(value)
            except ValueError:
                logger.debug(f"{field_name} value with type D cannot be converted to date: {value}")
                value = None
        elif len(value) == 7:  # e.g. 2020153 julian date
            try:
                value = datetime.strptime(value, '%Y%j').date().strftime('%Y-%m-%d')
            except ValueError:
                logger.debug(f"{field_name} value with type D cannot be converted to date: {value}")
                value = None
        elif len(value) == 6 or len(value) == 5:  # e.g. 082023
            try:
                date_format = self.spec.cast_fields[field_name].get("date_format") if \
                    field_name in self.spec.cast_fields else None
                value = self._parse_expiration_date(value, date_format)
            except ValueError:
                logger.debug(f"{field_name} value with type D cannot be converted to date: {value}")
                value = None
        elif len(value) == 4:  # e.g. 0153 last digit of year + julian day
            date_format = self.spec.cast_fields[field_name].get("date_format") if \
                field_name in self.spec.cast_fields else None

            if date_format and date_format in {"%y%m", "%m%y"}:
                try:
                    exp_date = datetime.strptime(value, date_format)
                    return self._parse_expiration_date(exp_date.strftime("%m%Y"))
                except ValueError:
                    logger.debug(f"{field_name} value with type D cannot be converted to date: {value}")
                    value = None
                    return value

            try:
                year_last_digit = value[0]
                julian_date = value[1:]
                year_prefix = str(datetime.now().date().year)[:-1]
                full_julian_date = year_prefix + year_last_digit + julian_date
                value = datetime.strptime(full_julian_date, '%Y%j').date().strftime('%Y-%m-%d')
            except ValueError:
                logger.debug(f"{field_name} value with type D cannot be converted to date: {value}")
                value = None
        elif len(value) == 3 and pic_clause == "9(6)":
            # Special case where dates are listed as 9(6), are really YYMM, but arrive as 3 digits: 923 instead of 0923
            value = "0" + value
            date_format = self.spec.cast_fields[field_name].get("date_format") if \
                field_name in self.spec.cast_fields else None

            if date_format and date_format in {"%y%m", "%m%y"}:
                exp_date = datetime.strptime(value, date_format)
                try:
                    return self._parse_expiration_date(exp_date.strftime("%m%Y"))
                except ValueError:
                    logger.debug(
                        f"{field_name} value with type D cannot be converted to date: {value}")
                    value = None
        elif len(value) < 3:
            logger.debug(f"{field_name} value with type D cannot be converted to date: {value}")
            value = None

        return value

    @staticmethod
    def _parse_date_string(date: str) -> str:
        """Parse standard date strings, usually 8 char"""
        for fmt in ['%Y%m%d', '%m%d%Y', '%m/%d/%y']:
            try:
                return datetime.strptime(date, fmt).date().strftime('%Y-%m-%d')
            except ValueError:
                pass

        raise ValueError

    @staticmethod
    def _parse_time_field(value: str) -> str:
        """Parse string to time formatted string. Strips off any precision after length of 6."""
        try:
            return f"{value[:2]}:{value[2:4]}:{value[4:6]}"
        except IndexError:
            return value

    @staticmethod
    def _parse_expiration_date(date: str, date_format: str = None) -> str:
        """Try to parse expiration dates, which have several different formats. Returns the last day of expiration month
        when a custom date format is not provided."""
        if date_format:
            try:
                return datetime.strptime(date, date_format).date().strftime('%Y-%m-%d')
            except ValueError:
                pass

        exp = None

        for fmt in ['%m%Y', '%m/%y']:
            try:
                exp = datetime.strptime(date, fmt).date()
                break
            except ValueError:
                pass

        if not exp:
            raise ValueError
        else:
            last_day = pendulum.parse(str(exp)).end_of("month")
            return last_day.strftime('%Y-%m-%d')

    @staticmethod
    def unpack_number(number):
        """ Unpack a COMP-3 number. """
        a = array('B', number)
        v = float(0)

        # For all but last digit (half byte)
        for i in a[:-1]:
            v = (v * 100) + (((i & 0xf0) >> 4) * 10) + (i & 0xf)

        # Last digit
        i = a[-1]
        v = (v * 10) + ((i & 0xf0) >> 4)

        # Negative/Positve check.
        if (i & 0xf) == 0xd:
            v = -v

        # Decimal points are determined by a COBOL program's PICtrue clauses, not
        # the data on disk.
        return int(v)
