from crypt import methods
from application.validation import BusinessValidationError
from application.models import Deck, Review, User, Card
from application.database import db
from operator import and_
from sqlalchemy import false, true
from flask_jwt_extended import jwt_required
from flask_restful import fields, marshal_with
from flask_restful import Resource
from flask import jsonify, request

from flask import current_app as app

from app import cache

import uuid

import bcrypt
import datetime as dt


# ~ HELPER FUNCTIONS


def qa_check(q, a, deck_id):
    cards = db.session.query(Card).filter(Card.deck_id == deck_id).all()
    for card in cards:
        if(q == card.question):
            return False
        if(a == card.answer):
            return False
    return True


# ~ FOR MARSHAL-WITH OUTPUT

card_output_fields = {
    "deck_id": fields.String,
    "card_id": fields.String,
    "question": fields.String,
    "answer": fields.String
}

review_output_fields = {
    "total_q": fields.Integer,
    "easy_q": fields.Integer,
    "medium_q": fields.Integer,
    "hard_q": fields.Integer,
    "score": fields.Float,
    "last_reviewed": fields.String,
    "past_scores": fields.String
}

deck_output_fields = {
    "deck_id": fields.String,
    "deck_name": fields.String,
}

user_output_fields = {
    "user_id": fields.String,
    "username": fields.String,
    "email_id": fields.String,
    "phone_no": fields.String,
    "webhook_url": fields.String,
    "app_preferences": fields.String,
}

# _ User API


class UserAPI(Resource):
    @marshal_with(user_output_fields)
    def get(self, user_id) :
        user = db.session.query(User).filter(User.user_id == user_id).first()
        return user

    def post(self):
        ID = str(uuid.uuid4()).replace("-", "")
        data = request.json
        username = data["username"]
        password = data["password"]
        email = data["email"]
        phone = data["phone"]
        webhook_url = ""
        app_preferences = ""

        if username is None or username == "":
            raise BusinessValidationError(
                status_code=400, error_message="Username is required")
        if password is None or password == "":
            raise BusinessValidationError(
                status_code=400, error_message="Password is required")
        if email is None or email == "":
            raise BusinessValidationError(
                status_code=400, error_message="Email ID is required")
        if phone is None or email == "":
            raise BusinessValidationError(
                status_code=400, error_message="Phone Number is required")

        hashed_password = bcrypt.hashpw(
            password.encode('utf8'), bcrypt.gensalt())

        user = db.session.query(User).filter(User.username == username).first()
        if user:
            raise BusinessValidationError(
                status_code=400, error_message="Duplicate user")

        new_user = User(user_id=ID, username=username,
                        password=hashed_password, email_id=email, phone_no=phone, webhook_url=webhook_url, app_preferences=app_preferences)
        db.session.add(new_user)
        db.session.commit()

        return_value = {
            "message": "New User Created",
            "status": 200,
            "user_id": ID,
            "user_name": username,
        }

        return jsonify(return_value)

    @marshal_with(user_output_fields)
    def put(self, user_id) :
        data = request.json
        username = data["user_name"]
        email_id = data["email_id"]
        phone_no = data["phone_no"]
    

        if(not user_id or not username or not email_id or not phone_no) :
            raise BusinessValidationError(status_code=400, error_message="One or more fields are missing")

        user = db.session.query(User).filter(User.user_id == user_id).first()
        
        if(user is None):
            raise BusinessValidationError(status_code=400, error_message="Invalid user ID or no such user exists")

        user_list = db.session.query(User).all()
        
        for u in user_list :
            ud = u.__dict__
            print("********** USER **********", ud)
            if(user.username != username and ud["username"] == username) :
                raise BusinessValidationError(status_code=400, error_message="Username already exists")
            if(user.email_id != email_id and ud["email_id"] == email_id) :
                raise BusinessValidationError(status_code=400, error_message="Email ID already exists")
            if(user.phone_no != phone_no and ud["phone_no"] == phone_no) :
                raise BusinessValidationError(status_code=400, error_message="Phone no already exists")


        user.username = username
        user.email_id = email_id
        user.phone_no = phone_no

        db.session.add(user)
        db.session.commit()
        return user

    def delete(self, user_id) :
        decks = db.session.query(Deck).filter(Deck.user_id == user_id).all()
        for deck in decks :
            deck_id = deck.__dict__["deck_id"]
            
            # 1. Delete the cards
            db.session.query(Card).where(Card.deck_id == deck_id).delete(synchronize_session=False)
            db.session.commit()
            
            # 2. Delete the reviews
            db.session.query(Review).where(Review.deck_id == deck_id).delete(synchronize_session=False)
            db.session.commit()

            # 3. Delete the decks
            db.session.query(Deck).filter(Deck.deck_id == deck_id).delete(synchronize_session=False)
            db.session.commit()
        
        # 4. Delete the user
        db.session.query(User).filter(User.user_id == user_id).delete(synchronize_session=False)
        db.session.commit()

        return_value = {
            "user_id": user_id,
            "message": "User deleted",
            "status": 200,
        }

        return jsonify(return_value)


