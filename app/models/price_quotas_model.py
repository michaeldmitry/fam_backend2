from datetime import datetime, timedelta
from hashlib import md5
from time import time
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
# import jwt
import base64
import os
# from app.models.sale_employee_association_table import sale_employee_association_table

class PriceQuotas(db.Model):
    id = db.Column(db.Integer, primary_key =True)
    date = db.Column(db.DateTime, default = datetime.utcnow)
    total_price = db.Column(db.Float(2), default = 0.0)
    # official_id = db.Column(db.BigInteger, default=1000, index=True)
    representative_name = db.Column(db.Unicode(64))
    representative_number = db.Column(db.String(13))
    representative_email = db.Column(db.String(40))

    customer_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    orders_customer =  db.relationship('OrderPriceQuota', backref='sale', lazy='dynamic')
    # employees = db.relationship('Employee', secondary=sale_employee_association_table, backref='employee_sales', lazy='dynamic')


    def to_dict(self):
        data = {
            'id': self.id,
            'representative_name': self.representative_name,
            'representative_number': self.representative_number,
            'representative_email': self.representative_email,
            'date': self.date,
            'total_price':self.total_price,
            'customer':self.customer.name,
            'customer_id': self.customer_id,
        }
        # data['employees'] = [ {"fullname":emp.fullname, "id": emp.id} for emp in self.employees.all()]

        return data
    
    def from_dict(self, data, customer):
        for field in ["total_price"]:
            if field in data:
                setattr(self, field, data[field])
        if customer:
            self.customer = customer
    


    
    
