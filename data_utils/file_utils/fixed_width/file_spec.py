import csv
import logging
import re
import os
from collections import defaultdict
from enum import Enum
from typing import Any, Dict

from data_utils.connectors.s3_connector import S3Connector
from data_utils.settings import Settings
from sqlalchemy import NUMERIC, VARCHAR, DATE, JSON, TIME

logger = logging.getLogger(__name__)


class FileFormatEnum(Enum):
    EBCDIC = 'EBCDIC'
    ASCII = 'ASCII'
    LATIN_1 = 'LATIN_1'


FORMAT_ENCODING_MAP = {
    FileFormatEnum.EBCDIC: "cp037",
    FileFormatEnum.ASCII: "ascii",
    FileFormatEnum.LATIN_1: "latin-1"
}


class FileSpec:
    def __init__(self, settings: Settings, file_config: Dict[str, Any]):
        self.settings = settings
        self.s3_conn = S3Connector()
        self.layout_filename = file_config.get("layout_name")
        self.record_type_field_name = file_config.get("record_type_field_name") or "Record Type"
        self.cast_fields = file_config.get("cast_fields", {})
        self.sequence_fields = file_config.get("sequence_fields", {})
        self.nested_field_name = file_config.get("nested_field_name")
        self.nest_json_fields = file_config.get("nest_json_fields", {})
        self.layout = defaultdict(list)
        self.dtypes = {"DETAIL_RECORD_NUMBER": NUMERIC(11, 0)}
        self.struct_fmt_str = defaultdict(str)

        self._generate_layout()

    def _generate_layout(self) -> None:
        """
        Reads CSV layout file and builds a dict of tuples, with a key for each "Record Type". E.g.
        CIF has record types 5 and 6, so two dict keys. Also populates dtypes which are used when
        loading the fields into databases.
        """
        download_path = self.settings.get("file_config", "download_path")
        file_path = f"{download_path}{self.layout_filename}"

        if self.settings.getboolean("file_config", "use_s3"):
            bucket = self.settings.get("file_config", "layout_bucket")
            self.s3_conn.download_file(bucket, self.layout_filename, file_path)

        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)

            for row in reader:
                if row.get(self.record_type_field_name):
                    key = row.get(self.record_type_field_name)
                else:
                    key = "000"

                try:
                    name = row["Copybook Element Name"].strip()
                    data_type = row["Data Type"].strip()
                    start = int(row["Start"])
                    end = int(row["End"])
                    length = int(row["Length"])
                    logic = row["Logic Type"].strip()
                    pic_clause = row["Pic Clause"].strip()
                except ValueError:
                    logger.info(f"Error parsing layout row: record type {key}, field_name: {name}")
                    continue

                # Fields can be cast to different types by defining in yaml file "cast_fields" item.
                if name in self.cast_fields:
                    data_type = self.cast_fields[name]["data_type"]
                    pic_clause = self.cast_fields[name]["pic_clause"]

                # Add struct unpack str
                self.struct_fmt_str[key] += f"{length}s"

                # Add tuple to layout for use in parsing
                self.layout[key].append((name, data_type, start, end, length, logic, pic_clause))

                # Add sqlalchemy type to dtypes for use in loading
                self._build_dtypes(name, data_type, length, pic_clause)

        # Add dtypes for nested JSON columns
        self._add_json_dtypes()

        if self.settings.getboolean("file_config", "use_s3"):
            # Try to clean up downloaded layout after dict is created, but leave test files.
            if "sample_test_files" not in file_path:
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.error(f"Error trying to clean up layout file: {e}")

    def _build_dtypes(self, name: str, data_type: str, length: int, pic_clause: str):
        """
        Adds the field's SQLAlchemy type to dtypes dicts. For use in loading with Pandas.
        """
        parsed_name = self.parse_field_name(name)
        if parsed_name != "" and "FILLER" not in parsed_name:
            if name in self.sequence_fields:
                for i in range(1, self.sequence_fields[name] + 1):
                    sequence_name = f"{parsed_name}_{i}"
                    self.dtypes[sequence_name] = self._sqlalchemy_type(data_type, length, pic_clause)
            else:
                self.dtypes[parsed_name] = self._sqlalchemy_type(data_type, length, pic_clause)

    def _add_json_dtypes(self):
        """
        Certain files e.g. EVT, AUD are too large for MySQL row size. Fields are compressed
        into JSON blobs, so we need to provide a dtype for the field and its corresponding
        "STRUCTURE" field, which tells what dtype each child attr is.
        """
        # EVT File is too large to load to SQL. Fields are nested by event type.
        if self.nested_field_name:
            self.dtypes[self.nested_field_name.upper()] = JSON
            self.dtypes[self.nested_field_name.upper() + "_STRUCTURE"] = JSON

        # AUD file is too large, but no common fields to nest like EVT file. Certain prefixes chosen to be nested.
        if self.nest_json_fields:
            for k, v in self.nest_json_fields.items():
                key = v.get("json_field_name")
                self.dtypes[key.upper()] = JSON
                self.dtypes[key.upper() + "_STRUCTURE"] = JSON

    @staticmethod
    def _sqlalchemy_type(data_type: str, length: int, pic_clause: str):
        """Returns SQLAlchemy column type based on provided data_type, length, and pic_clause."""
        if "C" in pic_clause:
            # Packed numbers take up more space unpacked, so use the pic clause length instead.
            match = re.findall(r'\((.*?) *\)', pic_clause)
            if len(match) == 1:
                try:
                    length = int(match[0])
                except:
                    logger.error(f"Could not extract packed field pic clause length: {pic_clause}")

        if data_type == "N" and "." not in pic_clause and "V" not in pic_clause:
            return NUMERIC(length, 0)
        elif data_type == "N" and ("." in pic_clause or "V" in pic_clause):
            parts = re.findall(r'\((.*?) *\)', pic_clause)
            integer = int(parts[0])
            decimal = int(parts[1])

            # Set mysql precision to total number of digits stored.
            integer = integer + decimal

            return NUMERIC(integer, decimal)
        elif data_type == "D":
            return DATE()
        elif data_type == "T":
            return TIME()
        else:
            return VARCHAR(length)

    @staticmethod
    def parse_field_name(name: str) -> str:
        """Converts original copybook element name to SQL friendly version using only underscores
        as a delimiter between words. Also strips the first string before the first underscore. This
        is usually just the file name abbreviation that we already have from the file itself."""
        convert_to_underscores = name.upper().replace("-", "_").replace("(", "_").replace(")", "_").strip("_")
        strip_prefix = ''.join(convert_to_underscores.split("_", 1)[1:]).strip()
        return strip_prefix
