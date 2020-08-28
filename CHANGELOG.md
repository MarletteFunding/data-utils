# Change Log
All noteworthy changes to this library will be documented here. This project uses [Semantic Versioning](http://semver.org/)

## [0.1.0] - 08/28/2020
### Added
- initial version:
  - settings.py - Wrapper of ConfigParser used to parse .ini files for configuration. Can override values with environment variables or use AWS SSM by prefixing value with `ssm:`
  - script.py - Base class for Python scripts used for ETL. Includes basic setup like initializes Settings class, logging, and argparse. Build all code/callables in the `run` function in sub-classes.
  - connectors - Various connectors for outside services, e.g. Snowflake, Slack, SFTP. Reduce boilerplate across projects.
