from datetime import datetime, timedelta
from hashlib import md5
from time import time
from flask import current_app
from app import db

class Subcategory(db.Model):
    id = db.Column(db.Integer, primary_key =True)
    name = db.Column(db.Unicode(64), nullable=False, index=True, unique=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    products = db.relationship('Product', backref='subcategory', lazy='dynamic')

    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name,
            'category_id': self.category_id
        }
                
        return data
    
    def from_dict(self, data):
        for field in ["name"]:
            if field in data:
                setattr(self, field, data[field])
