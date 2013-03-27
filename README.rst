Elephant
========

Elephant is an S3-backed key-value store with querying powered by Elastic Search. Your data is persisted on S3 as simple JSON documents, but you can instantly query it over HTTP.

Suddenly, your data becomes as durable as S3, as portable as JSON, and as queryable as HTTP. Enjoy!

Usage
-----

.. code-block:: pycon

    >>> requests.post('http://elephant-server/pages/', data={'title': 'Test Page', 'draft': True})
    <Response [200]>
    
    >>> requests.get('http://elephant-server/pages/', params={'q': 'draft:True'}).json()
    {u'records': [{u'epoch': 1364286524987, u'title': u'Test Post', u'uuid': u'ce251e8a-ab6b-4f7e-bdc4-eecf0e71ac16', 'draft': True}]}


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

Inspiration
-----------

Extracted out of the in-progress `blackbox <https://github.com/kennethreitz/blackbox>`_ project.
