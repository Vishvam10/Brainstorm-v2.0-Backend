import json
from operator import and_
from urllib.parse import uses_relative
import uuid
from flask import jsonify, request
from flask_restful import Resource
from flask_restful import fields, marshal_with
from flask_restful import reqparse
from sqlalchemy import false, true
from application.database import db
from application.models import Deck, Review, User, Card
from application.validation import BusinessValidationError

# ~ HELPER FUNCTIONS


def qa_check(q, a, deck_id):
    cards = db.session.query(Card).filter(Deck.deck_id == deck_id).all()
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

# _ User API


class UserAPI(Resource):
    def post(self):
        ID = str(uuid.uuid4()).replace("-", "")
        data = request.json
        username = data["username"]
        password = data["password"]
        email = data["email"]
        phone = data["phone"]

        if username is None:
            raise BusinessValidationError(
                status_code=400, error_message="Username is required")
        if password is None:
            raise BusinessValidationError(
                status_code=400, error_message="Password is required")
        if email is None:
            raise BusinessValidationError(
                status_code=400, error_message="Email ID is required")
        if phone is None:
            raise BusinessValidationError(
                status_code=400, error_message="Phone Number is required")

        user = db.session.query(User).filter(User.username == username).first()
        if user:
            raise BusinessValidationError(
                status_code=400, error_message="Duplicate user")

        new_user = User(user_id=ID, username=username,
                        password=password, email_id=email, phone_no=phone)
        db.session.add(new_user)
        db.session.commit()

        return_value = {
            "message": "New User Created",
            "status": 200,
            "user_id": ID,
            "user_name": username,
        }

        return jsonify(return_value)

# _ Deck API


class DeckAPI(Resource):

    @marshal_with(deck_output_fields)
    def get(self):
        args = request.args
        user_id = args.get("user_id", None)
        users = db.session.query(User).filter(
            User.user_id == user_id
        ).first()
        print(users)
        if(users is None):
            raise BusinessValidationError(
                status_code=404, error_message="Invalid User ID")
        if user_id is None:
            raise BusinessValidationError(
                status_code=404, error_message="User ID is required")
        deck = db.session.query(Deck).filter(
            Deck.user_id == user_id).all()

        return deck

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
    def put(self, deck_id):
        if deck_id is None:
            raise BusinessValidationError(
                status_code=400, error_message="Deck ID is required")

        deck = db.session.query(Deck).filter(Deck.deck_id == deck_id).first()
        if(request.json):
            new_name = request.json["deck_name"]
            if(new_name is None or new_name == ""):
                raise BusinessValidationError(
                    status_code=400, error_message="New Deck Name is required")

            deck.deck_name = new_name
            db.session.add(deck)
            db.session.commit()
            return deck
        raise BusinessValidationError(
            status_code=400, error_message="KeyError : deck_name OR JSON body required")

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
    def get(self, deck_id):
        cards = db.session.query(Card).filter(Card.deck_id == deck_id).all()
        print(cards)
        return cards

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

        if questions is None:
            raise BusinessValidationError(
                status_code=400, error_message="Questions are required")
        if answers is None:
            raise BusinessValidationError(
                status_code=400, error_message="Answers are required")

        # print(questions, type(questions), len(questions))
        for i in range(0, len(questions)):
            ID = str(uuid.uuid4()).replace("-", "")
            if(qa_check(questions[i], answers[i], deck_id)):
                new_card = Card(
                    card_id=ID, question=questions[i], answer=answers[i], deck_id=deck_id)
                db.session.add(new_card)
                db.session.commit()
            else:
                continue

        return_value = {
            "message": "Cards Created",
            "status": 200,
            "deck_id": ID,
        }

        return jsonify(return_value)

    @marshal_with(card_output_fields)
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
    def get(self, deck_id):
        review = db.session.query(Review).filter(
            Review.deck_id == deck_id).first()
        return review

    def post(self, deck_id):
        data = request.json
        ID = deck_id + "review"
        total_q = data['total_q']
        easy_q = data['easy_q']
        medium_q = data['medium_q']
        hard_q = data['hard_q']
        score = data['score']
        last_reviewed = data['last_reviewed']
        past_scores = data['past_scores']

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

        new_review = Review(review_id=ID, deck_id=deck_id, total_q=total_q, easy_q=easy_q, medium_q=medium_q,
                            hard_q=hard_q, score=score, last_reviewed=last_reviewed, past_scores=past_scores)

        try:
            db.session.add(new_review)
            db.session.commit()
        except Exception as e:
            print(e)
            return_value = {
                "message": "Review already present. Use PUT method to update it.",
                "status": 200,
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
    def put(self, deck_id):
        data = request.json
        new_total_q = data['total_q']
        new_easy_q = data['easy_q']
        new_medium_q = data['medium_q']
        new_hard_q = data['hard_q']
        new_score = data['score']
        new_last_reviewed = data['last_reviewed']
        new_past_scores = data['past_scores']

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
        review.last_reviewed = new_last_reviewed
        review.past_scores = new_past_scores

        db.session.add(review)
        db.session.commit()
        return review

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
