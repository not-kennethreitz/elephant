Elephant
========

Elephant is an S3-backed key-value store with querying powered by Elastic Search. Your data is persisted on S3 as simple JSON documents, but you can instantly query it over HTTP.

Suddenly, your data becomes as durable as S3, as portable as JSON, and as queryable as HTTP. Enjoy!

Usage
-----

.. code-block:: pycon

    >>> requests.post('http://elephant-server/', data={'title': 'Test Page', 'draft': True})
    <Response [200]>

    >>> requests.get('http://elephant-server/', params={'q': 'draft:True'}).json()
    {u'records': [{u'epoch': 1364286524987, u'title': u'Test Page', u'uuid': u'ce251e8a-ab6b-4f7e-bdc4-eecf0e71ac16'}}


Configuration
-------------


Elephant expects the following environment variables to be set::

    # AWS Credentials
    BYODEMO_BUCKET_NAME = xxxxxx
    BYODEMO_AWS_ACCESS_KEY_ID = xxxxxx
    BYODEMO_AWS_SECRET_ACCESS_KEY = xxxxxx

    # Elastic Search Server
    FOUNDELASTICSEARCH_URL = xxxxxx
    ES_PASSWORD = xxxxxx

If you need a production Elastic Search instance, checkout `searchly <http://www.searchly.com/>`_ and `heroku-elasticsearch <https://github.com/kennethreitz/heroku-elasticsearch>`_.


Management
----------

Reseeding ElasticSearch is super simple::

    $ python elephant.py seed
    Creating Index...
    Indexing...
    [####                            ] 29/378

Inspiration
-----------

Extracted out of the in-progress `blackbox <https://github.com/kennethreitz/blackbox>`_ project.
