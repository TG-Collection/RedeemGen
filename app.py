from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from datetime import datetime, timedelta
import random
import string
import os

app = Flask(__name__)


# Read MongoDB URL from environment variables
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb+srv://gen:gen@gen.fuemgjr.mongodb.net/?retryWrites=true&w=majority')

client = MongoClient(MONGODB_URL)
db = client.licenceCodesDB
codes = db.codes
access_keys = db.access_keys

def generate_license_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def generate_access_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

@app.route('/generate_access_key', methods=['GET'])
def generate():
    while True:
        access_key = generate_access_key()
        try:
            access_keys.insert_one({"_id": access_key})
            return {"access_key": access_key}, 200
        except DuplicateKeyError:
            continue

@app.route('/', methods=['GET'])
def landing_page():
    return render_template('index.html')

@app.route('/', methods=['GET'])
def home():
    access_key = request.args.get('access_key')
    operation = request.args.get('action')
    validate = request.args.get('days', default=30)
    code = request.args.get('code')
    
    # Validate access_key here
    access_key_entry = access_keys.find_one({"_id": access_key})
    if access_key_entry is None:
        return {"message": "Invalid access key"}, 403

    if operation == 'generate':
        expiration_date = datetime.now() + timedelta(days=int(validate))
        while True:
            license_code = generate_license_code()
            try:
                codes.insert_one({"_id": license_code, "expiration_date": expiration_date, "used": False})
                return {"license_code": license_code}, 200
            except DuplicateKeyError:
                continue
    elif operation == 'validate':
        entry = codes.find_one({"_id": code})
        if entry is None:
            return {"message": "Invalid code"}, 404
        elif entry["used"] == True:
            return {"message": "This code is already in use"}, 403
        elif entry["expiration_date"] < datetime.now():
            return {"message": "The code has expired"}, 403
        else:
            codes.update_one({"_id": code}, {"$set": {"used": True}})
            return {"message": "Code validated successfully"}, 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
