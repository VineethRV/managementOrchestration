
# Models
from flask_sqlalchemy import SQLAlchemy
from flask import current_app

db = SQLAlchemy()

class ContactInfo(db.Model):
    """Contact information model."""
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    physical_address = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f"ContactInfo('{self.phone_number}', '{self.email}', '{self.physical_address}')"

# Routes
from flask import Blueprint, request, jsonify
from yourapplication import db
import logging
from yourapplication.decorators import token_required

contact_info_blueprint = Blueprint('contact_info', __name__)

@contact_info_blueprint.route('/api/contact-info', methods=['GET'])
def get_contact_info():
    """
    Retrieve contact information, including phone number, email, and physical address.

    Returns:
        A JSON response with the contact information.
    """
    try:
        contact_info = ContactInfo.query.first()
        if contact_info is None:
            return jsonify({"message": "No contact information found"}), 404
        return jsonify({
            "phone_number": contact_info.phone_number,
            "email": contact_info.email,
            "physical_address": contact_info.physical_address
        }), 200
    except Exception as e:
        logging.error(f"Error retrieving contact information: {e}")
        return jsonify({"message": "Internal server error"}), 500

# Helper functions
def create_contact_info(phone_number, email, physical_address):
    """
    Create a new contact information entry.

    Args:
        phone_number (str): The phone number.
        email (str): The email.
        physical_address (str): The physical address.

    Returns:
        The created contact information entry.
    """
    try:
        contact_info = ContactInfo(phone_number=phone_number, email=email, physical_address=physical_address)
        db.session.add(contact_info)
        db.session.commit()
        return contact_info
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating contact information: {e}")
        return None
