from werkzeug.exceptions import HTTPException
from flask import make_response
import json


class BusinessValidationError(HTTPException):
    def __init__(self, status_code, error_message):
        message = {
            "error_message": error_message,
            "status": status_code
        }
        # json.dumps() converts an object into a JSON string. make_response takes a string as the first argument
        self.response = make_response(json.dumps(message), status_code)
