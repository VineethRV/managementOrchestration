
from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask Blueprint and SQLAlchemy
cake_designs_blueprint = Blueprint('cake_designs', __name__)
db = SQLAlchemy()

# SQLAlchemy model definition
class CakeDesign(db.Model):
    """Cake design model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)

    def to_dict(self):
        """Convert cake design to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'imageUrl': self.image_url,
            'price': self.price
        }

# Routes
@cake_designs_blueprint.route('/api/cake-designs', methods=['GET'])
@jwt_required()
def get_cake_designs():
    """
    Retrieve a list of available cake designs

    Returns:
        A JSON array of cake design objects
    """
    try:
        # Query cake designs from database
        cake_designs = CakeDesign.query.all()
        
        # Convert cake designs to dictionaries
        cake_designs_dict = [cake_design.to_dict() for cake_design in cake_designs]
        
        # Return JSON response
        return jsonify(cake_designs_dict), 200
    
    except SQLAlchemyError as e:
        # Log error and return 500 status code
        logger.error(f"Error retrieving cake designs: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

# Helper function to handle database transactions
def handle_database_transaction(func):
    def wrapper(*args, **kwargs):
        try:
            # Start database transaction
            db.session.begin()
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Commit database transaction
            db.session.commit()
            
            # Return result
            return result
        
        except IntegrityError as e:
            # Log error and rollback database transaction
            logger.error(f"Integrity error: {e}")
            db.session.rollback()
            return jsonify({"error": "Integrity Error"}), 400
        
        except SQLAlchemyError as e:
            # Log error and rollback database transaction
            logger.error(f"Database error: {e}")
            db.session.rollback()
            return jsonify({"error": "Database Error"}), 500
    
    return wrapper
