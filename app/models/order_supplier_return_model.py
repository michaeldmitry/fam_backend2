from datetime import datetime, timedelta
from hashlib import md5
from time import time
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
# import jwt
import base64
import os

class OrderSupplierReturn(db.Model):
    id = db.Column(db.Integer, primary_key =True)
    date = db.Column(db.DateTime, default = datetime.utcnow)
    quantity = db.Column(db.Integer, default = 0)
    price_per_item = db.Column(db.Float)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    return_purchase_id = db.Column(db.Integer, db.ForeignKey('return_purchase.id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('client.id'))

    


    
    
