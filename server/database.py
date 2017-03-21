import numpy as np
from pymongo import MongoClient


def find_unique_resource(collection):
    '''Returns the single object present in the collection.'''
    the_object = collection.find_one()


