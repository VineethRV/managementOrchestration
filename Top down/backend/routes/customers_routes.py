
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import logging

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cake_orders.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret'

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Define the Customer model
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    orders = db.relationship('Order', backref='customer', lazy=True)

# Define the Order model
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False)

# Create the database tables
with app.app_context():
    db.create_all()

# Define a function to validate the request body
def validate_request_body(expected_fields):
    try:
        data = request.json
        for field in expected_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        return data
    except Exception as e:
        logging.error(f"Error validating request body: {e}")
        return None

# Define a function to handle errors
def handle_error(error):
    logging.error(f"Error: {error}")
    return jsonify({"error": str(error)}), 500

# Define the endpoint to create a new customer account
@app.route('/api/customers', methods=['POST'])
def create_customer():
    """
    Create a new customer account.

    Request Body:
        - name (string, required)
        - email (string, required, unique)
        - password (string, required, min length 8)
        - phone (string, optional)

    Response:
        - customer_id (integer)
        - name (string)
        - email (string)
        - token (string)
    """
    try:
        expected_fields = ['name', 'email', 'password']
        data = validate_request_body(expected_fields)
        if not data:
            return jsonify({"error": "Invalid request body"}), 400

        if len(data['password']) < 8:
            return jsonify({"error": "Password must be at least 8 characters long"}), 400

        customer = Customer.query.filter_by(email=data['email']).first()
        if customer:
            return jsonify({"error": "Email already exists"}), 400

        new_customer = Customer(
            name=data['name'],
            email=data['email'],
            password=generate_password_hash(data['password']),
            phone=data.get('phone')
        )

        db.session.add(new_customer)
        db.session.commit()

        access_token = create_access_token(identity=new_customer.id)
        return jsonify({
            "customer_id": new_customer.id,
            "name": new_customer.name,
            "email": new_customer.email,
            "token": access_token
        }), 201
    except Exception as e:
        db.session.rollback()
        return handle_error(e)

# Define the endpoint to login an existing customer
@app.route('/api/customers/login', methods=['POST'])
def login_customer():
    """
    Login an existing customer to view order history.

    Request Body:
        - email (string, required)
        - password (string, required)

    Response:
        - customer_id (integer)
        - name (string)
        - email (string)
        - token (string)
    """
    try:
        expected_fields = ['email', 'password']
        data = validate_request_body(expected_fields)
        if not data:
            return jsonify({"error": "Invalid request body"}), 400

        customer = Customer.query.filter_by(email=data['email']).first()
        if not customer:
            return jsonify({"error": "Email does not exist"}), 404

        if not check_password_hash(customer.password, data['password']):
            return jsonify({"error": "Invalid password"}), 401

        access_token = create_access_token(identity=customer.id)
        return jsonify({
            "customer_id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "token": access_token
        }), 200
    except Exception as e:
        return handle_error(e)

# Define a decorator to require authentication
def require_auth(f):
    @jwt_required
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

# Define the endpoint to retrieve order history for a logged-in customer
@app.route('/api/customers/orders', methods=['GET'])
@require_auth
def get_order_history():
    """
    Retrieve order history for a logged-in customer.

    Response:
        - orders (list of objects)
            - order_id (integer)
            - order_date (date)
            - total (decimal)
            - status (string)
    """
    try:
        customer_id = get_jwt_identity()
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({"error": "Customer not found"}), 404

        orders = customer.orders.all()
        order_history = []
        for order in orders:
            order_history.append({
                "order_id": order.id,
                "order_date": order.order_date,
                "total": order.total,
                "status": order.status
            })

        return jsonify({"orders": order_history}), 200
    except Exception as e:
        return handle_error(e)

# Define the endpoint to retrieve the customer's name and contact information
@app.route('/api/customers/me', methods=['GET'])
@require_auth
def get_customer_info():
    """
    Retrieve the customer's name and contact information.

    Response:
        - customer_id (integer)
        - name (string)
        - email (string)
        - phone (string)
    """
    try:
        customer_id = get_jwt_identity()
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({"error": "Customer not found"}), 404

        return jsonify({
            "customer_id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone
        }), 200
    except Exception as e:
        return handle_error(e)

if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR)
    app.run(debug=True)