@app.route('/api/user/all', methods=["GET"])
def get_all_users() :
    users = db.session.query(User).all()
    data = []
    for u in users : 
        data.append((u.__dict__["username"], u.__dict__["user_id"]))
    return_value = {
        "data" : data
    }
    return jsonify(return_value)

@app.route('/api/user/update_user_preferences/<string:user_id>', methods=["GET","PUT"])
def user_preferences(user_id) :
    if(request.method == "GET") :
        user = db.session.query(User).filter(User.user_id == user_id).first()    
        if(user is None):
            raise BusinessValidationError(status_code=400, error_message="Invalid user ID or no such user exists")
        
        data = {
            "webhook_url" : user.webhook_url,
            "user_preferences" : user.user_preferences
        }
        return jsonify(data)

    if(request.method == "PUT") :
        data = request.json
        webhook_url = data["webhook_url"]
        user_preferences = data["user_preferences"]
        
        user = db.session.query(User).filter(User.user_id == user_id).first()
            
        if(user is None):
            raise BusinessValidationError(status_code=400, error_message="Invalid user ID or no such user exists")

        user.webhook_url = webhook_url
        user.user_preferences = user_preferences
        

        db.session.add(user)
        db.session.commit()

        return_value = {
            "message" : "Updated user preferences"
        }

        return jsonify(return_value)





@app.route('/api/password_reset/<string:user_id>', methods=["POST"])
def reset_password(user_id) :
    data = request.json
    current_password = data["current_password"]
    new_password = data["new_password"]
    
    print("***************** OLD PASSWORD *****************", current_password)
    if current_password is None or current_password == "":
        raise BusinessValidationError(
            status_code=400, error_message="Current Password is required")
    if new_password is None or new_password == "":
        raise BusinessValidationError(
            status_code=400, error_message="New Password is required")
    
    user = db.session.query(User).filter(User.user_id == user_id).first()

    hashed_password = user.password
    string_password = hashed_password.decode('utf8')
    print("***************** OLD HASHED PASSWORD *****************", string_password)
    if(not bcrypt.checkpw(current_password.encode('utf8'), string_password.encode('utf8'))):
        raise BusinessValidationError(
            status_code=400, error_message="Incorrect Password")
    
    new_hashed_password = bcrypt.hashpw(new_password.encode('utf8'), bcrypt.gensalt())
    user.password = new_hashed_password
    print("***************** NEW PASSWORD *****************", new_hashed_password)
    db.session.add(user)
    db.session.commit()

    return_value = {
        "message": "Password Changed Successfully",
        "status": 200,
        "new_password" : new_password
    }

    return jsonify(return_value)




# _ Deck API


