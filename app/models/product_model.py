from datetime import datetime, timedelta
from hashlib import md5
from time import time
from flask import current_app
from app import db
# import jwt
import base64
import os
from .product_warehouse_model import ProductWarehouse
from .reallocation_model import Reallocation
from sqlalchemy.sql import func
from sqlalchemy import text
from sqlalchemy.types import JSON

class Product(db.Model):
    id = db.Column(db.Integer, primary_key =True)
    description = db.Column(db.Unicode(64))
    part_number = db.Column(db.String(20))
    store_qt = db.Column(db.Integer, default=0)
    store_loc = db.Column(db.String(50), default='None')
    preorder_level = db.Column(db.Integer, default = 0)
    notes = db.Column(db.String(50))

    # replasement = db.Column(db.String(50))
    replaces_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    replaced_by = db.relationship('Product', backref=db.backref('replaces', remote_side=[id]))
    root_replacement_id = db.Column(db.Integer)
    
    orders_supplier = db.relationship('OrderSupplier', backref='product', lazy='dynamic')
    orders_customer = db.relationship('OrderCustomer', backref='product', lazy='dynamic')

    returns_order_supplier = db.relationship('OrderSupplierReturn', backref='product', lazy='dynamic')
    returns_order_customer = db.relationship('OrderCustomerReturn', backref='product', lazy='dynamic')

    warehouses = db.relationship('Warehouse', secondary = 'product_warehouse' , lazy='dynamic')
    reallocations = db.relationship('Reallocation', backref = 'product' , lazy='dynamic')
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategory.id'))
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))

    attributes = db.Column(JSON)

    def to_dict(self, warehouse_id= None):
        data = {
            'id': self.id,
            'description': self.description,
            'part_number': self.part_number,
            'preorder_level': self.preorder_level,
            'store_qt': self.store_qt,
            'subcategory_id': self.subcategory_id,
            'subcategory': self.subcategory.name,
            'category': self.subcategory.category.name,
            'brand': self.brand.name,
            'replaces_id': self.replaces_id,
            'replaces': self.replaces.part_number if self.replaces else None,
            'root_replacement_id': self.root_replacement_id,
            'root_replacement': Product.query.get(self.root_replacement_id).part_number if self.root_replacement_id else None
        }
        

    
        total_quantity = self.store_qt
        sum_query = text('select SUM(product_warehouse.quantity) as Total from product_warehouse where product_warehouse.product_id='+str(self.id))
        res_query = db.engine.execute(sum_query)
        result = [dict(row) for row in res_query]
        data['total_quantity'] = self.store_qt + int(result[0]['Total'])

        if(warehouse_id):
            data['warehouse_quantity'] = ProductWarehouse.query.filter(ProductWarehouse.product_id == self.id, ProductWarehouse.warehouse_id == warehouse_id).first().quantity
        return data
        
    def to_dict_drop(self):
        data = {
            'value': self.id,
            'label': self.part_number,
            'description': self.description,
            
        }
        return data

    def check_store_availability(self, quantity):
        if(self.store_qt >= quantity):
            return True
        return False

    def getProductUpTree(self):
        sql = text("with recursive cteUp (id, part_number, replaces_id) as (select id, part_number, replaces_id from product where id = {} union all select p.id,\
             p.part_number, p.replaces_id from product p inner join cteUp on p.id= cteUp.replaces_id) select * from cteUp;".format(self.id))

        both = db.engine.execute(sql)
        return both
