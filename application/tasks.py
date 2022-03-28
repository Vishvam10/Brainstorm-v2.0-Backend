from gzip import READ
from importlib.resources import contents
from nis import cat
from re import template
from application.helpers import create_pdf_report, format_message
from application.workers import celery
from application.models import Deck, Review, User, Card
from application.database import db

import datetime as dt
from flask import current_app as app
from flask import jsonify

from email import encoders, message
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from json import dumps
from httplib2 import Http

from flask import send_file


import smtplib
import pandas as pd
import numpy as np
import uuid
import os
import ast

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

# _ CELERY TASKS - For the App

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

@celery.task()
def send_performance_reports() :
    month = str(dt.datetime.now().strftime("%B"))
    users = db.session.query(User).all()
    for user in users :
        # For simplicity type = "pdf"
        user_id = user.__dict__["user_id"]
        user_name = user.__dict__["username"]
        user_email = user.__dict__["email_id"]
        upr = user.__dict__["user_preferences"]
        subject = "Performance Report for {}".format(month)
        decks = db.session.query(Deck).filter(Deck.user_id == user_id).all()
        deck_data = []
        qa_data = []
        easy_q = 0
        medium_q = 0
        hard_q = 0
        total_q = 0
        for deck in decks :
            deck_id = deck.__dict__["deck_id"]
            review = db.session.query(Review).filter(Review.deck_id == deck_id).first();            
            rev = review.__dict__
            easy_q += rev["easy_q"]
            medium_q += rev["medium_q"]
            hard_q += rev["hard_q"]
            total_q += rev["total_q"]
            ps = rev["past_scores"].split(",")
            past_scores = list(map(float, ps))
            past_scores_list = []
            for p in past_scores :
                past_scores_list.append(round(p,2))
            percentage_change = None
            all_time_average = None
            n = len(past_scores)
            if(n > 0) :
                all_time_average = round(sum(past_scores[1:]) / len(past_scores[1:]), 2)
                if(n > 3) :
                    percentage_change = round(100 * ((past_scores_list[-1] - past_scores_list[-2]) / past_scores_list[-2]), 20)
            

            d = {
                "deck_name" : deck.__dict__["deck_name"],
                "recent_score" : rev["score"],
                "percentage_change" : percentage_change,
                "past_scores" : ', '.join(str(x) for x in past_scores_list[-6:-1]),
                "all_time_average" : all_time_average
            }
            deck_data.append(d)
        qa_data = {
            "total_easy_q" : easy_q,
            "total_medium_q" : medium_q,
            "total_hard_q" : hard_q,
            "total_total_q" : total_q,
        }
        data = {
            "deck_data" : deck_data,
            "qa_data" : qa_data,
            "user_name" : user_name,
            "month" : month
        }
      
        print("DATA : ", data)
        
        # 1. Convert data to HTML
        template_file = "./email_templates/performance_report.html"
        HTML_output = format_message(template_file, data=data)
       
        if(upr is not None) :
            u_pref = ast.literal_eval(upr)
            report_format = u_pref["report_format"]
            if(report_format == "pdf") :
                # 2. Create PDF report
                ID = str(uuid.uuid4()).replace("-", "")
                file_name = "{}_{}_{}".format(user_name, month, ID)
                updated_filename = os.path.join(media, file_name)
                attachment_file = create_pdf_report(HTML_output, updated_filename)
                
                # 3. Send as an email attachment
                print("UPDATED FILENAME : ", updated_filename)
                message = "Your monthly performance report is here"
                send_email.delay(user_email, subject, message, content="text", attachment_file=attachment_file)
            else :
                message = HTML_output
                send_email.delay(user_email, subject, message, content="html", attachment_file=None)
        else :
            ID = str(uuid.uuid4()).replace("-", "")
            file_name = "{}_{}_{}".format(user_name, month, ID)
            updated_filename = os.path.join(media, file_name)
            attachment_file = create_pdf_report(HTML_output, updated_filename)
            
            print("UPDATED FILENAME : ", updated_filename)
            message = "Your monthly performance report is here"
            send_email.delay(user_email, subject, message, content="text", attachment_file=attachment_file)
    
    return True

@celery.task
def reminder_bot() :
    users = db.session.query(User).all()
    for user in users :
        user_id = user.__dict__["user_id"]
        user_name = user.__dict__["username"]
        webhook_url = user.__dict__["webhook_url"]

        if(webhook_url is None) :
            continue

        # Sample Webhook URL 
        # webhook_url = "https://chat.googleapis.com/v1/spaces/AAAARWvCKTU/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=tmfkrmHHaNuiWqrH1mG8f2panUvcODZtInv2b5MwHVM%3D"
	
        now = dt.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        message = "Hello World - {}".format(now)
        
        bot_message = {
            'text' : message
        }

        message_headers = {'Content-Type': 'application/json; charset=UTF-8'}

        http_obj = Http()

        http_obj.request(
            uri=webhook_url,
            method='POST',
            headers=message_headers,
            body=dumps(bot_message),
        )
        
    return True

@celery.task
def convert_and_send_file(file_type, deck_id) :
    f = "QA_Export_" + deck_id + "." + file_type
    fn = media + "/" + f
    print("FILE NAME : ", fn)

    # Create a file out of the deck
    cards = db.session.query(Card).filter(Card.deck_id == deck_id).all()
    
    data = []
    for card in cards :
        card_data = card.__dict__
        question = card_data["question"]
        answer = card_data["answer"]
        data.append({question, answer})

    df  = pd.DataFrame.from_records(data)
    df.columns = ["Question", "Answer"]
    if(file_type == "csv") :
        df.to_csv(fn, index=False)   
    else :
        df.to_excel(fn, index=False)   

    return fn

@celery.task()
def print_current_time_job():
    print("START")
    now = dt.datetime.now()
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

# _ CELERY TASKS - For the cleanup 
# TODO

# _ CELERY SCHEDULER 

@celery.on_after_finalize.connect
def print_time(sender, **kwargs):
    sender.add_periodic_task(crontab("*/2 * * * *"), print_current_time_job.s(), name='PRINT CURRENT TIME')

    # Monthly Report Generation
    sender.add_periodic_task(crontab("0 0 1 * *"), send_performance_reports.s(), name='SEND PERFORMANCE REPORT EMAILS')
    
    # Daily Reminder at 10:30 AM through Google Chat
    sender.add_periodic_task(crontab("30 10 * * *"), reminder_bot.s(), name='SEND REMINDER THROUGH GOOGLE CHAT')



#_ HELPER FUNCTIONS 

def qa_check(q, a, deck_id):
    cards = db.session.query(Card).filter(Card.deck_id == deck_id).all()
    for card in cards:
        if(q == card.question):
            return False
        if(a == card.answer):
            return False
    return True
