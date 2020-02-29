import numpy as np
import pickle
import hashlib
import json
import re

from bson import json_util
from flask import Flask, request, jsonify, render_template, abort
from flask_pymongo import PyMongo 
from flask_cors import CORS, cross_origin

mongo = PyMongo()

app = Flask(__name__)

# app.config["MONGO_URI"] = 'connection string goes here'
#Example_____________
app.config["MONGO_URI"] = 'mongodb+srv://strainer_admin:strainer_admin123@strainercluster-igrpg.azure.mongodb.net/strainer?retryWrites=true&w=majority'
CORS(app)

app.config['CORS_HEADERS'] = 'Content-Type'

mongo.init_app(app)

class AfterThisResponse:
    def __init__(self, app=None):
        self.callbacks = []
        if app:
            self.init_app(app)

    def __call__(self, callback):
        self.callbacks.append(callback)
        return callback

    def init_app(self, app):
        # install extensioe
        app.after_this_response = self

        # install middleware
        app.wsgi_app = AfterThisResponseMiddleware(app.wsgi_app, self)

    def flush(self):
        try:
            for fn in self.callbacks:
                try:
                    fn()
                except Exception:
                    traceback.print_exc()
        finally:
            self.callbacks = []

class AfterThisResponseMiddleware:
    def __init__(self, application, after_this_response_ext):
        self.application = application
        self.after_this_response_ext = after_this_response_ext

    def __call__(self, environ, start_response):
        iterator = self.application(environ, start_response)
        try:
            return ClosingIterator(iterator, [self.after_this_response_ext.flush])
        except Exception:
            traceback.print_exc()
            return iterator

AfterThisResponse(app)

@app.route('/')
@cross_origin()
def home():
    return render_template('index.html')

@app.route('/setdata/<id>', methods=['POST'])
@cross_origin()
def setdata(id):
    try:
        queryId = int(id)
    except:
        return jsonify({'message': 'Not a valid Id'}), 400
    
    query_collection = mongo.db.queries
    # result = json.dumps(list(query_collection.find({'queryId' : queryId},{ "_id": 0, "queryId": 1 })), default=json_util.default)
    # if result == "[]":
    #     return jsonify({'queryId': queryId, 'message': 'No tweet is available for that Id'}), 400
    # query_collection.update({ "queryId": queryId },{ '$set': { "dataCollected": True }})

    @app.after_this_response
    def post_process():
        responce = requests.get('https://strainer-data-demo.herokuapp.com/get/'+ str(queryId))
        for tweet in responce.json(): 
            # To do work
            print(tweet['tweet'])

            # End of work
        query_collection.update({ "queryId": queryId },{ '$set': { "network": True }})

if __name__ == "__main__":
    app.run(debug=True)