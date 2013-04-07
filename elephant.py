# -*- coding: utf-8 -*-

import os
import errno
import json
import time
import urlparse
from os import makedirs
from datetime import datetime
from uuid import uuid4

import boto
from flask import Flask, request, Response, jsonify, redirect
from flask.ext.script import Manager
from clint.textui import progress
from pyelasticsearch import ElasticSearch
from pyelasticsearch.exceptions import IndexAlreadyExistsError, InvalidJsonResponseError


app = Flask(__name__)
manager = Manager(app)

# Configuration
app.debug = 'DEBUG' in os.environ

# The Elastic Search endpoint to use.
ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
ELASTICSEARCH_URL = os.environ.get('SEARCHBOX_URL') or ELASTICSEARCH_URL
CLUSTER_NAME = os.environ['CLUSTER_NAME']
API_KEY = os.environ['API_KEY']
AIRPLANE_MODE = 'AIRPLANE_MODE' in os.environ
# TODO: PUBLIC_QUERIES = 'PUBLIC_QUERIES' in os.environ

# If S3 bucket doesn't exist, set it up.
BUCKET_NAME = 'elephant-{}'.format(CLUSTER_NAME)


# Elastic Search Stuff.
ES = ElasticSearch(ELASTICSEARCH_URL)
_url = urlparse.urlparse(ES.servers.live[0])
ES_AUTH = (_url.username, _url.password)

class TrunkStore(object):
    """An abstracted S3 Bucket. Allows for airplane mode :)"""

    def __init__(self, name, airplane_mode=False):
        self.bucket_name = name
        self.airplane_mode = airplane_mode

        if self.airplane_mode:
            mkdir_p('db')
        else:
            conn = boto.connect_s3()
            if self.bucket_name not in conn:
                self._bucket = boto.connect_s3().create_bucket(self.bucket_name)

            boto.connect_s3().get_bucket(self.bucket_name)

    def delete(self, key):
        if self.airplane_mode:
            os.remove('db/{}'.format(key))
            return

        return self._bucket.delete_key(key)

    def set(self, key, value):
        if self.airplane_mode:
            split = key.split('/')
            if len(split) > 1:
                mkdir_p('db/{}'.format(split[0]))

            with open('db/{}'.format(key), 'w') as f:
                f.write(value)
                return

        key = self._bucket.new_key(key)
        key.update_metadata({'Content-Type': 'application/json'})
        key.set_contents_from_string(value)

        return True

    def get(self, key):
        if self.airplane_mode:
            with open('db/{}'.format(key)) as f:
                return f.read()

        return self._bucket.get_key(key).read()

    def list(self):
        if self.airplane_mode:
            return os.listdir('db')

        return [k.name for k in self._bucket.list()]

def mkdir_p(path):
    """Emulates `mkdir -p` behavior."""
    try:
        makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise


def epoch(dt=None):
    """Returns the epoch value for the given datetime, defulting to now."""

    if not dt:
        dt = datetime.utcnow()

    return int(time.mktime(dt.timetuple()) * 1000 + dt.microsecond / 1000)



TRUNK = TrunkStore(name=BUCKET_NAME, airplane_mode=AIRPLANE_MODE)

class Collection(object):
    """A set of Records."""

    def __init__(self, name):
        self.name = name

    def __getitem__(self, k):
        return Record._from_uuid(k, collection=self.name)

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

        q['query'] = {'term': {'query': query}},

        results = ES.search(q, index=self.name, **params)

        params['es_q'] = query
        for hit in results['hits']['hits']:
            yield Record._from_uuid(hit['_id'], collection=self.name)

    def search(self, query, sort=None, size=None, **kwargs):
        """Returns a list of Records for the given query."""

        if sort is not None:
            kwargs['sort'] = sort
        if size is not None:
            kwargs['size'] = size

        return [r for r in self.iter_search(query, **kwargs)]

    def save(self):
        try:
            return ES.create_index(self.name)
        except (IndexAlreadyExistsError, InvalidJsonResponseError):
            pass

    def new_record(self):
        r = Record()
        r.collection_name = self.name
        return r



