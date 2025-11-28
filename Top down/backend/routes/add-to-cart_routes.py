
# Import necessary libraries
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

# Initialize Flask app and database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cakes.db'
db = SQLAlchemy(app)

# Define models
class Cake(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

class Flavor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Design(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cake_id = db.Column(db.Integer, db.ForeignKey('cake.id'), nullable=False)
    flavor_id = db.Column(db.Integer, db.ForeignKey('flavor.id'), nullable=False)
    design_id = db.Column(db.Integer, db.ForeignKey('design.id'), nullable=False)
    message = db.Column(db.String(200), nullable=False)
    pickup_or_delivery = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Define helper function to calculate total cost
def calculate_total_cost(cake_price, quantity):
    return cake_price * quantity

# Define route handler for adding to cart
@app.route('/api/add-to-cart', methods=['POST'])
@jwt_required
def add_to_cart():
    """
    Add the customized cake to the user's cart.

    Request Body:
    - cake_id (integer): The ID of the cake to be added to cart.
    - flavor_id (integer): The ID of the flavor chosen for the cake.
    - design_id (integer): The ID of the design chosen for the cake.
    - message (string): The message to be written on the cake.
    - pickup_or_delivery (string): Either 'pickup' or 'delivery'.
    - quantity (integer): The number of cakes to be ordered.

    Response:
    - cart_id (integer): The ID of the cart.
    - cake_id (integer): The ID of the cake added to cart.
    - flavor_id (integer): The ID of the flavor chosen for the cake.
    - design_id (integer): The ID of the design chosen for the cake.
    - message (string): The message to be written on the cake.
    - pickup_or_delivery (string): Either 'pickup' or 'delivery'.
    - quantity (integer): The number of cakes ordered.
    - total_cost (float): The total cost of the cake.
    - status (string): Either 'success' or 'failure'.
    """
    try:
        # Get user ID from JWT token
        user_id = get_jwt_identity()

        # Get request body
        data = request.json

        # Validate request body
        if not data:
            return jsonify({'status': 'failure', 'message': 'Missing request body'}), 400

        # Check for missing data
        required_fields = ['cake_id', 'flavor_id', 'design_id', 'message', 'pickup_or_delivery', 'quantity']
        if not all(field in data for field in required_fields):
            return jsonify({'status': 'failure', 'message': 'Missing required fields'}), 400

        # Get cake, flavor, and design IDs
        cake_id = data['cake_id']
        flavor_id = data['flavor_id']
        design_id = data['design_id']

        # Check if cake, flavor, and design exist
        cake = Cake.query.get(cake_id)
        flavor = Flavor.query.get(flavor_id)
        design = Design.query.get(design_id)
        if not cake or not flavor or not design:
            return jsonify({'status': 'failure', 'message': 'Invalid cake, flavor, or design ID'}), 400

        # Calculate total cost
        total_cost = calculate_total_cost(cake.price, data['quantity'])

        # Create new cart entry
        cart = Cart(
            user_id=user_id,
            cake_id=cake_id,
            flavor_id=flavor_id,
            design_id=design_id,
            message=data['message'],
            pickup_or_delivery=data['pickup_or_delivery'],
            quantity=data['quantity'],
            total_cost=total_cost
        )

        # Add cart entry to database
        db.session.add(cart)
        db.session.commit()

        # Return success response
        return jsonify({
            'cart_id': cart.id,
            'cake_id': cake_id,
            'flavor_id': flavor_id,
            'design_id': design_id,
            'message': data['message'],
            'pickup_or_delivery': data['pickup_or_delivery'],
            'quantity': data['quantity'],
            'total_cost': total_cost,
            'status': 'success'
        }), 201

    except Exception as e:
        # Log error and return failure response
        logging.error(e)
        db.session.rollback()
        return jsonify({'status': 'failure', 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)
