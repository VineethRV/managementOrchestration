
from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, Text, ARRAY
from sqlalchemy.exc import SQLAlchemyError
import logging
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask Blueprint and SQLAlchemy
delivery_blueprint = Blueprint('delivery_blueprint', __name__)
db = SQLAlchemy()

# SQLAlchemy model definition
class DeliveryOption(db.Model):
    """Delivery Option model"""
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Float, nullable=False)
    estimated_delivery_time = Column(String(100), nullable=False)
    available_areas = Column(ARRAY(String(100)), nullable=False)

    def __repr__(self):
        return f"DeliveryOption('{self.name}', '{self.description}', {self.price}, '{self.estimated_delivery_time}', {self.available_areas})"

# Helper function for error handling
def handle_error(e):
    """Handle SQLAlchemy errors"""
    logger.error(e)
    return jsonify({"error": "Internal Server Error"}), 500

# Route handler for Get Delivery Options
@delivery_blueprint.route('/api/delivery-options', methods=['GET'])
@jwt_required()
def get_delivery_options():
    """
    Retrieve a list of available delivery options

    Returns:
        list: List of delivery options
    """
    try:
        # Query database for delivery options
        delivery_options = DeliveryOption.query.all()
        
        # Serialize delivery options to JSON
        data = [{"id": option.id, "name": option.name, "description": option.description, 
                 "price": option.price, "estimated_delivery_time": option.estimated_delivery_time, 
                 "available_areas": option.available_areas} for option in delivery_options]
        
        # Return JSON response
        return jsonify(data), 200
    
    except SQLAlchemyError as e:
        # Handle SQLAlchemy errors
        return handle_error(e)
