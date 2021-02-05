from datetime import datetime, timedelta
from hashlib import md5
from time import time
from flask import current_app
from app import db

class Brand(db.Model):
    id = db.Column(db.Integer, primary_key =True)
    name = db.Column(db.Unicode(64), nullable=False, index=True, unique=True) 
    # products = db.relationship('Product', secondary=brand_product_association_table, lazy='subquery',
    #     backref=db.backref('brands', lazy=True))
    products = db.relationship('Product', backref='brand', lazy='dynamic')


    
    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name
        }
                
        return data
    
    def from_dict(self, data):
        for field in ["name"]:
            if field in data:
                setattr(self, field, data[field])
