from flask import Flask, render_template, request
from pymongo import MongoClient, errors
from datetime import datetime, timedelta
from random import choice
from string import ascii_uppercase, digits
from bson.objectid import ObjectId

app = Flask(__name__)


# Read MongoDB URL from environment variables
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb+srv://gen:gen@gen.fuemgjr.mongodb.net/?retryWrites=true&w=majority')

client = MongoClient(MONGODB_URL)
db = client["license_db"]
codes = db["codes"]
access_keys = db.get_collection('access_keys')

def generate_license_code():
    return ''.join(choice(ascii_uppercase + digits) for _ in range(10))

@app.route('/')
def home():
    access_key = request.args.get('access_key')
    user = access_keys.find_one({"_id": access_key})

    if user is None:
        return {"message": "Invalid access key"}, 403

    action = request.args.get('action')
    if action == 'generate':
        time_in_days = int(request.args.get('days', 30))
        expiration_date = datetime.now() + timedelta(days=time_in_days)

        try:
            license_code = generate_license_code() + str(user["_id"])
            codes.insert_one({"_id": license_code, "expiration_date": expiration_date, "used": False, "user_id": str(user["_id"])})
            return {"license_code": license_code}, 200
        except errors.DuplicateKeyError:
            return home()
    elif action == 'validate':
        code = request.args.get('code')
        entry = codes.find_one({"_id": code})

        if entry is None or entry["user_id"] != str(user["_id"]):
            return {"message": "Invalid code"}, 404
        elif entry["used"] == True:
            return {"message": "This code is already in use"}, 403
        elif entry["expiration_date"] < datetime.now():
            return {"message": "The code has expired"}, 403
        else:
            codes.update_one({"_id": code}, {"$set": {"used": True}})
            return {"message": "Code validated successfully"}, 200
    else:
        return render_template('index.html')

@app.route('/generate_access_key')
def generate_access_key():
    user_id = ObjectId()
    access_key = generate_license_code()

    access_keys.insert_one({"_id": access_key, "user_id": str(user_id)})

    return {"access_key": access_key}, 200



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

