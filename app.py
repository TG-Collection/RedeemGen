# app.py
from flask import Flask, request, Blueprint, jsonify, render_template
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from datetime import datetime, timedelta
from werkzeug.exceptions import HTTPException
import string
import random
import os
import logging

app = Flask(__name__)
bp = Blueprint('license', __name__, url_prefix='/')

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Read MongoDB URL from environment variables
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb+srv://gen:gen@gen.fuemgjr.mongodb.net/?retryWrites=true&w=majority')

client = MongoClient(MONGODB_URL)
db = client["license_db"]
codes = db["codes"]

def generate_license_code(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

@app.route('/')
def landing_page():
    return render_template('index.html')

@bp.route('/')
def home():
    if 'generate_key' in request.args:
        time_in_days = int(request.args.get('validate'))
        expiration_date = datetime.now() + timedelta(days=time_in_days)

        try:
            license_code = generate_license_code()
            codes.insert_one({"_id": license_code, "expiration_date": expiration_date, "used": False})
            return {"license_code": license_code}, 200
        except DuplicateKeyError:
            return home()
    elif 'validate' in request.args:
        code = request.args.get('validate')
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
    else:
        return {"message": "Invalid request"}, 400

# Add a handler for all uncaught exceptions
@app.errorhandler(Exception)
def handle_error(e):
    code = 500
    if isinstance(e, HTTPException):
        code = e.code
    return jsonify(error=str(e)), code

app.register_blueprint(bp)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)

