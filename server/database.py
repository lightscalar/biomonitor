'''Routines for dealing with MongoDB output.'''
from bson import ObjectId
import numpy as np
from pymongo import MongoClient


def find_unique_resource(collection):
    '''Returns the single object present in the collection.'''
    the_object = collection.find_one()


def update_document(document, collection):
    query = {'_id': document['_id']}
    collection.update_one(query, {'$set': document}, upsert=False)


def find_document(document_id, collection):
    query = {'_id': string_to_obj(document_id)}
    return collection.find_one(query)


def string_to_obj(string):
    return ObjectId(string)


def goodify(obj):
    '''Loop through a mongo object and convert '_id' field to string.'''
    if '_id' in obj:
        obj['_id'] = str(obj['_id'])
    return obj


def serialize_mongo(result):

    # If it is a list, iterate over it.
    if type(result) == list:
        out = []
        for obj in result:
            out.append(goodify(obj))
        return out
    else:
        out = goodify(result)
    return out


