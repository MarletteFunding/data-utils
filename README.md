# Data Utils
#### Python library for managing shared code

This library includes some useful modules that save time from writing common boilerplate.

* `data_utils/settings.py` - Loads the .ini config files into a ConfigParser object. See above section for more info. 

* `data_utils/script.py` - Base class for any scripts. Loads SETTINGS object as `self.settings`, 
parses command line arguments, and initializes logging. 

* `data_utils/connectors/snowflake_connector.py` - Snowflake connector helper class. Abstracts
having to write the full connection call by reading from your SETTINGS object. Includes shorthand 
for queries and eventually will include more for staging files, etc.