class DeckAPI(Resource):

    @marshal_with(deck_output_fields)
    @jwt_required()
    @cache.memoize(50)
    def get(self):
        args = request.args
        user_id = args.get("user_id", None)
        users = db.session.query(User).filter(
            User.user_id == user_id
        ).first()
        if(users is None):
            raise BusinessValidationError(
                status_code=404, error_message="Invalid User ID")
        if user_id is None:
            raise BusinessValidationError(
                status_code=404, error_message="User ID is required")
        deck = db.session.query(Deck).filter(
            Deck.user_id == user_id).all()

        return deck

    @jwt_required()
    def post(self):
        data = request.json
        ID = str(uuid.uuid4()).replace("-", "")
        deck_name = data["deck_name"]
        user_id = data["user_id"]

        if deck_name is None:
            raise BusinessValidationError(
                status_code=400, error_message="Deck name is required")
        if user_id is None:
            raise BusinessValidationError(
                status_code=400, error_message="User id is required")

        deck = db.session.query(Deck).filter(
            and_(Deck.user_id == user_id, Deck.deck_name == deck_name)).first()
        if(deck):
            print(deck.deck_name)
            if(deck.deck_name == deck_name):
                print(deck.deck_name)
                raise BusinessValidationError(
                    status_code=400, error_message="Duplicate Deck Name")

        new_deck = Deck(deck_id=ID, deck_name=deck_name, user_id=user_id)
        db.session.add(new_deck)
        db.session.commit()

        return_value = {
            "message": "New Deck Created",
            "status": 200,
            "deck_id": ID,
            "deck_name": deck_name,
        }

        return jsonify(return_value)

    @marshal_with(deck_output_fields)
    @jwt_required()
    def put(self, deck_id):
        data = request.json
        if deck_id is None:
            raise BusinessValidationError(
                status_code=400, error_message="Deck ID is required")

        if(data):
            user_id = data["user_id"]
            new_name = request.json["deck_name"]
            decks = db.session.query(Deck).filter(Deck.user_id == user_id).all()
            for deck in decks :
                if(deck.deck_name == new_name) :
                    raise BusinessValidationError(
                        status_code=400, error_message="Deck name already exists")

            deck.deck_name = new_name
            db.session.add(deck)
            db.session.commit()
            return deck
            
        raise BusinessValidationError(
            status_code=400, error_message="KeyError : Deck name or JSON body required")

    @jwt_required()
    def delete(self, deck_id):
        deck = db.session.query(Deck).filter(Deck.deck_id == deck_id).first()
        print(deck)
        if(deck is None):
            raise BusinessValidationError(
                status_code=404, error_message="Invalid Deck ID")

        db.session.query(Card).where(Card.deck_id == deck_id).delete(
            synchronize_session=False)
        db.session.query(Deck).filter(
            Deck.deck_id == deck_id).delete(synchronize_session=False)

        db.session.commit()

        return_value = {
            "deck_id": deck_id,
            "message": "Deck and its cards deleted",
            "status": 200,
        }

        return jsonify(return_value)


# _ Card API


class CardAPI(Resource):

    @marshal_with(card_output_fields)
    @jwt_required()
    @cache.memoize(50)
    def get(self, deck_id):
        cards = db.session.query(Card).filter(Card.deck_id == deck_id).all()
        print(cards)
        return cards

    @jwt_required()
    def post(self, deck_id):
        if deck_id is None:
            raise BusinessValidationError(
                status_code=400, error_message="Deck ID is required")

        deck = db.session.query(Deck).filter(Deck.deck_id == deck_id).first()

        if(deck is None):
            raise BusinessValidationError(
                status_code=400, error_message="Invalid Deck ID")

        data = request.json
        questions = data['questions']
        answers = data['answers']
        extra_message = ""
        if questions is None:
            raise BusinessValidationError(
                status_code=400, error_message="Questions are required")
        if answers is None:
            raise BusinessValidationError(
                status_code=400, error_message="Answers are required")

        print(questions, type(questions), len(questions))
        for i in range(0, len(questions)):
            ID = str(uuid.uuid4()).replace("-", "")
            if(qa_check(questions[i], answers[i], deck_id)):
                new_card = Card(
                    card_id=ID, question=questions[i], answer=answers[i], deck_id=deck_id)
                db.session.add(new_card)
                db.session.commit()
            else:
                extra_message = "Duplicates found and ignore. "
                continue
                
        message = extra_message + " Cards created successfully"
        return_value = {
            "message": message,
            "status": 200,
            "deck_id": ID,
        }

        return jsonify(return_value)

    @marshal_with(card_output_fields)
    @jwt_required()
    def put(self):
        args = request.args
        data = request.json
        card_id = args.get('card_id', None)
        new_question = data.get('question', None)
        new_answer = data.get('answer', None)

        card = db.session.query(Card).filter(Card.card_id == card_id).first()

        if(card is None):
            raise BusinessValidationError(
                status_code=400, error_message="Invalid Card ID")

        card.question = new_question
        card.answer = new_answer
        db.session.add(card)
        db.session.commit()
        return card

    @jwt_required()
    def delete(self):
        card_id = request.args.get("card_id", None)
        card = db.session.query(Card).filter(Card.card_id == card_id).first()
        print(card)
        if(card is None):
            raise BusinessValidationError(
                status_code=404, error_message="Invalid Card ID")
        try:
            db.session.query(Card).filter(
                Card.card_id == card_id).delete(synchronize_session=False)
            db.session.commit()

            return_value = {
                "deck_id": card_id,
                "message": "Card deleted successfully",
                "status": 200,
            }
            return jsonify(return_value)
        except:
            return_value = {
                "deck_id": card_id,
                "message": "No such card exists",
                "status": 400,
            }
            return jsonify(return_value)


