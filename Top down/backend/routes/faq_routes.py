
# Import necessary libraries
from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError, DataError
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Flask Blueprint
faq_blueprint = Blueprint('faq_blueprint', __name__)

# Initialize SQLAlchemy
db = SQLAlchemy()

# Define the FAQ model
class FAQ(db.Model):
    """FAQ model"""
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"FAQ('{self.id}', '{self.question}', '{self.answer}')"

# Create the FAQ table
with db.app.app_context():
    db.create_all()

# Define a helper function to handle database transactions
def handle_db_transaction(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            db.session.commit()
            return result
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"IntegrityError: {e}")
            return jsonify({"error": "IntegrityError"}), 400
        except DataError as e:
            db.session.rollback()
            logger.error(f"DataError: {e}")
            return jsonify({"error": "DataError"}), 400
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error: {e}")
            return jsonify({"error": "Error"}), 500
    return wrapper

# Define the GET /api/faq endpoint
@faq_blueprint.route('/api/faq', methods=['GET'])
@jwt_required()
def get_faq():
    """
    Retrieve FAQ section for common inquiries.

    Returns:
        JSON array of FAQ objects, each containing 'id', 'question', and 'answer' properties.
    """
    try:
        faqs = FAQ.query.all()
        faq_list = []
        for faq in faqs:
            faq_dict = {
                "id": faq.id,
                "question": faq.question,
                "answer": faq.answer
            }
            faq_list.append(faq_dict)
        return jsonify(faq_list), 200
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": "Error"}), 500
