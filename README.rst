Elephant
========

A persistent, full-text searchable key-value store. Powered by Flask, ElasticSearch, and good intensions.

Extracted out of the in-progress `blackbox <https://github.com/kennethreitz/blackbox>`_ project.

Configuration
-------------

Elephant expects the following environment variables to be set::

    # AWS Credentials
    AWS_ACCESS_KEY_ID = xxxxxx
    AWS_SECRET_ACCESS_KEY = xxxxxx
 
    # Elastic Search Server
    ELASTICSEARCH_URL = xxxxxx
    
    # Instance Name
    CLUSTER_NAME = xxxxxx
    
    # Instance Password
    API_KEY = xxxxxx

If you need an Elastic Search to test against, checkout `heroku-elasticsearch <https://github.com/kennethreitz/heroku-elasticsearch>`_.


Managing
--------

Seeding the index from S3:

    $ python manage.py seed_index
    Reseeding the index...
