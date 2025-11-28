
# Models (if needed)
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
import logging

db = SQLAlchemy()

class RestaurantLocation(db.Model):
    """Restaurant location model."""
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    zip = db.Column(db.String(10), nullable=False)
    country = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"RestaurantLocation('{self.latitude}', '{self.longitude}', '{self.address}')"

# Routes
from flask import Blueprint, request, jsonify
from yourapplication import db
from yourapplication.models import RestaurantLocation
import jwt
from functools import wraps

# Create a logger
logger = logging.getLogger(__name__)

# Create a blueprint
restaurant_location_blueprint = Blueprint('restaurant_location_blueprint', __name__)

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(*args, **kwargs)
    return decorated

# Get restaurant location
@restaurant_location_blueprint.route('/api/restaurant-location', methods=['GET'])
@token_required
def get_restaurant_location():
    """
    Retrieve restaurant location to display on map.

    Returns:
        JSON object with restaurant location details.
    """
    try:
        # Query the database for the restaurant location
        restaurant_location = RestaurantLocation.query.first()
        if restaurant_location is None:
            return jsonify({'message': 'Restaurant location not found'}), 404
        # Return the restaurant location as a JSON object
        return jsonify({
            'latitude': restaurant_location.latitude,
            'longitude': restaurant_location.longitude,
            'address': restaurant_location.address,
            'city': restaurant_location.city,
            'state': restaurant_location.state,
            'zip': restaurant_location.zip,
            'country': restaurant_location.country
        }), 200
    except Exception as e:
        # Log the error and return a 500 error
        logger.error(f"Error getting restaurant location: {e}")
        return jsonify({'message': 'Internal server error'}), 500
