# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.5] - 2021-09-22
### Fixed
- [DSO-19] [TELE-1117] add verify=False to avoid SSL problems  

## [1.0.4] - 2021-09-22
### Changed
- [INFRA-3976] change package name char to use the standards "-" and "~" as separator
The usage of "." caused problems (recent version where not seen as the most recent by apt (see deb-version man page). 

## [1.0.3] - 2021-09-21
### Fixed
- [MTELEECAA-10] fix missing parameter post_data and Response not json
- I incremented again because that does not appear in production.

## [1.0.2] - 2021-08-30
### Fixed
- [MTELEECAA-10] fix missing parameter post_data and Response not json

## [1.0.1] - 2021-08-26
### Changed
- [INFRA-3919]  Use global env variable (Jenkins) to store deb pkg name

## [1.0.0] - 2021-08-18
### Removed
- [TELE-1034] Translation
- [TELE-1034] Manifest
- [TELE-1034] Manage.py
- [TELE-1034] version
### Added
- [TELE-1034] Relax pre-commit rules and Black settings
- [TELE-1034] Update version.sh
- [TELE-1034] Add TODOs for non-priority tasks
- [TELE-1034] Refactor requests for lisibility
- [TELE-1034] Use schema for post data
- [TELE-1034] Remove translation
- [TELE-1034] Black and cleanup models.py
- [TELE-1034] Add read work request method with GET
- [TELE-1034] Return error if distant server response code is superior to 400
- [TELE-1034] Cleanup setup.py
- [TELE-1034] Rename and refactor changelog [dmshd] [nhislaire] [njphspv] [sverbois]
- [TELE-913] pass requester contact info [dmshd]
- split fpm command on multiple line
- build package with python3
- do not set auto dependencies [nhislaire]
- [TELE-933] add dont_write_bytecode (fpm include pyc files in production fix) [dmshd]
- [TELE-933] only clean on success [dmshd] (2nd)
  fix merge code commited by mistake
  https://support.imio.be/browse/TELE-933
- [TELE-933] only clean on success [dmshd] 
  https://support.imio.be/browse/TELE-933
- [TELE-933] add cleanWs() to fix workspace not cleaned [dmshd] 
  https://support.imio.be/browse/TELE-933
- [TELE-930] add endpoint to retrieve details of a work request [dmshd]
  https://support.imio.be/browse/TELE-930
- [TELE-927] add comments to models enpoints [dmshd]
  https://support.imio.be/browse/TELE-927
- [TELE-927] add attachment post to ATAL endpoint [dmshd]
  https://support.imio.be/browse/TELE-927
- [TELE-913] add work request post [dmshd]
- [TELE-913] add 0001_initial migration file [dmshd]
- [TELE-913] fix test endpoint url [dmshd]
- [TELE-913] remove unused import and field + pre-commit and pyproject optim [dmshd]
- [TELE-913] return test endpoint response and remode duplicate changes.rst
- [TELE-913] start over for atal 6 [dmshd]
- [TELE-695] use passerelle json_load to avoid encoding issues [dmshd]
- [TELE-642] fix encoding again in soap.py
- [TELE-638] In models, changes implementation of StringIO to be python3 complient
- [TELE-640] Fix Test method by adding request as parameter
- [TELE-641] Use BytesIO instead of StringIO
- [TELE-636] fix parenthesis position
- [TELE-636] Fix json bug as it loads a bytes instead of a str since python3
- Adapt Jenkinsfile to install package python3/dist-package instead of python2 [nhislaire] [dmshd]
