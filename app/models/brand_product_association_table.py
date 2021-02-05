from app import db


brand_product_association_table = db.Table('brand_product_association',
    db.Column('brand_id', db.Integer, db.ForeignKey('brand.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True)
)

