import json
from application.validation import BusinessValidationError
from application.models import Deck, Review, User, Card
from sqlalchemy import and_
from flask import request
from application.models import *
from application.database import db
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import create_access_token
from flask import current_app as app
from flask import Flask, jsonify, request, redirect, url_for

from werkzeug.utils import secure_filename
from flask import send_from_directory

import os
import bcrypt

# from flask import session


base_url = 'http://192.168.1.9:5000/'

#~ LOGIN


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data["username"]
    password = data["password"]
    email = data["email"]
    user = db.session.query(User).filter(User.username == username).first()

    if(user is None):
        raise BusinessValidationError(
            status_code=400, error_message="Invalid username or no such user exists")

    if(user.email_id != email):
        raise BusinessValidationError(
            status_code=400, error_message="Incorrect Email")

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


@app.route('/protected', methods=["GET"])
@jwt_required()
def sample():
    current_user = get_jwt_identity()
    return_value = {
        "current_user": current_user
    }
    return jsonify(return_value)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=["POST"])
@jwt_required()
def upload() :
    for file in request.files.getlist("File") :
        print(file)
        if file.filename == '' :
            return "ENTER FILENAME"
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    print("FORM : ", request.form)
    print("DATA : ", request.data)
    return "UPLOAD"

@app.route("/download/<path:name>", methods=["GET"])
def download_file(name):
    return send_from_directory(app.config['UPLOAD_FOLDER'], name, as_attachment=True)