from email import encoders, message
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

import uuid

from weasyprint import HTML
# from flask import current_app as app
from jinja2 import Template

SMTP_SERVER_HOST = "localhost"
SMTP_SERVER_PORT = 1025
SENDER_ADDRESS = "s.vishvam@gmail.com"
SENDER_PASSWORD = ""
# SMTP_SERVER_HOST = app.config["SMTP_SERVER_HOST"]
# SMTP_SERVER_PORT = app.config["SMTP_SERVER_PORT"]
# SENDER_ADDRESS = app.config["SENDER_ADDRESS"]
# SENDER_PASSWORD = app.config["SENDER_PASSWORD"]

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

def format_message(template_file, data={}) :
    with open(template_file) as file :
        template = Template(file.read())
        return template.render(data=data)

def create_pdf_report(data) :
    # message = format_message("report.html", data)
    html = HTML(string=data)
    file_name = str(uuid.uuid4()) + ".pdf"
    
    HTML(string=html).write_pdf('out.pdf')
    return file_name

# to = "sagowa2690@kuruapp.com"
# s = "Sample"
# m = "<h1>asdfajsld;kfj sd; asdfjas ldjaskd asdf</h1>"
# t = "./../email_templates/welcome.html"
# a = "qa.csv"
