from datetime import datetime, timedelta
from hashlib import md5
from time import time
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
# import jwt
import base64
import os

class Warehouse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, index=True)
    address = db.Column(db.String(50))
    products = db.relationship('Product', secondary = 'product_warehouse' , lazy='dynamic')

    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name,
            'address':self.address,
        }
                
        return data

    def from_dict(self, data):
        for field in ['name', 'address']:
            if field in data:
                setattr(self, field, data[field])


    
    
