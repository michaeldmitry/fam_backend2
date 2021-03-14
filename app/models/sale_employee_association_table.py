from app import db


sale_employee_association_table = db.Table('sale_employee_association',
    db.Column('sale_id', db.Integer, db.ForeignKey('sale.id'), primary_key=True),
    db.Column('employee_id', db.Integer, db.ForeignKey('employee.id'), primary_key=True)
)

