import os

from flask import Flask
from flask_restful import Api
from application.base_apis import CardAPI, DeckAPI, ReviewAPI
from application.config import LocalDevelopmentConfig
from application.database import db
from flask_cors import CORS

from flask_jwt_extended import JWTManager
# from waitress import serve


if __name__ == "__main__":
    my_app = None
    api = None

    my_app = Flask(__name__)
    my_app.config.from_object(LocalDevelopmentConfig)
    jwt = JWTManager(my_app)
    db.init_app(my_app)
    api = Api(my_app)
    CORS(my_app)
    my_app.app_context().push()

    from application.specific_apis import *
    from application.base_apis import *
    api.add_resource(UserAPI, "/api/user/")
    api.add_resource(DeckAPI, "/api/deck/", "/api/deck/<string:deck_id>")
    api.add_resource(CardAPI, "/api/card/", "/api/card/<string:deck_id>")
    api.add_resource(ReviewAPI, "/api/review/<string:deck_id>")
    # port = int(os.environ.get('PORT', 33507))
    # serve(my_app, host="0.0.0.0", port=port)
    my_app.run(host='0.0.0.0')
