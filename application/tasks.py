from application.workers import celery
from datetime import datetime
from flask import current_app as app

from celery.schedules import crontab
print("crontab ", crontab)


@celery.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10.0, print_current_time_job.s(), name='add every 10')


@celery.task()
def calculate_aggregate_likes(article_id):
    # You can get all the likes for the `article_id`
    # Calculate the aggregate and store in the DB
    print("#####################################")
    print("Received {}".format(article_id))
    print("#####################################")
    return True

@celery.task()
def just_say_hello(name):
    print("INSIDE TASK")
    print("Hello {}".format(name))


@celery.task()
def print_current_time_job():
    print("START")
    now = datetime.now()
    print("now =", now)
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("date and time =", dt_string) 
    print("COMPLETE")

# from flask import Flask
# from flask import current_app as app
# import redis

# from application.models import Deck, Review, User, Card
# from application.database import db

# from celery import Celery

# import pandas as pd
# import numpy as np
# import uuid

# uploads = app.config["UPLOAD_FOLDER"]




# def parse_file(file, file_type, deck_id):
#     if(file_type == "csv"):
#         file_path = "{}\{}".format(uploads, file)
#         print("***********REACHED***********", file_path, file_type)
#         df = pd.read_csv(file_path, on_bad_lines='skip')

#     elif(file_type == "xlsx" or file_type == "xls"):
#         df = pd.read_excel(file)

#     questions = df["questions"].tolist()
#     answers = df["answers"].tolist()

#     for i in range(0, len(questions)):
#         ID = str(uuid.uuid4()).replace("-", "")
#         if(qa_check(questions[i], answers[i], deck_id)):
#             new_card = Card(
#                 card_id=ID, question=questions[i], answer=answers[i], deck_id=deck_id)
#             db.session.add(new_card)
#             db.session.commit()
#         else:
#             continue
#     return


# def qa_check(q, a, deck_id):

#     cards = db.session.query(Card).filter(Deck.deck_id == deck_id).all()
#     for card in cards:
#         if(q == card.question):
#             return False
#         if(a == card.answer):
#             return False
#     return True


@celery.task(name="f1")
def f1():
    return "***************** IN F1 *****************"


@app.route("/ftask")
def sample_task():
    f1.delay()
    return "async"
