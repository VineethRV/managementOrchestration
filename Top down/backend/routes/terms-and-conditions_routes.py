
from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from flask_jwt_extended import jwt_required
import logging

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask Blueprint and SQLAlchemy
terms_and_conditions_blueprint = Blueprint('terms_and_conditions_blueprint', __name__)
db = SQLAlchemy()

# SQLAlchemy model definition
class TermsAndConditions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'TermsAndConditions(id={self.id}, content={self.content})'

# Helper function to get terms and conditions
def get_terms_and_conditions():
    try:
        terms_and_conditions = TermsAndConditions.query.first()
        if terms_and_conditions:
            return terms_and_conditions.content
        else:
            return None
    except SQLAlchemyError as e:
        logger.error(f'Error getting terms and conditions: {e}')
        return None

# Flask route handler
@terms_and_conditions_blueprint.route('/api/terms-and-conditions', methods=['GET'])
@jwt_required()
def get_terms_and_conditions_endpoint():
    """
    Returns the terms and conditions page content.

    :return: JSON response with terms and conditions content
    """
    try:
        terms_and_conditions = get_terms_and_conditions()
        if terms_and_conditions:
            return jsonify({'terms_and_conditions': terms_and_conditions}), 200
        else:
            return jsonify({'error': 'Terms and conditions not found'}), 404
    except Exception as e:
        logger.error(f'Error getting terms and conditions: {e}')
        return jsonify({'error': 'Internal server error'}), 500
