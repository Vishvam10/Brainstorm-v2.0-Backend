from flask import Flask
from flask import current_app as app
from flask_celery import make_celery
import redis

from application.models import Deck, Review, User, Card
from application.database import db

import pandas as pd
import numpy as np
import uuid

uploads = app.config["UPLOAD_FOLDER"]
celery = make_celery(app)


@celery.task
def parse_file(file, file_type, deck_id) :
    if(file_type == "csv") :
        file_path = "{}\{}".format(uploads, file)
        print("***********REACHED***********", file_path, file_type)
        df = pd.read_csv(file_path, on_bad_lines='skip')

    elif(file_type == "xlsx" or file_type == "xls") :
        df = pd.read_excel(file)
    
    questions = df["questions"].tolist()
    answers = df["answers"].tolist()

    for i in range(0, len(questions)):
        ID = str(uuid.uuid4()).replace("-", "")
        if(qa_check(questions[i], answers[i], deck_id)):
            new_card = Card(
                card_id=ID, question=questions[i], answer=answers[i], deck_id=deck_id)
            db.session.add(new_card)
            db.session.commit()
        else:
            continue
    return


def qa_check(q, a, deck_id):
    cards = db.session.query(Card).filter(Deck.deck_id == deck_id).all()
    for card in cards:
        if(q == card.question):
            return False
        if(a == card.answer):
            return False
    return True