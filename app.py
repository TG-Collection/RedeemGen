from flask import Flask, request, render_template
from pymongo import MongoClient, errors
from random import choice
from string import ascii_uppercase, digits
from datetime import datetime, timedelta
import os

app = Flask(__name__)


# Read MongoDB URL from environment variables
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb+srv://gen:gen@gen.fuemgjr.mongodb.net/?retryWrites=true&w=majority')

client = MongoClient(MONGODB_URL)
db = client['license_db']
codes = db['codes']
access_keys = db['access_keys']

app = Flask(__name__)

def generate_license_code():
    return ''.join(choice(ascii_uppercase + digits) for _ in range(20))

@app.route('/')
def home():
    action = request.args.get('action')

    if action is None:
        return render_template('index.html')

    if action == 'generate_key':
        generated_key = generate_license_code()
        try:
            access_keys.insert_one({"_id": generated_key})
            return {"access_key": generated_key}, 200
        except errors.DuplicateKeyError:
            return home()

    access_key = request.args.get('access_key')
    if access_keys.find_one({"_id": access_key}) is None:
        return {"message": "Invalid access key"}, 401

    if action == 'generate':
        time_in_days = int(request.args.get('days', 30))  # Set default validation period to 30 days
        expiration_date = datetime.now() + timedelta(days=time_in_days)
        license_code = generate_license_code()
        try:
            codes.insert_one({"_id": license_code, "expiration_date": expiration_date, "used": False, "access_key": access_key})
            return {"license_code": license_code}, 200
        except errors.DuplicateKeyError:
            return home()

    elif action == 'validate':
        code = request.args.get('code')
        entry = codes.find_one({"_id": code})
        if entry is None:
            return {"message": "Invalid code"}, 404
        elif entry["access_key"] != access_key:
            return {"message": "This code does not belong to the provided access key"}, 403
        elif entry["used"] == True:
            return {"message": "This code is already in use"}, 403
        elif entry["expiration_date"] < datetime.now():
            return {"message": "The code has expired"}, 403
        else:
            codes.update_one({"_id": code}, {"$set": {"used": True}})
            return {"message": "Code validated successfully"}, 200

    return render_template('index.html')

            
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
