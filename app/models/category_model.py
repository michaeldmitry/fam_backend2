from datetime import datetime, timedelta
from hashlib import md5
from time import time
from flask import current_app
from app import db

class Category(db.Model):
    id = db.Column(db.Integer, primary_key =True)
    name = db.Column(db.String(64), nullable=False, index=True, unique=True)
    subcategories = db.relationship('Subcategory', backref='category', lazy='dynamic')

    
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
