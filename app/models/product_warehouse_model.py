from datetime import datetime, timedelta, date
from app import db
# from app.models.stock_model import Stock

class ProductWarehouse(db.Model):
    # id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, default=0)
    location = db.Column(db.String(50))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id') , primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), primary_key=True)

    product = db.relationship('Product',  backref = 'product_assoc')
    warehouse = db.relationship('Warehouse',  backref = 'warehouse_assoc')

    def check_warehouse_availability(self, quantity, item_id, warehouse_id):
        temp = ProductWarehouse.query.filter(ProductWarehouse.product_id == item_id , ProductWarehouse.warehouse_id == warehouse_id).first()
        if(temp.quantity < quantity):
            return False
        return True

    def reallocate_from_store(self, quantity, product_id, to_warehouse_id, location):
        temp = ProductWarehouse.query.filter(ProductWarehouse.product_id == product_id , ProductWarehouse.warehouse_id == to_warehouse_id).first()
        temp.quantity = temp.quantity + quantity
        if(location != 'N/A'):
            temp.location = location
        
        return temp

    def reallocate_from_warehouse(self, quantity, product_id, to_warehouse_id, location):
        temp = ProductWarehouse.query.filter(ProductWarehouse.product_id == product_id , ProductWarehouse.warehouse_id == to_warehouse_id).first()

        temp.quantity = temp.quantity + quantity

        if(location != "N/A"):
            temp.location = location

        return temp