# _ Review API

class ReviewAPI(Resource):

    @marshal_with(review_output_fields)
    @jwt_required()
    @cache.memoize(50)
    def get(self, deck_id):
        review = db.session.query(Review).filter(
            Review.deck_id == deck_id).first()
        if(deck_id is None):
            raise BusinessValidationError(
                status_code=400, error_message="Deck ID is required")
        if(review is None):
            raise BusinessValidationError(
                status_code=200, error_message="No review exists for now")
            
        return review

    @jwt_required()
    def post(self, deck_id):
        data = request.json
        ID = deck_id + "review"
        total_q = data['total_q']
        easy_q = data['easy_q']
        medium_q = data['medium_q']
        hard_q = data['hard_q']
        score = data['score']
        now = dt.datetime.now().strftime("%b-%m-%Y %H:%M %p")
        last_reviewed = now
        past_scores = "{}".format(score)

        if total_q is None:
            raise BusinessValidationError(
                status_code=400, error_message="Total questions are required")
        if easy_q is None:
            raise BusinessValidationError(
                status_code=400, error_message="Number of easy questions are required")
        if medium_q is None:
            raise BusinessValidationError(
                status_code=400, error_message="Number of medium questions are required")
        if hard_q is None:
            raise BusinessValidationError(
                status_code=400, error_message="Number of hard questions are required")
        if score is None:
            raise BusinessValidationError(
                status_code=400, error_message="Score is required")
        if last_reviewed is None:
            raise BusinessValidationError(
                status_code=400, error_message="Last reviewed is required")
        if past_scores is None:
            raise BusinessValidationError(
                status_code=400, error_message="Past scores are required")
        # review = db.session.query(Review).filter(Review.deck_id == deck_id).first()
        new_review = Review(review_id=ID, deck_id=deck_id, total_q=total_q, easy_q=easy_q, medium_q=medium_q,
                            hard_q=hard_q, score=score, last_reviewed=last_reviewed, past_scores=past_scores)
        # if(review.review_id == ID) :
        #     raise BusinessValidationError(
        #         status_code=409, error_message="Review already present. Use PUT method to update it.")
        
        try:
            db.session.add(new_review)
            db.session.commit()
        except Exception as e:
            print(e)
            return_value = {
                "message": "Review already present. Use PUT method to update it.",
                "status": 409,
                "review_id": ID,
                "deck_id": deck_id,
            }
            return jsonify(return_value)
            

        return_value = {
            "message": "Review Created",
            "status": 200,
            "review_id": ID,
            "deck_id": deck_id,
        }
        return jsonify(return_value)

    @marshal_with(review_output_fields)
    @jwt_required()
    def put(self, deck_id):
        data = request.json
        new_total_q = data['total_q']
        new_easy_q = data['easy_q']
        new_medium_q = data['medium_q']
        new_hard_q = data['hard_q']
        new_score = data['score']
        now = dt.datetime.now().strftime("%b-%m-%Y %H:%M %p")
        review = db.session.query(Review).filter(
            Review.deck_id == deck_id).first()
        if(review is None):
            raise BusinessValidationError(
                status_code=400, error_message="Invalid Deck ID")
        review.total_q = new_total_q
        review.easy_q = new_easy_q
        review.medium_q = new_medium_q
        review.hard_q = new_hard_q
        review.score = new_score
        review.last_reviewed = now
        review.past_scores = review.past_scores + "," + str(new_score)
        db.session.add(review)
        db.session.commit()
        return review

    @jwt_required()
    def delete(self, deck_id):
        try:
            db.session.query(Review).filter(Review.deck_id ==
                                            deck_id).delete(synchronize_session=False)
            db.session.commit()
        except Exception as e:
            return_value = {
                "message": "No such review",
                "status": 200,
                "deck_id": deck_id,
            }
            return jsonify(return_value)
        return_value = {
            "message": "Review deleted successfully",
            "status": 200,
            "deck_id": deck_id,
        }
        return jsonify(return_value)
