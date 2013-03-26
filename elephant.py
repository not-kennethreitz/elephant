# -*- coding: utf-8 -*-

import os
from uuid import uuid4

from flask import Flask
from pyelasticsearch import ElasticSearch


app = Flask(__name__)

# The Elastic Search endpoint to use.
ELASTICSEARCH_URL = os.environ['ELASTICSEARCH_URL']
CLUSTER_NAME = os.environ['CLUSTER_NAME']
API_KEY = os.environ['API_KEY']


@app.route('/')
def hello_world():
    return 'Hello World!'

if __name__ == '__main__':
    app.run()