Elephant
========

A persistent, full-text searchable key-value store. Powered by Flask, ElasticSearch, and good intensions.

Extracted out of the in-progress `blackbox <https://github.com/kennethreitz/blackbox>`_ project.

What is this?
-------------

Basically, this is an HTTP key/value store with full-text search and fast queries. 

Search and query functionality is all provided by a backing Elastic Seach server. Everything is immediately replicated to S3 as JSON documents.

Simplicity — full-text search, HTTP, persitience, data portability.

Enjoy.

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
