# -*- coding: utf-8 -*-

import os
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



@app.before_request
def require_apikey():
    assert request.params.get('key') == API_KEY

    return '-_-', 403

@app.route('/')
def hello_world():
    return 'Hello World!'

if __name__ == '__main__':
    app.run()