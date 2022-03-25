import uuid

from weasyprint import HTML
from flask import current_app as app
from jinja2 import Template

REPORTS = app.config["REPORTS_FOLDER"]

def format_message(template_file, data={}) :
    with open(template_file) as file :
        template = Template(file.read())
        return template.render(data=data)

def create_pdf_report(data) :
    # message = format_message("report.html", data)
    html = HTML(string=data)
    file_name = "user_reports/" + str(uuid.uuid4()) + ".pdf"
    
    HTML(string=html).write_pdf('out.pdf')
    return file_name
