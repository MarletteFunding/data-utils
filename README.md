# Data Utils
#### Python library for managing shared code

This library includes some useful modules that save time from writing common boilerplate.

* `data_utils/settings.py` - Loads the .ini config files into a ConfigParser object. 

* `data_utils/script.py` - Base class for any scripts. Loads SETTINGS object as `self.settings`, 
parses command line arguments, and initializes logging. 

* `data_utils/connectors/snowflake_connector.py` - Snowflake connector helper class. Abstracts
having to write the full connection call by reading from your SETTINGS object. Includes shorthand 
for queries and eventually will include more for staging files, etc.

* `data_utils/connectors/slack_connector.py` - Class that can send alert messages to Slack.

* `data_utils/connectors/sftp_connector.py` - Wrapper of pysftp package that accepts a Settings object to connect.

* `data_utils/connectors/s3_connector.py` - Wrapper of boto3.client("s3") package. Mainly adds retry logic to standard functions.

* `data_utils/file_interfaces/pgp.py` - Wrapper of python-gnupg package. Simplifies pgp encryption/decryption.

* `data_utils/file_interfaces/sftp_s3_interface.py` - Class to help with common tasks transferring files to and from SFTP & S3.

* `data_utils/file_interfaces/fixed_width/file_spec.py` - Loads a CSV file which represents the schema/delimitation of fixed-width files. For use in parsing.

* `data_utils/file_interfaces/fixed_width/type_caster.py` - Helpers for casting fixed-width file data types based on COBOL pic clause.


### To make changes and release a new version:
* Make your changes locally
* Increment the version number in pyproject.toml
* Update the changelog with a summary of your changes
* Commit & push changes to github, open PR, merge to master
* Create a new release in github, tagging it with the same version number in pyproject.toml
* Releases can be installed specifically by Poetry by settings the `rev` tag in pyproject.toml for data-utils, e.g.:
  ```
  [tool.poetry.dependencies]
  python = "^3.7"
  data-utils = {git = "https://github.com/MarletteFunding/data-utils", rev = "0.1.7"}
  ```
