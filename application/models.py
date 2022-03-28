from .database import db


class User(db.Model):
    __tablename__ = "user"
    user_id = db.Column(db.String, unique=True, nullable=False, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, unique=True, nullable=False)
    email_id = db.Column(db.String, unique=True, nullable=False)
    phone_no = db.Column(db.String, unique=True, nullable=False)
    webhook_url = db.Column(db.String, unique=True, nullable=True)
    app_preferences = db.Column(db.String, nullable=False)
    user_preferences = db.Column(db.String, nullable=False)

    def to_dict(self):
        return dict(id=self.user_id, username=self.username, password=self.password, email_id=self.email_id, phone_no=self.phone_no, webhook_url=self.webhook_url, app_preferences=self.app_preferences, user_preferences=self.user_preferences)


class Deck(db.Model):
    __tablename__ = "deck"
    deck_id = db.Column(db.String, unique=True,
                        primary_key=True, nullable=False)
    deck_name = db.Column(db.String, nullable=False)
    user_id = db.Column(db.String, db.ForeignKey(
        "user.user_id"), nullable=False)

    def to_dict(self):
        return dict(id=self.deck_id, deck_name=self.deck_name, user_id=self.user_id)


class Card(db.Model):
    __tablename__ = "card"
    card_id = db.Column(db.String, primary_key=True,
                        unique=True, nullable=False)
    question = db.Column(db.String, nullable=False)
    answer = db.Column(db.String, nullable=False)
    deck_id = db.Column(db.String, db.ForeignKey(
        "deck.deck_id"), nullable=False)


class Review(db.Model):
    __tablename__ = "review"
    review_id = db.Column(db.String, primary_key=True,
                          unique=True, nullable=False)
    deck_id = db.Column(db.String, db.ForeignKey(
        "deck.deck_id"), nullable=False)
    total_q = db.Column(db.Integer, nullable=False)
    easy_q = db.Column(db.Integer, nullable=False)
    medium_q = db.Column(db.Integer, nullable=False)
    hard_q = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Float, nullable=False)
    last_reviewed = db.Column(db.String, nullable=False)
    past_scores = db.Column(db.String, nullable=False)
