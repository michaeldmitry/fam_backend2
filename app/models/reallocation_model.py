from datetime import datetime, timedelta, date
from app import db
from .warehouse_model import Warehouse

class Reallocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date  = db.Column(db.DateTime, default=datetime.utcnow)
    quantity = db.Column(db.Integer)
    from_loc = db.Column(db.String(50))
    to_loc = db.Column(db.String(50))
    from_warehouse_id = db.Column(db.Integer)
    to_warehouse_id = db.Column(db.Integer)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))

    def to_dict(self):
        data = {
            'id': self.id,
            'date': self.date,
            'quantity':self.quantity,
            'product':self.product.part_number
        }
        if(self.from_loc == "store"):
            data['from_loc'] = self.from_loc
            data['to_loc'] = Warehouse.query.get_or_404(self.to_warehouse_id).name
        elif(self.from_loc == "warehouse"):
            data['from_loc'] = Warehouse.query.get_or_404(self.from_warehouse_id).name
            if(self.to_loc == "warehouse"):
                data['to_loc'] = Warehouse.query.get_or_404(self.to_warehouse_id).name
            elif(self.to_loc == "store"):
                data['to_loc'] = self.to_loc
                
        return data