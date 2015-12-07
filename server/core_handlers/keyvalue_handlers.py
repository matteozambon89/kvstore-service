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
from pyserver.core import app, get_storage_location, make_my_response_json
from pyserver.core import convert_types_in_dictionary, remove_single_element_lists
from pyserver.core import json_response

ddb_kvstore = Table(os.environ.get('KVSTORE_DYNAMO_TABLE', 'kv-store'))
s3_conn = boto.connect_s3()
s3_bucket = s3_conn.get_bucket(os.environ.get('KVSTORE_S3_BUCKET', 'kvstore-large.glgroup.com'))

def add_cors(response):
    response[2]['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
    response[2]['Access-Control-Allow-Credentials'] = 'true'
    response[2]['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    response[2]['Access-Control-Allow-Headers'] = request.headers.get('Access-Control-Request-Headers', '*')

@app.route("/kv/__user_betas__/<path:keys>", methods=["OPTIONS"])
@app.route('/kv/<path:key>', methods=['OPTIONS'])
def allow_cors(keys='', key='', data=''):
    response = make_response(data)
    response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = request.headers.get('Access-Control-Request-Headers', '*')
    return response

def get_storage_path_for(key):
    hash_o = hashlib.sha256()
    hash_o.update(key)
    storage_key = hash_o.hexdigest()
    return os.path.join(
        storage_key[:2],
        storage_key[2:4],
        storage_key
    )

def store_it(key, data, content_type):
    try:
        ddb_kvstore.put_item(data={'key': key, 'path':get_storage_path_for(key), 'body':data,'content-type':content_type}, overwrite=True)
    except ValidationException, e:
        # if we get an "it's too big" exception we'll put it in our s3
        # kvstore 'big stuff' bucket
        newS3Key = S3Key(s3_bucket)
        newS3Key.key = get_storage_path_for(key)
        newS3Key.set_metadata('content-type', content_type)
        newS3Key.set_metadata('key', key)
        newS3Key.set_contents_from_string(data);

def read_it(key):
    try:
        item = ddb_kvstore.get_item(path=get_storage_path_for(key))
        return item['content-type'], item['body'], key
    except ItemNotFound, e:
        # could be because it's super big, so we'll try our s3 bucket before
        # giving up for good
        try:
            s3Key = S3Key(s3_bucket)
            s3Key.key = get_storage_path_for(key)
            body = s3Key.get_contents_as_string()
            content_type = s3Key.get_metadata('content-type')
            return content_type, body, key
        except S3ResponseError, e:
            logging.error("unable to find item for key %s anywhere\n%s", key, e)

        return None, None, None

def delete_it(key):
    ddb_kvstore.delete_item(path=get_storage_path_for(key))

@app.route("/kv/<path:key>", methods=["POST"])
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

@app.route("/kv/<path:key>", methods=["GET"])
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
    add_cors(response)
    return response


@app.route("/kv/__multikey__/<path:keys>", methods=["GET"])
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

    add_cors(response)
    return response

@app.route("/kv/__beta_groups__/<path:keys>", methods=["GET"])
def pyserver_core_keyvalue_handlers_get_beta_groups(keys=None):
    keys = keys.split('/')

    content_type, value, file_path = read_it('bmp_data')
    bmp_value = json.loads(value)
    groups = dict( (item['name'], item['users']) for item in bmp_value['groups'] )

    values = {}
    for key in keys:
        if key in groups:
            values[key] = groups[key]
        else:
            values[key] = []

    callback = request.values.get("callback", None)

    if callback:
        response = "%s(%s);" % (callback, json.dumps(values)), 200, {"Content-Type": "application/javascript"}
    else:
        response = json.dumps(values), 200, {"Content-Type": 'application/json' }

    response[2]['X-File-Path'] = file_path
    add_cors(response)
    return response

@app.route("/kv/__user_betas__/<path:keys>", methods=["GET"])
def pyserver_core_keyvalue_handlers_get_user_betas(keys=None):
    keys = keys.split('/')

    content_type, value, file_path = read_it('bmp_data')
    bmp_value = json.loads(value)
    users = {}
    for user in keys:
        users[user] = []

    for group in bmp_value['groups']:
        for user in group['users']:
            if user in users:
                users[user].append(group['name'])

    callback = request.values.get("callback", None)

    if callback:
        response = "%s(%s);" % (callback, json.dumps(users)), 200, {"Content-Type": "application/javascript"}
    else:
        response = json.dumps(users), 200, {"Content-Type": 'application/json' }

    response[2]['X-File-Path'] = file_path
    add_cors(response)
    return response

@app.route("/kv/__multikey__", methods=["POST"])
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

@app.route("/kv/<path:key>", methods=["DELETE"])
@make_my_response_json
def pyserver_core_keyvalue_handlers_delete_data_for(key):
    """
        Removes all stored data for a given key.
    """
    delete_it(key)
    return dict(message="ok")