class Record(object):
    """A record in the database."""

    def __init__(self):
        self.uuid = str(uuid4())
        self.data = {}
        self.epoch = epoch()
        self.collection_name = None

    def __repr__(self):
        return "<Record:{0}:{1} {2}>".format(
                self.collection_name, self.uuid, repr(self.data))

    def __getitem__(self, *args, **kwargs):
        return self.data.__getitem__(*args, **kwargs)

    def __setitem__(self, *args, **kwargs):
        return self.data.__setitem__(*args, **kwargs)

    def save(self):
        self.epoch = epoch()

        self._persist()
        self._index()

    def delete(self):
        ES.delete(index=self.collection.name, doc_type='record', id=self.uuid)
        TRUNK.delete('{}/{}'.format(self.collection.name, self.uuid))

    def _persist(self):
        """Saves the Record to S3."""
        _key = '{0}/{1}'.format(self.collection_name, self.uuid)
        TRUNK.set(_key, self.json)

    def _index(self):
        """Saves the Record to Elastic Search."""
        return ES.index(self.collection.name, 'record', self.dict, id=self.uuid)

    @property
    def dict(self):
        d = self.data.copy()
        d.update(uuid=self.uuid, epoch=self.epoch)
        return d

    @property
    def json(self):
        return json.dumps({'record': self.dict})

    @property
    def collection(self):
        return Collection(name=self.collection_name)

    @classmethod
    def _from_uuid(cls, uuid, collection=None):
        if collection is None:
            collection, uuid = uuid.split('/', 2)

        result = ES.get(collection, 'record', uuid)['_source']

        r = cls()
        r.collection_name = collection
        r.uuid = result.pop('uuid', None)
        r.epoch = result.pop('epoch', None)
        r.data = result

        return r

    @classmethod
    def _from_uuid_s3(cls, uuid, collection=None):
        if collection:
            uuid = '{}/{}'.format(collection, uuid)
        else:
            collection = uuid.split('/')[0]

        key_content = TRUNK.get(uuid)
        j = json.loads(key_content)['record']

        r = cls()
        r.collection_name = collection
        r.uuid = j.pop('uuid', None)
        r.epoch = j.pop('epoch', None)
        r.data = j

        return r

@manager.command
def seed():
    """Seeds the index from the configured S3 Bucket."""

    print 'Creating Index...'
    c = Collection(CLUSTER_NAME)
    c.save()

    print 'Indexing...'
    for key in progress.bar([k for k in TRUNK.list()]):
         r = Record._from_uuid_s3(key)
         r._index()

@app.before_request
def require_apikey():
    """Blocks aunauthorized requests."""
    # TODO: Convert this to a decorator

    if app.debug:
        return

    valid_key_param = request.args.get('key') == API_KEY
    valid_key_header = request.headers.get('X-Key') == API_KEY
    valid_basic_pass = request.authorization.password == API_KEY if request.authorization else False

    if not (valid_key_param or valid_key_header or valid_basic_pass):
        return '>_<', 403

@app.route('/login')
def login_challenge():
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})


@app.route('/')
def get_collection():
    """Get a list of records from a given collection."""

    c = Collection(CLUSTER_NAME)

    args = request.args.to_dict()
    results = c.search(request.args.get('q'), **args)

    return jsonify(records=[r.dict for r in results])

@app.route('/', methods=['POST', 'PUT'])
def post_collection():
    """Add a new record to the trunk."""
    c = Collection(CLUSTER_NAME)
    c.save()

    record = c.new_record()
    record.data = request.json or request.form.to_dict()
    record.save()

    return get_record(CLUSTER_NAME, record.uuid)

@app.route('/<uuid>')
def get_record(uuid):
    """Get a record from the trunk."""

    # Don't let the browsers win.
    if uuid == 'favicon.ico':
        return '.'

    return jsonify(record=Collection(CLUSTER_NAME)[uuid].dict)

@app.route('/<uuid>', methods=['POST'])
def post_record(uuid):
    """Replaces a given Record."""
    record = Collection(CLUSTER_NAME)[uuid]
    record.data = request.json or request.form.to_dict()
    record.save()

    return get_record(CLUSTER_NAME, uuid)

@app.route('/<uuid>', methods=['PUT'])
def put_record(uuid):
    """Updates a given Record."""

    record = Collection(CLUSTER_NAME)[uuid]
    record.data.update(request.json or request.form.to_dict())
    record.save()

    return get_record(CLUSTER_NAME, uuid)

@app.route('/<uuid>', methods=['DELETE'])
def delete_record(uuid):
    """Deletes a given record."""
    Collection(CLUSTER_NAME)[uuid].delete()
    return redirect('/{}/'.format(CLUSTER_NAME))

if __name__ == '__main__':
    manager.run()
