from app import db
from sqlalchemy.types import LargeBinary


class Employee(db.Model):
    id = db.Column(db.Integer, primary_key =True)
    fullname = db.Column(db.String(256), nullable=False) 
    address = db.Column(db.String(256))
    phone = db.Column(db.String(11))
    id_number = db.Column(db.String(20))
    title = db.Column(db.String(50))
    insurance_number = db.Column(db.String(50))
    employment_date = db.Column(db.DateTime)
    fixed_salary = db.Column(db.Integer)
    variable_salary = db.Column(db.Integer)
    is_employee = db.Column(db.Boolean, default=True)
    profile_pic = db.Column(LargeBinary())

    def to_dict(self):
        data = {
            'id': self.id,
            'fullname': self.fullname,
            'address': self.address,
            'phone': self.phone,
            'id_number': self.id_number,
            'title': self.title,
            'insurance_number': self.insurance_number,
            'employment_date': self.employment_date,
            'fixed_salary': self.fixed_salary,
            'variable_salary': self.variable_salary,
            'is_employee': self.is_employee,
            'profile_pic': self.profile_pic
        }
                
        return data

    def from_dict(self, data):
        for field in ["fullname", "address", "phone", "id_number", "title", "insurance_number", "employment_date", "fixed_salary", "variable_salary", "profile_pic"]:
            if field in data:
                setattr(self, field, data[field])