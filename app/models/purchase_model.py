from datetime import datetime, timedelta
from hashlib import md5
from time import time
from flask import current_app
from app import db
from .order_supplier_model import OrderSupplier

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key =True, autoincrement=False)
    taxes_included = db.Column(db.Boolean, default = True)
    date = db.Column(db.DateTime, default = datetime.utcnow)
    paid = db.Column(db.Float(2), default = 0.0)
    total_price = db.Column(db.Float(2), default = 0.0)
    representative_name = db.Column(db.Unicode(64))
    representative_number = db.Column(db.String(13))
    representative_email = db.Column(db.String(50))
    supplier_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    orders_supplier =  db.relationship('OrderSupplier', backref='purchase', lazy='dynamic')
    
    def to_dict(self):
        data = {
            'id': self.id,
            'taxes_included': self.taxes_included,
            'date': self.date,
            'total_price':self.total_price,
            'supplier':self.supplier.name,
            'supplier_id': self.supplier_id,
            'paid':self.paid,
            'representative_name': self.representative_name,
            'representative_number': self.representative_number,
            'representative_email': self.representative_email,
        }
                
        return data
    
    def from_dict(self, data, supplier):
        for field in ["id", "total_price", "paid", "taxes_included"]:
            if field in data:
                setattr(self, field, data[field])
        if supplier:
            self.supplier = supplier