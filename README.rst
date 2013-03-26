Elephant
========

A persistent, full-text searchable key-value store. Powered by Flask, ElasticSearch, and good intensions.

Extracted out of the in-progress `blackbox <https://github.com/kennethreitz/blackbox>`_ project.

Configuration
-------------

Elephant expects the following environment variables to be set::

    AWS_ACCESS_KEY_ID = xxxxxx
    AWS_SECRET_ACCESS_KEY = xxxxxx
    ELASTICSEARCH_URL = xxxxxx
    CLUSTER_NAME = xxxxxx
    API_KEY = xxxxxx


Managing
--------

Seeding the index from S3:

    $ python manage.py seed_index
    Reseeding the index...