
# Import necessary libraries
from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from datetime import datetime

# Initialize the database and blueprint
db = SQLAlchemy()
pos_blueprint = Blueprint('pos_blueprint', __name__)

# Define the POS system model
class PosSystem(db.Model):
    id = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    api_key = db.Column(db.String(100), nullable=False)
    credentials = db.Column(db.JSON, nullable=False)

    def __repr__(self):
        return f"PosSystem('{self.id}', '{self.name}', '{self.description}', '{self.api_key}', '{self.credentials}')"

# Define the connection history model
class ConnectionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pos_system_id = db.Column(db.String(100), db.ForeignKey('pos_system.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"ConnectionHistory('{self.id}', '{self.pos_system_id}', '{self.timestamp}', '{self.status}')"

# Define the cake inventory model
class CakeInventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cake_id = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"CakeInventory('{self.id}', '{self.cake_id}', '{self.quantity}')"

# Routes
@pos_blueprint.route('/api/pos/systems', methods=['GET'])
def get_available_pos_systems():
    """
    Returns a list of available POS systems for integration.
    
    :return: A list of POS systems
    """
    try:
        pos_systems = PosSystem.query.all()
        return jsonify([{'id': pos_system.id, 'name': pos_system.name, 'description': pos_system.description, 'api_key': pos_system.api_key, 'credentials': pos_system.credentials} for pos_system in pos_systems])
    except SQLAlchemyError as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": "Failed to retrieve POS systems"}), 500

@pos_blueprint.route('/api/pos/connect', methods=['POST'])
@jwt_required
def connect_to_pos_system():
    """
    Connects to a POS system using the provided API key or credentials.
    
    :return: A JSON object with the connected status and POS system ID
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing request body"}), 400
        api_key = data.get('api_key')
        credentials = data.get('credentials')
        if not api_key or not credentials:
            return jsonify({"error": "Missing API key or credentials"}), 400
        pos_system = PosSystem.query.filter_by(api_key=api_key).first()
        if not pos_system:
            return jsonify({"error": "Invalid API key"}), 404
        # Connect to the POS system using the provided credentials
        # For demonstration purposes, this is a placeholder
        connected = True
        return jsonify({"connected": connected, "pos_system_id": pos_system.id})
    except SQLAlchemyError as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": "Failed to connect to POS system"}), 500

@pos_blueprint.route('/api/pos/disconnect', methods=['POST'])
@jwt_required
def disconnect_from_pos_system():
    """
    Disconnects from the currently connected POS system.
    
    :return: A JSON object with the disconnected status
    """
    try:
        # Disconnect from the POS system
        # For demonstration purposes, this is a placeholder
        disconnected = True
        return jsonify({"disconnected": disconnected})
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": "Failed to disconnect from POS system"}), 500

@pos_blueprint.route('/api/pos/status', methods=['GET'])
@jwt_required
def get_pos_system_integration_status():
    """
    Returns the current integration status and connection history of the POS system.
    
    :return: A JSON object with the integration status and connection history
    """
    try:
        pos_system_id = request.args.get('pos_system_id')
        if not pos_system_id:
            return jsonify({"error": "Missing POS system ID"}), 400
        pos_system = PosSystem.query.filter_by(id=pos_system_id).first()
        if not pos_system:
            return jsonify({"error": "Invalid POS system ID"}), 404
        connection_history = ConnectionHistory.query.filter_by(pos_system_id=pos_system_id).all()
        return jsonify({"connected": True, "pos_system_id": pos_system_id, "connection_history": [{"timestamp": history.timestamp, "status": history.status} for history in connection_history]})
    except SQLAlchemyError as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": "Failed to retrieve POS system status"}), 500

@pos_blueprint.route('/api/pos/inventory', methods=['PUT'])
@jwt_required
def update_cake_inventory():
    """
    Updates the cake inventory in the website based on the POS system data.
    
    :return: A JSON object with the updated status
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing request body"}), 400
        inventory = data.get('inventory')
        if not inventory:
            return jsonify({"error": "Missing inventory data"}), 400
        for item in inventory:
            cake_id = item.get('cake_id')
            quantity = item.get('quantity')
            if not cake_id or not quantity:
                return jsonify({"error": "Missing cake ID or quantity"}), 400
            cake_inventory = CakeInventory.query.filter_by(cake_id=cake_id).first()
            if cake_inventory:
                cake_inventory.quantity = quantity
            else:
                cake_inventory = CakeInventory(cake_id=cake_id, quantity=quantity)
                db.session.add(cake_inventory)
        db.session.commit()
        return jsonify({"updated": True})
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Error: {e}")
        return jsonify({"error": "Failed to update cake inventory"}), 500

@pos_blueprint.route('/api/pos/override', methods=['PUT'])
@jwt_required
def override_pos_system_data():
    """
    Manually overrides the POS system data for cake inventory or availability.
    
    :return: A JSON object with the overridden status
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing request body"}), 400
        cake_id = data.get('cake_id')
        quantity = data.get('quantity')
        availability = data.get('availability')
        if not cake_id or not quantity or not availability:
            return jsonify({"error": "Missing cake ID, quantity, or availability"}), 400
        cake_inventory = CakeInventory.query.filter_by(cake_id=cake_id).first()
        if cake_inventory:
            cake_inventory.quantity = quantity
        else:
            cake_inventory = CakeInventory(cake_id=cake_id, quantity=quantity)
            db.session.add(cake_inventory)
        db.session.commit()
        return jsonify({"overridden": True})
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Error: {e}")
        return jsonify({"error": "Failed to override POS system data"}), 500

@pos_blueprint.route('/api/pos/history', methods=['GET'])
@jwt_required
def get_pos_system_connection_history():
    """
    Returns the connection history of the POS system.
    
    :return: A list of connection history
    """
    try:
        pos_system_id = request.args.get('pos_system_id')
        if not pos_system_id:
            return jsonify({"error": "Missing POS system ID"}), 400
        connection_history = ConnectionHistory.query.filter_by(pos_system_id=pos_system_id).all()
        return jsonify([{"timestamp": history.timestamp, "status": history.status} for history in connection_history])
    except SQLAlchemyError as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": "Failed to retrieve POS system connection history"}), 500

@pos_blueprint.route('/api/pos/error', methods=['POST'])
@jwt_required
def handle_pos_system_error():
    """
    Handles errors that occur during POS system integration or synchronization.
    
    :return: A JSON object with the handled status
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing request body"}), 400
        error_code = data.get('error_code')
        error_message = data.get('error_message')
        if not error_code or not error_message:
            return jsonify({"error": "Missing error code or message"}), 400
        # Handle the error
        # For demonstration purposes, this is a placeholder
        handled = True
        return jsonify({"handled": handled})
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": "Failed to handle POS system error"}), 500

@pos_blueprint.route('/api/pos/credentials', methods=['GET'])
@jwt_required
def get_pos_system_credentials():
    """
    Returns the credentials of the currently connected POS system.
    
    :return: A JSON object with the POS system credentials
    """
    try:
        pos_system_id = request.args.get('pos_system_id')
        if not pos_system_id:
            return jsonify({"error": "Missing POS system ID"}), 400
        pos_system = PosSystem.query.filter_by(id=pos_system_id).first()
        if not pos_system:
            return jsonify({"error": "Invalid POS system ID"}), 404
        return jsonify({"api_key": pos_system.api_key, "credentials": pos_system.credentials})
    except SQLAlchemyError as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": "Failed to retrieve POS system credentials"}), 500

@pos_blueprint.route('/api/pos/credentials', methods=['PUT'])
@jwt_required
def update_pos_system_credentials():
    """
    Updates the credentials of the currently connected POS system.
    
    :return: A JSON object with the updated status
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing request body"}), 400
        pos_system_id = data.get('pos_system_id')
        api_key = data.get('api_key')
        credentials = data.get('credentials')
        if not pos_system_id or not api_key or not credentials:
            return jsonify({"error": "Missing POS system ID, API key, or credentials"}), 400
        pos_system = PosSystem.query.filter_by(id=pos_system_id).first()
        if not pos_system:
            return jsonify({"error": "Invalid POS system ID"}), 404
        pos_system.api_key = api_key
        pos_system.credentials = credentials
        db.session.commit()
        return jsonify({"updated": True})
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Error: {e}")
        return jsonify({"error": "Failed to update POS system credentials"}), 500
