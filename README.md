Passerelle connector to communicate with ATAL
================================================

Installation
------------

 - add to Passerelle installed apps settings:
   INSTALLED_APPS += ('passerelle_imio_ia_tech',)

 - enable module:
   PASSERELLE_APP_PASSERELLE_IMIO_IA_TECH_ENABLED = True


Usage
-----

 - create and configure new connector
   - Title/description: whatever you want
   - Certificate check: uncheck if the service has no valid certificate

 - test service by clicking on the available links
   - the /testConnection/ endpoint try to establish a connection with ATAL
   - the /test_createItem/ endpoint try to create a new point in ATAL
