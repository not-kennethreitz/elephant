import json
import os
from uuid import uuid4

import maya
import boto3
import botocore
from flask import Flask, request, jsonify

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q


# Set environment variables.
BUCKET_NAME = os.environ['BYODEMO_BUCKET_NAME']
ES_URL = os.environ['FOUNDELASTICSEARCH_URL']
ES_PASSWORD = os.environ['ES_PASSWORD']
CLUSTER_NAME = 'elephant'

# Set environment variables that boto expects.
os.environ['AWS_ACCESS_KEY_ID'] = os.environ['BYODEMO_AWS_ACCESS_KEY_ID']
os.environ['AWS_SECRET_ACCESS_KEY'] = os.environ['BYODEMO_AWS_SECRET_ACCESS_KEY']

# Amazon S3.
s3 = boto3.resource('s3')
bucket = s3.Bucket(BUCKET_NAME)
bucket_exists = True

# Elastic search.
es = Elasticsearch([ES_URL], http_auth=('elastic', ES_PASSWORD))

# Ensure that bucket exists.
try:
    s3.meta.client.head_bucket(Bucket='mybucket')
except botocore.exceptions.ClientError as e:
    error_code = int(e.response['Error']['Code'])
    if error_code == 404:
        bucket_exists = False
assert bucket_exists

# Database stuff.
class TrunkStore(object):
    def __init__(self, bucket):
        self.bucket = bucket

    def get(self, key):
        """Gets an object from S3."""
        return s3.Object(self.bucket.name, key).get()['Body'].read()

    def set(self, key, value):
        """Sets an object on S3."""
        return s3.Object(self.bucket.name, key).put(Body=value)

    def delete(self, key):
        """Removes an object from S3."""
        return s3.Object(self.bucket.name, key).delete()

    def list(self):
        return [key.key for key in self.bucket.objects.all()]

trunk = TrunkStore(bucket=bucket)


class Collection(object):
    """A set of Record.s"""
    def __init__(self):
        pass

    def __getitem__(self, k):
        return Record._from_uuid(k)

    def iter_search(self, query, size=100, **kwargs):

        index = CLUSTER_NAME

        results = Search(using=es, index=CLUSTER_NAME).query('query_string', query=query).sort('-epoch')[:size].execute()
        # print results

        for hit in results:
            yield Record._from_uuid(hit['uuid'])

    def search(self, query, size=10, **kwargs):

        return [r for r in self.iter_search(query, size=size, **kwargs)]

    def new_record(self):
        r = Record()
        return r

    def purge(self):
        for record in self.iter_search('*', size=9999):
            record.purge()

    def seed(self):
        for key in trunk.list():
            r = Record._from_uuid_s3(key)
            r.save()

collection = Collection()

class Record(object):
    """A record in the collection."""
    def __init__(self):
        self.uuid = str(uuid4())
        self.data = {}
        self.epoch = maya.now().epoch

    def __repr__(self):
        return "<Record:{0} {1}>".format(self.uuid, repr(self.data))

    def __getitem__(self, *args, **kwargs):
        return self.data.__getitem__(*args, **kwargs)

    def __setitem__(self, *args, **kwargs):
        return self.data.__setitem__(*args, **kwargs)

    def save(self):
        self.epoch = maya.now().epoch

        self._persist()
        self._index()

    def delete(self):
        es.delete(index=CLUSTER_NAME, doc_type='record', id=self.uuid)
        trunk.delete(self.uuid)

    def purge(self):
        es.delete(index=CLUSTER_NAME, doc_type='record', id=self.uuid)

    def _persist(self):
        """Saves the Record to S3."""
        trunk.set(self.uuid, self.json)

    def _index(self):
        """Saves the Record to Elastic Search."""
        return es.index(CLUSTER_NAME, 'record', self.dict, id=self.uuid)

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
        return Collection()

    @classmethod
    def _from_uuid(cls, uuid):
        result = Search(using=es, index=CLUSTER_NAME).query('match', uuid=uuid).execute()[0]
        result = result.to_dict()

        r = cls()
        r.uuid = result.pop('uuid', None)
        r.epoch = result.pop('epoch', None)
        r.data = result

        return r

    @classmethod
    def _from_uuid_s3(cls, uuid):
        key_content = trunk.get(uuid)
        j = json.loads(key_content)['record']

        r = cls()
        r.uuid = j.pop('uuid', None)
        r.epoch = j.pop('epoch', None)
        r.data = j

        return r



# Flask stuff.
app = Flask(__name__)
app.debug = True

# Application routes.
@app.route('/')
def get_collection():
    """Get a list of records from a given collection."""

    args = request.args.to_dict()

    # Convert size to int, for Python.
    if 'size' in args:
        args['size'] = int(args['size'])

    results = collection.search(request.args.get('q', '*'), **args)

    return jsonify(records=[r.dict for r in results])

@app.route('/', methods=['POST', 'PUT'])
def post_collection():
    """Add a new record to a given collection."""

    record = collection.new_record()
    record.data = request.json or request.form.to_dict()
    record.save()

    return get_record(record.uuid)

@app.route('/<uuid>')
def get_record(uuid):
    """Get a record from a given collection."""

    return jsonify(record=collection[uuid].dict)

@app.route('/<uuid>', methods=['POST'])
def post_record(uuid):
    """Replaces a given Record."""

    record = collection[uuid]
    record.data = request.json or request.form.to_dict()
    record.save()

    return get_record(uuid)


@app.route('/<uuid>', methods=['PUT'])
def put_record(uuid):
    """Updates a given Record."""

    record = collection[uuid]
    record.data.update(request.json or request.form.to_dict())
    record.save()

    return get_record(uuid)

@app.route('/<uuid>', methods=['DELETE'])
def delete_record(uuid):
    """Deletes a given record."""

    collection[uuid].delete()
    return redirect('/')

if __name__ == '__main__':
    app.run()