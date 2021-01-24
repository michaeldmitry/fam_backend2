from datetime import datetime, timedelta
from hashlib import md5
from time import time
from flask import current_app
# from werkzeug.security import generate_password_hash, check_password_hash
from app import db
# import jwt
import base64
import os

class OrderCustomer(db.Model):
    id = db.Column(db.Integer, primary_key =True)
    date = db.Column(db.DateTime, default = datetime.utcnow)
    quantity = db.Column(db.Integer, default = 0)
    price_per_item = db.Column(db.Float)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('client.id'))

    def to_dict(self):
        data = {
            'id': self.id,
            'date': self.date,
            'product':self.product.part_number,
            'quantity':self.quantity,
            'price_per_item':self.price_per_item,
            'sale_id': self.sale_id,
            'customer': self.customer.name,
            'product_id': self.product_id,
            'product_description': self.product.description
        }
                
        return data

    


    
    
