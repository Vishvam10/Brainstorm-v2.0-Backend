from application.workers import celery
from application.models import Deck, Review, User, Card
from application.database import db

from datetime import datetime
from flask import current_app as app

from email import encoders, message
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import smtplib
import pandas as pd
import numpy as np
import uuid

from celery.schedules import crontab
print("crontab ", crontab)

SMTP_SERVER_HOST = "localhost"
SMTP_SERVER_PORT = 1025
SENDER_ADDRESS = "s.vishvam@gmail.com"
SENDER_PASSWORD = ""

# SMTP_SERVER_HOST = app.config["SMTP_SERVER_HOST"]
# SMTP_SERVER_PORT = app.config["SMTP_SERVER_PORT"]
# SENDER_ADDRESS = app.config["SENDER_ADDRESS"]
# SENDER_PASSWORD = app.config["SENDER_PASSWORD"]

media = app.config["MEDIA_FOLDER"]


@celery.task()
def send_email(to_address, subject, message, content="text", attachment_file=None) :
    msg = MIMEMultipart()
    msg["From"] = SENDER_ADDRESS
    msg["To"] = to_address
    msg["Subject"] = subject

    if content == "html" :
        msg.attach(MIMEText(message, "html"))
    else :
        msg.attach(MIMEText(message, "plain"))

    if attachment_file :
        with open(attachment_file, 'rb') as attachment :
            part = MIMEBase("application", "octect-stream") 
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition", f"attachment; filename = {attachment_file}",
        )

        msg.attach(part)

    s = smtplib.SMTP(host=SMTP_SERVER_HOST, port=SMTP_SERVER_PORT)
    s.login(SENDER_ADDRESS, SENDER_PASSWORD)
    s.send_message(msg)
    s.quit()
    return True

@celery.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10.0, print_current_time_job.s(), name='add every 10')

    

@celery.task()
def print_current_time_job():
    print("START")
    now = datetime.now()
    print("now =", now)
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("date and time =", dt_string) 
    print("COMPLETE")

@celery.task
def parse_file(file, file_type, deck_id):
    if(file_type == "csv"):
        file_path = "{}/{}".format(media, file)
        df = pd.read_csv(file_path, on_bad_lines='skip')
        print(df)
    elif(file_type == "xlsx" or file_type == "xls"):
        df = pd.read_excel(file)

    questions = df["questions"].tolist()
    answers = df["answers"].tolist()

    for i in range(0, len(questions)):
        ID = str(uuid.uuid4()).replace("-", "")
        if(qa_check(questions[i], answers[i], deck_id)):
            new_card = Card(card_id=ID, question=questions[i], answer=answers[i], deck_id=deck_id)
            db.session.add(new_card)
            db.session.commit()
            
        else:
            continue
    print("CARDS CREATED FROM FILE")
    return True


def qa_check(q, a, deck_id):
    cards = db.session.query(Card).filter(Card.deck_id == deck_id).all()
    for card in cards:
        if(q == card.question):
            return False
        if(a == card.answer):
            return False
    return True