
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret'

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Define models
class Cake(db.Model):
    id = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    flavor = db.Column(db.String(100), nullable=False)
    design = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(100), nullable=False)

class PickupOption(db.Model):
    id = db.Column(db.String(100), primary_key=True)
    address = db.Column(db.String(100), nullable=False)
    time_slots = db.relationship('TimeSlot', backref='pickup_option', lazy=True)

class DeliveryOption(db.Model):
    id = db.Column(db.String(100), primary_key=True)
    address = db.Column(db.String(100), nullable=False)
    time_slots = db.relationship('TimeSlot', backref='delivery_option', lazy=True)
    fee = db.Column(db.Float, nullable=False)

class TimeSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.String(100), nullable=False)
    end_time = db.Column(db.String(100), nullable=False)
    pickup_option_id = db.Column(db.String(100), db.ForeignKey('pickup_option.id'), nullable=True)
    delivery_option_id = db.Column(db.String(100), db.ForeignKey('delivery_option.id'), nullable=True)

class PaymentMethod(db.Model):
    id = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(100), nullable=False)

class Order(db.Model):
    id = db.Column(db.String(100), primary_key=True)
    cake_id = db.Column(db.String(100), db.ForeignKey('cake.id'), nullable=False)
    pickup_option_id = db.Column(db.String(100), db.ForeignKey('pickup_option.id'), nullable=True)
    delivery_option_id = db.Column(db.String(100), db.ForeignKey('delivery_option.id'), nullable=True)
    payment_method_id = db.Column(db.String(100), db.ForeignKey('payment_method.id'), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(100), nullable=False)
    total_cost = db.Column(db.Float, nullable=False)

# Set up logging
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)

# Routes
@app.route('/api/checkout/options', methods=['GET'])
def get_checkout_options():
    """
    Retrieve available pickup and delivery options with corresponding addresses and time slots.
    
    Returns:
        A JSON object containing pickup and delivery options.
    """
    try:
        pickup_options = PickupOption.query.all()
        delivery_options = DeliveryOption.query.all()
        return jsonify({
            'pickup_options': [{'id': option.id, 'address': option.address, 'time_slots': [{'start_time': time_slot.start_time, 'end_time': time_slot.end_time} for time_slot in option.time_slots]} for option in pickup_options],
            'delivery_options': [{'id': option.id, 'address': option.address, 'time_slots': [{'start_time': time_slot.start_time, 'end_time': time_slot.end_time} for time_slot in option.time_slots], 'fee': option.fee} for option in delivery_options]
        }), 200
    except Exception as e:
        app.logger.error(e)
        return jsonify({'error': 'Failed to retrieve checkout options'}), 500

@app.route('/api/checkout/payment-methods', methods=['GET'])
def get_payment_methods():
    """
    Retrieve available payment method options.
    
    Returns:
        A JSON object containing payment method options.
    """
    try:
        payment_methods = PaymentMethod.query.all()
        return jsonify({
            'payment_methods': [{'id': method.id, 'name': method.name, 'description': method.description} for method in payment_methods]
        }), 200
    except Exception as e:
        app.logger.error(e)
        return jsonify({'error': 'Failed to retrieve payment methods'}), 500

