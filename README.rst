Elephant
========

Basically, this is a *Work in Progress* HTTP key/value store with full-text search and fast queries.

Search and query functionality is all provided by a backing Elastic Seach server. Everything is immediately replicated to S3 as JSON documents.

Simplicity — full-text search, HTTP, persitience, data portability.

Usage
-----

.. code-block:: pycon

    >>> requests.post('http://elephant-server/pages/', data={'title': 'Test Page', 'draft': True})
    <Response [200]>
    
    >>> requests.get('http://elephant-server/pages/', params={'q': 'draft:True'}).json()
    {u'records': [{u'epoch': 1364286524987, u'title': u'Test Post', u'uuid': u'ce251e8a-ab6b-4f7e-bdc4-eecf0e71ac16'}}


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

Management
----------

Reseeding ElasticSearch is super simple::

    $ python elephant.py purge
    Deleting all indexes...

    $ python elephant.py seed
    Calculating Indexes...
    [################################] 378/378
    Creating Indexes...
    Indexing...
    [####                            ] 29/378

Inpsiration
-----------

Extracted out of the in-progress `blackbox <https://github.com/kennethreitz/blackbox>`_ project.
