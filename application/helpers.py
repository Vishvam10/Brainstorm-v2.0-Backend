import uuid

from weasyprint import HTML
from flask import current_app as app
from jinja2 import Template

def format_message(template_file, data={}) :
    with open(template_file) as file :
        template = Template(file.read())
        return template.render(data=data)

def create_pdf_report(data, name) :
    html = HTML(string=data)
    file_name = name + ".pdf"
    html.write_pdf(target=file_name)
    return file_name
