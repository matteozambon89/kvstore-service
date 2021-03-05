import os
import json
import uuid
import errno
import hashlib
import logging
import boto
from functools import wraps
from flask import request, make_response
from boto.s3.key import Key as S3Key
from boto.exception import S3ResponseError
from boto.dynamodb2.table import Table
from boto.dynamodb2.exceptions import ItemNotFound, ValidationException
from boto.s3.connection import OrdinaryCallingFormat
from server.core import app, get_storage_location, make_my_response_json
from server.core import convert_types_in_dictionary, remove_single_element_lists
from server.core import json_response, return_cors_response

ddb_table_name = os.environ.get('KVSTORE_DYNAMO_TABLE', 'kvstore')
s3_bucket_name = os.environ.get('KVSTORE_S3_BUCKET', 'kvstore-large')
logging.info("Using DDB table: %s" % (ddb_table_name))
logging.info("Using S3 bucket %s for large objects" %(s3_bucket_name))

ddb_kvstore = Table(ddb_table_name)

if "." in s3_bucket_name:
    logging.debug("Using ordinary calling format for s3 connection")
    s3_conn = boto.connect_s3(calling_format=OrdinaryCallingFormat())
else:
    logging.debug("Using standard s3 connection")
    s3_conn = boto.connect_s3()

s3_bucket = s3_conn.get_bucket(s3_bucket_name)

def get_storage_path_for(key):
    hash_o = hashlib.sha256()
    hash_o.update(key.encode())
    storage_key = hash_o.hexdigest()
    return os.path.join(
        storage_key[:2],
        storage_key[2:4],
        storage_key
    )

def store_it(key, data, content_type):
    try:
        ddb_kvstore.put_item(data={'key': key, 'path':get_storage_path_for(key), 'body':data,'content-type':content_type}, overwrite=True)
    except ValidationException as e:
        # if we get an "it's too big" exception we'll put it in our s3
        # kvstore 'big stuff' bucket
        newS3Key = S3Key(s3_bucket)
        newS3Key.key = get_storage_path_for(key)
        newS3Key.set_metadata('content-type', content_type)
        newS3Key.set_metadata('key', key)
        newS3Key.set_contents_from_string(data)

def read_it(key):
    try:
        item = ddb_kvstore.get_item(path=get_storage_path_for(key))
        return item['content-type'], item['body'], key
    except ItemNotFound as e:
        # could be because it's super big, so we'll try our s3 bucket before
        # giving up for good
        try:
            s3Key = S3Key(s3_bucket)
            s3Key.key = get_storage_path_for(key)
            body = s3Key.get_contents_as_string()
            content_type = s3Key.get_metadata('content-type')
            return content_type, body, key
        except S3ResponseError as e:
            logging.debug("unable to find item for key %s anywhere\n%s", key, e)

        return None, None, None

def delete_it(key):
    ddb_kvstore.delete_item(path=get_storage_path_for(key))

@app.route("/<path:key>", methods=["OPTIONS"])
def pyserver_core_keyvalue_handlers_options_handler(key=None):
    return return_cors_response()

@app.route("/<path:key>", methods=["POST"])
@make_my_response_json
def pyserver_core_keyvalue_handlers_store_data(key=None):
    """
        Store all of the data provided in the body of the request, associated with the
        specified key.  The data stored includes the content type information of the request
        so on fetch the content type will be set as it was when the data was stored.

        :statuscode 200: provided data has been successfully stored by the given key
    """
    store_this_content_type = request.content_type
    store_this = None
    if request.json:
        store_this = json.dumps(request.json)
    elif request.data:
        store_this = request.data

    if not store_this and request.values.to_dict:
        # for form data we're going to conveniently store it as a json
        # blob, so it can be easily parsed when retrieved
        data = request.values.to_dict(flat=False)
        store_this = convert_types_in_dictionary(remove_single_element_lists(data))
        store_this = json.dumps(store_this)
        store_this_content_type = 'application/json'

    store_it(key, store_this, content_type=store_this_content_type)

    return {"message": "ok"}

@app.route("/<path:key>", methods=["GET"])
def pyserver_core_keyvalue_handlers_get_data_for(key=None):
    """
        For a given key return the data stored, if any.

        :statuscode 200: data found, and returned
        :statuscode 404: no stored data found for provided key
    """

    return404 = request.values.get("return404", None)
    content_type, value, file_path = read_it(key)
    callback = request.values.get("callback", None)
    if not value:
        if callback:
            # this is specifically to handle the (most common) use case of JSONP blowing
            # chunks if the response is a 404 as the borwser will not do anything further
            # causing the callback in your javascript library to never fire
            response = json_response(**dict(message="no data for key"))
        elif return404 and return404 == "false":
            response = json_response(**dict(message="no data for key"))
        else:
            response = json_response(**dict(message="no data for key", status_code=404))
    else:
        if callback:
            response = ("%s(%s);" % (callback, value), 200, {"Content-Type": "application/javascript"})
        else:
            response = (value, 200, {"Content-Type": content_type })

    response[2]['X-File-Path'] = file_path
    return response


@app.route("/__multikey__/<path:keys>", methods=["GET"])
def pyserver_core_keyvalue_handlers_get_data_for_multi(keys=None):
    """
        For a given set of keys return the data stored, if any.

        :statuscode 200: data found, and returned
        :statuscode 404: no stored data found for provided keys
    """
    keys = keys.split('/')

    values = {}
    first_content_type = None
    for key in keys:
        content_type, value, file_path = read_it(key)
        if value:
            if content_type == 'application/json':
                value = json.loads(value)
            first_content_type = content_type
            values[key] = value

    if first_content_type and first_content_type == 'application/json':
        values = json.dumps(values)

    return404 = request.values.get("return404", None)
    callback = request.values.get("callback", None)
    if not values:
        if callback:
            # this is specifically to handle the (most common) use case of JSONP blowing
            # chunks if the response is a 404 as the borwser will not do anything further
            # causing the callback in your javascript library to never fire
            response = json_response(**dict(message="no data for key"))
        elif return404 and return404 == "false":
            response = json_response(**dict(message="no data for key"))
        else:
            response = json_response(**dict(message="no data for key", status_code=404))

    else:
        if callback:
            response = "%s(%s);" % (callback, values), 200, {"Content-Type": "application/javascript"}
        else:
            response = values, 200, {"Content-Type": first_content_type }
    return response

@app.route("/__multikey__", methods=["POST"])
@make_my_response_json
def pyserver_core_keyvalue_handlers_store_data_multi():
    """
        Only stores JSON.

        :statuscode 200: provided data has been successfully stored by the given key
    """

    if request.content_type == 'application/json':
        for key in request.json:
            store_this = json.dumps(request.json[key])
            store_it(key, store_this, content_type='application/json')
    else:
        for key in request.values:
            store_it(key, request.values[key], content_type=request.content_type)

    return dict(message="ok")

@app.route("/<path:key>", methods=["DELETE"])
@make_my_response_json
def pyserver_core_keyvalue_handlers_delete_data_for(key):
    """
        Removes all stored data for a given key.
    """
    delete_it(key)
    return dict(message="ok")
