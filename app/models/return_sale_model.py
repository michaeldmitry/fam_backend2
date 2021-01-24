from datetime import datetime, timedelta, date
from app import db

class ReturnSale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date  = db.Column(db.DateTime, default=datetime.utcnow, index = True)
    total_price = db.Column(db.Float, default=0.0)
    customer_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    return_orders_customer=  db.relationship('OrderCustomerReturn', backref='return_sale', lazy='dynamic')
