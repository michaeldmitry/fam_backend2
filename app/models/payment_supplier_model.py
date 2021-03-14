from datetime import datetime, timedelta
from hashlib import md5
from time import time
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
# import jwt
import base64
import os

class PaymentSupplier(db.Model):
    id = db.Column(db.Integer, primary_key =True)
    date = db.Column(db.DateTime, default = datetime.utcnow)
    amount = db.Column(db.Float, default = 0.0)
    supplier_id =  db.Column(db.Integer, db.ForeignKey('client.id'))
    
    def to_dict(self):
        data = {
            'id': self.id,
            'date': self.date,
            'amount':self.amount,
            'supplier':self.supplier.name,
        }
                
        return data
    
    def from_dict(self, data):
        for field in ["amount"]:
            if field in data and data[field]:
                setattr(self, field, data[field])

    
