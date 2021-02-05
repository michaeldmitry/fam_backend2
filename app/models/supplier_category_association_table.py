from app import db


supplier_category_association_table = db.Table('supplier_category_association',
    db.Column('supplier_id', db.Integer, db.ForeignKey('client.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True)
)

