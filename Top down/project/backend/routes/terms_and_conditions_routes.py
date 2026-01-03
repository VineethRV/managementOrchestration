
# Models (if needed)
from flask_sqlalchemy import SQLAlchemy
from flask import current_app

db = SQLAlchemy()

class TermsAndConditions(db.Model):
    """Terms and Conditions model"""
    id = db.Column(db.Integer, primary_key=True)
    terms_and_conditions = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"TermsAndConditions('{self.terms_and_conditions}')"

# Routes
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import logging

terms_and_conditions_blueprint = Blueprint('terms_and_conditions', __name__)

@terms_and_conditions_blueprint.route('/api/terms-and-conditions', methods=['GET'])
def get_terms_and_conditions():
    """
    Retrieves terms and conditions for registration.

    Returns:
        A JSON response containing the terms and conditions.
    """
    try:
        terms_and_conditions = TermsAndConditions.query.first()
        if terms_and_conditions is None:
            return jsonify({"error": "Terms and conditions not found"}), 404
        return jsonify({"terms_and_conditions": terms_and_conditions.terms_and_conditions}), 200
    except Exception as e:
        logging.error(f"Error retrieving terms and conditions: {e}")
        return jsonify({"error": "Internal server error"}), 500

# Helper functions if needed
def get_terms_and_conditions_from_db():
    """
    Retrieves terms and conditions from the database.

    Returns:
        The terms and conditions as a string.
    """
    try:
        terms_and_conditions = TermsAndConditions.query.first()
        if terms_and_conditions is None:
            return None
        return terms_and_conditions.terms_and_conditions
    except Exception as e:
        logging.error(f"Error retrieving terms and conditions from db: {e}")
        return None
