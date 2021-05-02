from datetime import datetime, timedelta
from hashlib import md5
from time import time
from flask import current_app
from app import db
import base64
import os
from app.models.client_model import Client
from app.models.employee_model import Employee
from app.models.product_model import Product
from sqlalchemy.types import JSON

class SaleDraft(db.Model):
    id = db.Column(db.Integer, primary_key =True)
    date = db.Column(db.DateTime, default = datetime.utcnow)
    total_price = db.Column(db.Float(2), default =0.0)
    official = db.Column(db.Boolean, default=True)
    orders = db.Column(JSON, default=lambda: [{"product_id":0, "quantity": '', "price_per_item": '', "product_description": '', "quantity_error": ''}])
    employees_belong = db.Column(JSON, default=lambda: [0])
    customer_id = db.Column(db.String(64), default='')
    taxes_add = db.Column(db.Boolean, default=True)
    reduction_add = db.Column(db.Boolean, default=False)
    representative_name = db.Column(db.String(64), default='')
    representative_number = db.Column(db.String(64), default='')
    representative_email = db.Column(db.String(64), default='')



    def to_dict(self):
        print("customer:"+str(self.customer_id))
        data = {
            'id': self.id,
            'total_price': self.total_price,
            'sale_type': self.official,
            'orders':  [{"product_id":order['product_id'], "product":  Product.query.get(order['product_id']).part_number if Product.query.get(order['product_id']) else order['product_id'], "quantity": order['quantity'], "price_per_item": order['price_per_item'], "product_description": order['product_description']} for order in self.orders], 
            'employees_belong': self.employees_belong,
            'customer_id': self.customer_id,
            'taxes_add': self.taxes_add,
            'reduction_add': self.reduction_add,
            'date': self.date,
            'representative_name':self.representative_name,
            'representative_number':self.representative_number,
            'representative_email': self.representative_email,
            'customer': None if len(self.customer_id.strip()) == 0 else Client.query.get_or_404(int(self.customer_id)).name,
            # 'employees': []
        }
        data['employees'] = [ {"fullname": Employee.query.get_or_404(int(emp)).fullname, "id": Employee.query.get_or_404(int(emp)).id} for emp in self.employees_belong if emp!=0]

        return data
    
    # def from_dict(self, data, customer):
    #     for field in [ "total_price", "official", "orders", "employees_belong", "paid", "taxes_add", "reduction_add"]:
    #         if field in data:
    #             setattr(self, field, data[field])
    #     if customer:
    #         self.customer = customer
    


    
    
