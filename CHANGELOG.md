# Change Log
All noteworthy changes to this library will be documented here. This project uses [Semantic Versioning](http://semver.org/)

## [0.1.20] - 04/19/2021
### Changed
- Update dotenv to be compatible with Omelette project.

## [0.1.19] - 04/14/2021
### Changed
- Slim down FileSpec as it gets phased out in favor of embedded Parser in card-inbound-pipe.

## [0.1.18] - 02/24/2021
### Changed
- Cast null characters in TypeCaster to empty string.

## [0.1.17] - 02/02/2021
### Changed
- Changed all type_caster error log message types to DEBUG level.

## [0.1.16] - 02/02/2021
### Changed
- Changed type_caster date error log messages to DEBUG level.

## [0.1.15] - 01/29/2021
### Changed
- Add SqlAlchemy dtype support for packed numeric fields.
- Simplify time casting to use left 6 digits.
- Cast date values less than 3 characters in length to None.

## [0.1.14] - 01/14/2021
### Changed
- Removed try/except from Script.run since it is redundant when using Step Functions.

## [0.1.13] - 01/11/2021
### Changed
- Removed TSYS-specific code from sftp_s3_interface, put into application logic instead.

## [0.1.12] - 12/23/2020
### Added
- More log messages around SFTPS3Interface mysql & sftp connections

## [0.1.11] - 12/16/2020
### Added
- Struct fmt string to file spec

## [0.1.10] - 12/15/2020
### Added
- GNUPG Dep

## [0.1.9] - 12/15/2020
### Added
- SQLAlchemy dependency to support fixed width file spec dtypes

## [0.1.8] - 12/11/2020
### Added
- PGP encrypt
- Transfer S3 to SFTP
- Update README
- Rename file_utils
- Rename type_caster

## [0.1.7] - 12/10/2020
### Changed
- Remove `script` try/except slack alert to eliminate duplicate messages
- Set default job_owner_id fallback = None
- Fix SFTP-S3 Interface ini section variable

## [0.1.6] - 12/10/2020
### Added
- Add S3 connector for upload/download
- Add PGP decryption
- Add SFTP - S3 Interface
- Added fixed-width file tools, including file spec & data type parser

## [0.1.5] - 10/27/2020
### Added
- Fix Slack environment in message

## [0.1.4] - 10/26/2020
### Added
- Add args to slack connector for use in Lambda call

## [0.1.3] - 10/26/2020
### Added
- Switch dep management to poetry

## [0.1.2] - 10/16/2020
### Added
- Added extract, transform, load functions to Script class. Also wrapped `run` in a try/except with Slack alerting.


## [0.1.1] - 08/31/2020
### Added
- Added check in Slack connector for slack enabled in .ini file. Must have field "enabled" = "true" under "slack" section to send a message.

## [0.1.0] - 08/28/2020
### Added
- initial version:
  - settings.py - Wrapper of ConfigParser used to parse .ini files for configuration. Can override values with environment variables or use AWS SSM by prefixing value with `ssm:`
  - script.py - Base class for Python scripts used for ETL. Includes basic setup like initializes Settings class, logging, and argparse. Build all code/callables in the `run` function in sub-classes.
  - connectors - Various connectors for outside services, e.g. Snowflake, Slack, SFTP. Reduce boilerplate across projects.
