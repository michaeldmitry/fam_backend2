from datetime import datetime, timedelta
from hashlib import md5
from time import time
from flask import current_app
# from werkzeug.security import generate_password_hash, check_password_hash
from app import db
# import jwt
import base64
import os

class OrderPriceQuota(db.Model):
    id = db.Column(db.Integer, primary_key =True)
    date = db.Column(db.DateTime, default = datetime.utcnow)
    quantity = db.Column(db.Integer, default = 0)
    price_per_item = db.Column(db.Float(2))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    description = db.Column(db.Unicode(64))
    price_quota_id = db.Column(db.Integer, db.ForeignKey('price_quotas.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('client.id'))

    def to_dict(self):
        data = {
            'id': self.id,
            'date': self.date,
            'product':self.product.part_number,
            'quantity':self.quantity,
            'price_per_item':self.price_per_item,
            'price_quota_id': self.price_quota_id,
            'customer': self.customer.name,
            'product_id': self.product_id,
            'total':self.quantity*self.price_per_item,
            'product_description': self.description
        }
                
        return data

    


    
    