@app.route('/api/checkout/orders', methods=['POST'])
@jwt_required
def create_order():
    """
    Create a new order with selected pickup or delivery option and payment details.
    
    Request Body:
        cake_id (string): The ID of the cake.
        pickup_option_id (string): The ID of the pickup option.
        delivery_option_id (string): The ID of the delivery option.
        payment_method_id (string): The ID of the payment method.
        payment_details (object): The payment details.
        customer_name (string): The name of the customer.
        customer_email (string): The email of the customer.
        customer_phone (string): The phone number of the customer.
    
    Returns:
        A JSON object containing the order ID and total cost.
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400
        cake_id = data.get('cake_id')
        pickup_option_id = data.get('pickup_option_id')
        delivery_option_id = data.get('delivery_option_id')
        payment_method_id = data.get('payment_method_id')
        payment_details = data.get('payment_details')
        customer_name = data.get('customer_name')
        customer_email = data.get('customer_email')
        customer_phone = data.get('customer_phone')
        
        if not cake_id or not payment_method_id or not customer_name or not customer_email or not customer_phone:
            return jsonify({'error': 'Missing required fields'}), 400
        
        cake = Cake.query.get(cake_id)
        if not cake:
            return jsonify({'error': 'Cake not found'}), 404
        
        pickup_option = PickupOption.query.get(pickup_option_id) if pickup_option_id else None
        delivery_option = DeliveryOption.query.get(delivery_option_id) if delivery_option_id else None
        payment_method = PaymentMethod.query.get(payment_method_id)
        if not payment_method:
            return jsonify({'error': 'Payment method not found'}), 404
        
        order = Order(
            cake_id=cake_id,
            pickup_option_id=pickup_option_id,
            delivery_option_id=delivery_option_id,
            payment_method_id=payment_method_id,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            total_cost=cake.price
        )
        
        db.session.add(order)
        db.session.commit()
        
        return jsonify({
            'order_id': order.id,
            'total_cost': order.total_cost
        }), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(e)
        return jsonify({'error': 'Failed to create order'}), 500

@app.route('/api/checkout/payment-details/validate', methods=['POST'])
def validate_payment_details():
    """
    Validate payment details such as card number, expiration date, and CVV.
    
    Request Body:
        card_number (string): The card number.
        expiration_date (string): The expiration date.
        cvv (string): The CVV.
    
    Returns:
        A JSON object containing a boolean indicating whether the payment details are valid and an error message.
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400
        card_number = data.get('card_number')
        expiration_date = data.get('expiration_date')
        cvv = data.get('cvv')
        
        if not card_number or not expiration_date or not cvv:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate payment details using a dummy payment gateway
        # Replace with a real payment gateway
        is_valid = True
        error_message = ''
        
        return jsonify({
            'is_valid': is_valid,
            'error_message': error_message
        }), 200
    except Exception as e:
        app.logger.error(e)
        return jsonify({'error': 'Failed to validate payment details'}), 500

