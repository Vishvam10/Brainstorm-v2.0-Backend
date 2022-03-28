from application.validation import BusinessValidationError
from application.models import Deck, Review, User, Card
from application.database import db
from application.helpers import *
from application.tasks import *

from flask import request
from application.models import *
from application.database import db
from flask_jwt_extended import jwt_required
from flask_jwt_extended import create_access_token
from flask import current_app as app
from flask import jsonify, request

from werkzeug.utils import secure_filename

from app import cache

import os
import bcrypt
import pandas as pd
import numpy as np
import statistics as st
import uuid
import difflib

# from flask import session

base_url = 'http://192.168.1.9:5000/'
media = app.config["MEDIA_FOLDER"]

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
        "user_name" : username,
        "access_token": access_token
    }
    return jsonify(return_value)


#+ Uses Celery Jobs 

@app.route('/api/upload', methods=["POST"])
@jwt_required()
def upload():
    deck_id = request.form.get("deck_id")
    file = request.files.get("File")
    if file.filename == '':
        return "ENTER FILENAME"
    if file and allowed_file(file.filename):
        file_type = file.filename.split(".")[1]
        fn = "QA_Upload_" + deck_id + "." + file_type 
        uploaded_filename = secure_filename(fn)
        file.save(os.path.join(media, uploaded_filename))
        res = parse_file.delay(fn, file_type, deck_id)
    if(res) :
        return_value = {
            "message": "Imported successfully",
            "file_name" : uploaded_filename,
            "file_type" : file_type,
            "status": 200,
        }    
    else :
        return_value = {
            "message": "Import failed",
            "file_name" : uploaded_filename,
            "file_type" : file_type,
            "status": 500,
        }

    return jsonify(return_value)

#+ Uses Celery Jobs 

@app.route("/api/download/<string:deck_id>", methods=["POST"])
@jwt_required()
def download_file(deck_id):
    data = request.json
    user_id = data["user_id"]

    user = db.session.query(User).filter(User.user_id == user_id).first()
    upr = user.__dict__["user_preferences"]
    if(upr is None) :
        file_type = "csv" 
    else :
        u_pref = ast.literal_eval(upr)
        report_format = u_pref["export_format"]
        if(report_format == "csv") :
            file_type = "csv"
        elif(report_format == "excel") :
            file_type = "xlsx"
        else :
            file_type = "xlsx"

    
    fn = convert_and_send_file.delay(file_type=file_type, deck_id=deck_id).get()
    if(fn != "Invalid File Type") :
        return send_file(fn, mimetype='text/csv', attachment_filename=fn, as_attachment=True)
    
    return_value = {
        "message": "Invalid file type" 
    }

    return jsonify(return_value)

@app.route('/sample', methods=["GET"])
def sample() :
    send_performance_reports.delay()
    
    return_value = {
        "message": "Reached" 
    }
    return jsonify(return_value)

@app.route('/api/send_email', methods=["POST"])
def send() :
    data = request.json
    to_address = data["to_address"]
    subject = data["subject"]
    template = "./email_templates/welcome.html"
    d = {
        "user_name" : "Vishvam"
    }
    msg = format_message(template_file=template, data=d)
    
    send_email.delay(to_address, subject, msg, content="html")
    return_value = {
        "message": "Email Sent" 
    }
    return jsonify(return_value)


@app.route('/api/performance/<string:user_id>', methods=["GET"])
@cache.memoize(50)
def performance(user_id) :
    scores = []
    decks = db.session.query(Deck).filter(Deck.user_id == user_id).all()
    for deck in decks :
        reviews = db.session.query(Review).filter(Review.deck_id == deck.deck_id).all()
        for review in reviews :
            rev = review.__dict__
            scores.append({"deck_name" : deck.deck_name, "score" : rev["score"]})
    avg_score = 0   
    if(len(scores) > 1 ) :
        avg_score = round(float(sum(score['score'] for score in scores)) / len(scores), 2)
    max_score = max(scores, key=lambda d: d['score'], default=0)
    min_score = min(scores, key=lambda d: d['score'], default=0)
    revision_required = []
    for x in scores :
        s = round(x["score"],2)
        if(s < avg_score) :
            revision_required.append(x["deck_name"])
    return_value = {
        "max_score" : max_score["score"],
        "max_score_deck" : max_score["deck_name"],
        "min_score" : min_score["score"],
        "min_score_deck" : min_score["deck_name"],
        "avg_score" : avg_score,
        "revision_required" : revision_required
    }
    return jsonify(return_value)
    

#_ HELPER FUNCTIONS 

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def show_diff(seqm):
    output= []
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
        if opcode == 'equal':
            output.append(seqm.a[a0:a1])
        elif opcode == 'insert':
            output.append("<ins>" + seqm.b[b0:b1] + "</ins>")
        elif opcode == 'delete':
            output.append("<del>" + seqm.a[a0:a1] + "</del>")
        elif opcode == 'replace':
            raise NotImplementedError
        else:
            raise RuntimeError

    return ''.join(output)
