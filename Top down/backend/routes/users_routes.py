
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cake_orders.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret'

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
logger.addHandler(handler)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(64), nullable=True)
    orders = db.relationship('Order', backref='user', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(64), nullable=False)
    order_details = db.relationship('OrderDetail', backref='order', lazy=True)

class OrderDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    cake_id = db.Column(db.Integer, db.ForeignKey('cake.id'), nullable=False)
    flavor = db.Column(db.String(64), nullable=False)
    design = db.Column(db.String(64), nullable=False)
    message = db.Column(db.String(128), nullable=False)

class Cake(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    price = db.Column(db.Float, nullable=False)
    order_details = db.relationship('OrderDetail', backref='cake', lazy=True)

class PaymentInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    card_number = db.Column(db.String(16), nullable=False)
    expiration_date = db.Column(db.String(5), nullable=False)
    cvv = db.Column(db.String(3), nullable=False)
    billing_address = db.Column(db.String(128), nullable=False)

# Create all tables
with app.app_context():
    db.create_all()

def validate_request_data(data, required_fields):
    for field in required_fields:
        if field not in data:
            return False
    return True

@app.route('/api/users', methods=['POST'])
def create_account():
    """
    Create a new user account.

    Request Body:
        - username (string, required)
        - email (string, required)
        - password (string, required)
        - name (string, optional)

    Response:
        - userId (integer)
        - username (string)
        - email (string)
        - token (string)
    """
    try:
        data = request.json
        required_fields = ['username', 'email', 'password']
        if not validate_request_data(data, required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user:
            return jsonify({'error': 'Username already exists'}), 400

        new_user = User(
            username=data['username'],
            email=data['email'],
            password=generate_password_hash(data['password']),
            name=data.get('name')
        )
        db.session.add(new_user)
        db.session.commit()

        access_token = create_access_token(identity=new_user.id)
        return jsonify({
            'userId': new_user.id,
            'username': new_user.username,
            'email': new_user.email,
            'token': access_token
        }), 201
    except Exception as e:
        logger.error(e)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users/login', methods=['POST'])
def login():
    """
    Login to an existing user account.

    Request Body:
        - username (string, required)
        - password (string, required)

    Response:
        - userId (integer)
        - username (string)
        - email (string)
        - token (string)
    """
    try:
        data = request.json
        required_fields = ['username', 'password']
        if not validate_request_data(data, required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        user = User.query.filter_by(username=data['username']).first()
        if not user:
            return jsonify({'error': 'Invalid username or password'}), 401

        if not check_password_hash(user.password, data['password']):
            return jsonify({'error': 'Invalid username or password'}), 401

        access_token = create_access_token(identity=user.id)
        return jsonify({
            'userId': user.id,
            'username': user.username,
            'email': user.email,
            'token': access_token
        }), 200
    except Exception as e:
        logger.error(e)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users/<int:user_id>/orders', methods=['GET'])
@jwt_required
def get_order_history(user_id):
    """
    Retrieve a list of orders for a logged-in user.

    Response:
        - orders (list of objects)
            - orderId (integer)
            - orderDate (string)
            - total (number)
            - status (string)
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        orders = Order.query.filter_by(user_id=user_id).all()
        order_history = []
        for order in orders:
            order_history.append({
                'orderId': order.id,
                'orderDate': order.order_date,
                'total': order.total,
                'status': order.status
            })
        return jsonify({'orders': order_history}), 200
    except Exception as e:
        logger.error(e)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users/payment-info', methods=['POST'])
@jwt_required
def save_payment_info():
    """
    Save payment information for future orders (if user is logged in).

    Request Body:
        - cardNumber (string, required)
        - expirationDate (string, required)
        - cvv (string, required)
        - billingAddress (string, required)

    Response:
        - paymentInfoId (integer)
        - cardNumber (string)
        - expirationDate (string)
        - billingAddress (string)
    """
    try:
        data = request.json
        required_fields = ['cardNumber', 'expirationDate', 'cvv', 'billingAddress']
        if not validate_request_data(data, required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        payment_info = PaymentInfo(
            user_id=user_id,
            card_number=data['cardNumber'],
            expiration_date=data['expirationDate'],
            cvv=data['cvv'],
            billing_address=data['billingAddress']
        )
        db.session.add(payment_info)
        db.session.commit()

        return jsonify({
            'paymentInfoId': payment_info.id,
            'cardNumber': payment_info.card_number,
            'expirationDate': payment_info.expiration_date,
            'billingAddress': payment_info.billing_address
        }), 201
    except Exception as e:
        logger.error(e)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users/<int:user_id>/order-history', methods=['GET'])
@jwt_required
def get_order_history_with_details(user_id):
    """
    Retrieve order history for logged-in users.

    Response:
        - orders (list of objects)
            - orderId (integer)
            - orderDate (string)
            - total (number)
            - status (string)
            - orderDetails (list of objects)
                - cakeId (integer)
                - flavor (string)
                - design (string)
                - message (string)
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        orders = Order.query.filter_by(user_id=user_id).all()
        order_history = []
        for order in orders:
            order_details = []
            for detail in order.order_details:
                order_details.append({
                    'cakeId': detail.cake_id,
                    'flavor': detail.flavor,
                    'design': detail.design,
                    'message': detail.message
                })
            order_history.append({
                'orderId': order.id,
                'orderDate': order.order_date,
                'total': order.total,
                'status': order.status,
                'orderDetails': order_details
            })
        return jsonify({'orders': order_history}), 200
    except Exception as e:
        logger.error(e)
        return jsonify({'error': 'Internal server error'}), 500