@app.route('/api/checkout/payment/process', methods=['POST'])
@jwt_required
def process_payment():
    """
    Process payment using a dummy payment gateway for testing purposes.
    
    Request Body:
        order_id (string): The ID of the order.
        payment_method_id (string): The ID of the payment method.
        payment_details (object): The payment details.
    
    Returns:
        A JSON object containing the payment status and an error message.
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400
        order_id = data.get('order_id')
        payment_method_id = data.get('payment_method_id')
        payment_details = data.get('payment_details')
        
        if not order_id or not payment_method_id or not payment_details:
            return jsonify({'error': 'Missing required fields'}), 400
        
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        payment_method = PaymentMethod.query.get(payment_method_id)
        if not payment_method:
            return jsonify({'error': 'Payment method not found'}), 404
        
        # Process payment using a dummy payment gateway
        # Replace with a real payment gateway
        payment_status = 'success'
        error_message = ''
        
        return jsonify({
            'payment_status': payment_status,
            'error_message': error_message
        }), 200
    except Exception as e:
        app.logger.error(e)
        return jsonify({'error': 'Failed to process payment'}), 500

@app.route('/api/checkout/orders/summary', methods=['GET'])
@jwt_required
def get_order_summary():
    """
    Retrieve order summary, including cake details, pickup/delivery option, and total cost.
    
    Request Body:
        order_id (string): The ID of the order.
    
    Returns:
        A JSON object containing the order summary.
    """
    try:
        order_id = request.args.get('order_id')
        if not order_id:
            return jsonify({'error': 'Missing required fields'}), 400
        
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        cake = Cake.query.get(order.cake_id)
        if not cake:
            return jsonify({'error': 'Cake not found'}), 404
        
        pickup_option = PickupOption.query.get(order.pickup_option_id) if order.pickup_option_id else None
        delivery_option = DeliveryOption.query.get(order.delivery_option_id) if order.delivery_option_id else None
        
        return jsonify({
            'order_id': order.id,
            'cake_details': {
                'name': cake.name,
                'flavor': cake.flavor,
                'design': cake.design,
                'message': cake.message
            },
            'pickup_option': {
                'id': pickup_option.id,
                'address': pickup_option.address,
                'time_slot': {
                    'start_time': pickup_option.time_slots[0].start_time,
                    'end_time': pickup_option.time_slots[0].end_time
                }
            } if pickup_option else None,
            'delivery_option': {
                'id': delivery_option.id,
                'address': delivery_option.address,
                'time_slot': {
                    'start_time': delivery_option.time_slots[0].start_time,
                    'end_time': delivery_option.time_slots[0].end_time
                },
                'fee': delivery_option.fee
            } if delivery_option else None,
            'total_cost': order.total_cost
        }), 200
    except Exception as e:
        app.logger.error(e)
        return jsonify({'error': 'Failed to retrieve order summary'}), 500

@app.route('/api/checkout/orders/status', methods=['PUT'])
@jwt_required
def update_order_status():
    """
    Update order status in the restaurant's existing POS system and inventory management.
    
    Request Body:
        order_id (string): The ID of the order.
        status (string): The new status of the order.
    
    Returns:
        A JSON object containing a boolean indicating whether the order status was updated and an error message.
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400
        order_id = data.get('order_id')
        status = data.get('status')
        
        if not order_id or not status:
            return jsonify({'error': 'Missing required fields'}), 400
        
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Update order status in the restaurant's existing POS system and inventory management
        # Replace with a real implementation
        is_updated = True
        error_message = ''
        
        return jsonify({
            'is_updated': is_updated,
            'error_message': error_message
        }), 200
    except Exception as e:
        app.logger.error(e)
        return jsonify({'error': 'Failed to update order status'}), 500

@app.route('/api/checkout/orders/calculate-taxes', methods=['POST'])
@jwt_required
def calculate_taxes():
    """
    Calculate applicable taxes, fees, or discounts for an order.
    
    Request Body:
        order_id (string): The ID of the order.
        cake_id (string): The ID of the cake.
        pickup_option_id (string): The ID of the pickup option.
        delivery_option_id (string): The ID of the delivery option.
    
    Returns:
        A JSON object containing the taxes, fees, discounts, and total cost.
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400
        order_id = data.get('order_id')
        cake_id = data.get('cake_id')
        pickup_option_id = data.get('pickup_option_id')
        delivery_option_id = data.get('delivery_option_id')
        
        if not order_id or not cake_id or not pickup_option_id or not delivery_option_id:
            return jsonify({'error': 'Missing required fields'}), 400
        
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        cake = Cake.query.get(cake_id)
        if not cake:
            return jsonify({'error': 'Cake not found'}), 404
        
        pickup_option = PickupOption.query.get(pickup_option_id)
        if not pickup_option:
            return jsonify({'error': 'Pickup option not found'}), 404
        
        delivery_option = DeliveryOption.query.get(delivery_option_id)
        if not delivery_option:
            return jsonify({'error': 'Delivery option not found'}), 404
        
        # Calculate taxes, fees, and discounts
        # Replace with a real implementation
        taxes = 0
        fees = delivery_option.fee
        discounts = 0
        total_cost = cake.price + fees
        
        return jsonify({
            'taxes': taxes,
            'fees': fees,
            'discounts': discounts,
            'total_cost': total_cost
        }), 200
    except Exception as e:
        app.logger.error(e)
        return jsonify({'error': 'Failed to calculate taxes'}), 500

if __name__ == '__main__':
    app.run(debug=True)
