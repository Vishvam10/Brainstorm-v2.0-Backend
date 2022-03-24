from application.validation import BusinessValidationError
from application.models import Deck, Review, User, Card
from application.database import db
from application.emails import *


from flask import request
from application.models import *
from application.database import db
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import create_access_token
from flask import current_app as app
from flask import jsonify, request

from werkzeug.utils import secure_filename
from flask import send_from_directory

import os
import bcrypt
import pandas as pd
import numpy as np
import uuid

# from flask import session

base_url = 'http://192.168.1.9:5000/'
uploads = app.config["UPLOAD_FOLDER"]

ALLOWED_EXTENSIONS = {'txt', 'csv', 'xls', 'xlsx'}

#~ LOGIN

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    username = data["username"]
    password = data["password"]
    user = db.session.query(User).filter(User.username == username).first()

    if(user is None):
        raise BusinessValidationError(
            status_code=400, error_message="Invalid username or no such user exists")

    if(password != ""):
        hashed_password = user.password
        string_password = hashed_password.decode('utf8')
        if(not bcrypt.checkpw(password.encode('utf8'), string_password.encode('utf8'))):
            raise BusinessValidationError(
                status_code=400, error_message="Incorrect Password")

    access_token = create_access_token(identity=username)

    return_value = {
        "message": "Logged in successfully",
        "status": 200,
        "user_id": user.user_id,
        "access_token": access_token
    }
    return jsonify(return_value)

# _ This should be a Celery Job

@app.route('/api/upload', methods=["POST"])
@jwt_required()
def upload():
    deck_id = request.form.get("deck_id")
    file = request.files.get("File")
    print(deck_id)
    print(file)
    if file.filename == '':
        return "ENTER FILENAME"
    if file and allowed_file(file.filename):
        file_type = file.filename.split(".")[1]
        fn = "QA_Upload_" + deck_id + "." + file_type 
        uploaded_filename = secure_filename(fn)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], uploaded_filename))
        # parse_file(filename, file_type, deck_id)

    return_value = {
        "message": "Imported successfully",
        "file_name" : uploaded_filename,
        "file_type" : file_type,
        "status": 200,
    }
    return jsonify(return_value)

# _ This should be a Celery Job 

@app.route("/api/download/<path:name>", methods=["GET"])
def download_file(name):
    # fn = "QA_Upload_" + deck_id + "." + file_type
    return send_from_directory(app.config['UPLOAD_FOLDER'], name, as_attachment=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/sample', methods=["GET"])
@jwt_required()
def sample() :
    return_value = {
        "message": "Reached" 
    }
    return jsonify(return_value)

@app.route('/api/send_email', methods=["POST"])
def send() :
    data = request.json
    to_address = data["to_address"]
    subject = data["subject"]
    message = data["message"]
    send_email(to_address, subject, message)
    return_value = {
        "message": "Email Sent" 
    }
    return jsonify(return_value)
