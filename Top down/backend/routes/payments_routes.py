
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from sqlalchemy.exc import IntegrityError, DataError
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cakes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this!
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Set up logging
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    payment_method = db.Column(db.String(100), nullable=False)
    card_number = db.Column(db.String(20), nullable=True)
    expiration_date = db.Column(db.String(5), nullable=True)
    cvv = db.Column(db.String(3), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    order_id = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(10), nullable=False, default='pending')

    def __repr__(self):
        return f"Payment('{self.payment_method}', '{self.amount}', '{self.order_id}')"

# Helper function to validate payment request
def validate_payment_request(data):
    if 'payment_method' not in data:
        return False, 'Payment method is required'
    if data['payment_method'] == 'credit card':
        if 'card_number' not in data or 'expiration_date' not in data or 'cvv' not in data:
            return False, 'Card number, expiration date, and CVV are required for credit card payments'
    if 'amount' not in data:
        return False, 'Amount is required'
    if 'order_id' not in data:
        return False, 'Order ID is required'
    return True, ''

# Route to process payment
@app.route('/api/payments', methods=['POST'])
@jwt_required
def process_payment():
    """
    Process payment for an order.

    :return: JSON response with payment ID, status, and message
    """
    try:
        data = request.json
        is_valid, message = validate_payment_request(data)
        if not is_valid:
            return jsonify({'message': message}), 400
        payment = Payment(
            payment_method=data['payment_method'],
            card_number=data.get('card_number'),
            expiration_date=data.get('expiration_date'),
            cvv=data.get('cvv'),
            amount=data['amount'],
            order_id=data['order_id']
        )
        db.session.add(payment)
        db.session.commit()
        # Simulate payment processing (replace with actual payment gateway)
        payment.status = 'success'
        db.session.commit()
        return jsonify({
            'payment_id': payment.id,
            'status': payment.status,
            'message': 'Payment processed successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error processing payment: {e}')
        return jsonify({'message': 'Error processing payment'}), 500

# Route to verify payment
@app.route('/api/payments/verify', methods=['GET'])
@jwt_required
def verify_payment():
    """
    Verify payment status.

    :return: JSON response with payment ID, status, and message
    """
    try:
        order_id = request.args.get('order_id')
        if not order_id:
            return jsonify({'message': 'Order ID is required'}), 400
        payment = Payment.query.filter_by(order_id=order_id).first()
        if not payment:
            return jsonify({'message': 'Payment not found'}), 404
        return jsonify({
            'payment_id': payment.id,
            'status': payment.status,
            'message': 'Payment verified successfully'
        }), 200
    except Exception as e:
        app.logger.error(f'Error verifying payment: {e}')
        return jsonify({'message': 'Error verifying payment'}), 500

if __name__ == '__main__':
    app.run(debug=True)
