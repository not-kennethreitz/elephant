# -*- coding: utf-8 -*-

import os
import time
import datetime
from uuid import uuid4

import boto
from flask import Flask, request
# from boto.s3.connection import S3Connection
# from boto.exception import S3ResponseError
from pyelasticsearch import ElasticSearch


app = Flask(__name__)

# The Elastic Search endpoint to use.
ELASTICSEARCH_URL = os.environ['ELASTICSEARCH_URL']
CLUSTER_NAME = os.environ['CLUSTER_NAME']
API_KEY = os.environ['API_KEY']

# If S3 bucket doesn't exist, set it up.
BUCKET_NAME = 'elephant-{}'.format(CLUSTER_NAME)
BUCKET = boto.connect_s3().create_bucket(BUCKET_NAME)


ES = ElasticSearch(ELASTICSEARCH_URL)

def epoch(dt=None):
    """Returns the epoch value for the given datetime, defulting to now."""

    if not dt:
        dt = datetime.utcnow()

    return int(time.mktime(dt.timetuple()) * 1000 + dt.microsecond / 1000)


class Collection(object):
    """A set of Records."""

    def __init__(self):
        self.slug = None

    def iter_search(self, query, **kwargs):
        """Returns an iterator of Records for the given query."""

        if query is None:
            query = '*'

        # Pepare elastic search queries.
        params = {}
        for (k, v) in kwargs.items():
            params['es_{0}'.format(k)] = v

        params['es_q'] = query

        q = {
            'sort': [
                {"epoch" : {"order" : "desc"}},
            ]
        }

        # if query:
        q['query'] = {'term': {'query': query}},

        results = ES.search(q, index=self.slug, **params)
        # print results

        params['es_q'] = query
        for hit in results['hits']['hits']:
            yield Record.from_hit(hit)

    def search(self, query, sort=None, size=None, **kwargs):
        """Returns a list of Records for the given query."""

        if sort is not None:
            kwargs['sort'] = sort
        if size is not None:
            kwargs['size'] = size

        return [r for r in self.iter_search(query, **kwargs)]


class Record(object):
    """A record in the database."""

    def __init__(self):
        self.uuid = str(uuid4())
        self.data = {}
        self.epoch = epoch()
        self.collection = None

    def save(self):
        self.persist()
        self.index()

    def persist(self):
        """Saves the Record to S3."""
        key = BUCKET.new_key('{0}/{1}.json'.format(self.collection, self.uuid))
        key.update_metadata({'Content-Type': 'application/json'})
        key.set_contents_from_string(self.json)

    def index(self):
        """Saves the Record to Elastic Search."""
        return ES.index(self.collection, 'record', self.dict, id=self.uuid)

    @property
    def dict(self):
        d = self.data.copy()
        d.update(uuid=self.uuid, epoch=self.epoch)
        return d


@app.before_request
def require_apikey():
    assert request.params.get('key') == API_KEY

    return '-_-', 403

@app.route('/')
def hello_world():
    return 'Hello World!'

if __name__ == '__main__':
    app.run()