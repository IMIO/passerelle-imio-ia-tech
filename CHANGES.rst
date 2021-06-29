Changelog
=========

0.4.3
------------------

- split fpm command on multiple line
- build package with python3
- do not set auto dependencies
[nhi]

0.4.2
------------------

- [TELE-933] add dont_write_bytecode (fpm include pyc files in production fix) [dmu]


0.4.1
------------------

- [TELE-933] only clean on success [dmu] (2nd)
  fix merge code commited by mistake
  https://support.imio.be/browse/TELE-933

0.4.0
------------------

- [TELE-933] only clean on success [dmu] 
  https://support.imio.be/browse/TELE-933


0.3.9
------------------

- [TELE-933] add cleanWs() to fix workspace not cleaned [dmu] 
  https://support.imio.be/browse/TELE-933


0.3.8
------------------

- [TELE-930] add endpoint to retrieve details of a work request [dmu]
  https://support.imio.be/browse/TELE-930

0.3.7
------------------

- [TELE-927] add comments to models enpoints [dmu]
  https://support.imio.be/browse/TELE-927

0.3.6
------------------

- [TELE-927] add attachment post to ATAL endpoint [dmu]
  https://support.imio.be/browse/TELE-927


0.3.5
------------------

- [TELE-913] add work request post [dmu]



0.3.4
------------------

- [TELE-913] add 0001_initial migration file [dmu]


0.3.3
------------------

- [TELE-913] fix test endpoint url [dmu]


0.3.2
------------------

- [TELE-913] remove unused import and field + pre-commit and pyproject optim [dmu]


0.3.1
------------------

- [TELE-913] return test endpoint response and remode duplicate changes.rst

0.3.0
------------------

- [TELE-913] start over for atal 6 [dmu]

0.2.1f
------------------

- [TELE-695] use passerelle json_load to avoid encoding issues [dmu]

0.2.1e
------------------

- [TELE-642] fix encoding again in soap.py

0.2.1d
------------------

- [TELE-638] In models, changes implementation of StringIO to be python3 complient
- [TELE-640] Fix Test method by adding request as parameter
- [TELE-641] Use BytesIO instead of StringIO

0.2.1c
------------------

- [TELE-636] fix parenthesis position

0.2.1b
------------------

- [TELE-636] Fix json bug as it loads a bytes instead of a str since python3

0.2.1a
------------------

- Adapt Jenkinsfile to install package python3/dist-package instead of python2
[nhislaire] [dmuyshond]
