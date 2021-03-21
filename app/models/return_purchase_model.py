from datetime import datetime, timedelta, date
from app import db

class ReturnPurchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date  = db.Column(db.DateTime, default=datetime.utcnow, index = True)
    total_price = db.Column(db.Float(precision=2), default=0.0)
    supplier_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    return_orders_supplier =  db.relationship('OrderSupplierReturn', backref='return_purchase', lazy='dynamic')
