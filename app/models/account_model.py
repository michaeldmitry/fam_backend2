from app import db


class Account(db.Model):
    id = db.Column(db.Integer, primary_key =True)
    year = db.Column(db.Integer, nullable=False, index=True, unique=True) 
    # clients = db.relationship('Client', secondary = 'client_account' , lazy='dynamic')

    def to_dict(self):
        data = {
            'id': self.id,
            'year': self.year
        }
                
        return data
    
    def from_dict(self, data):
        for field in ["year"]:
            if field in data:
                setattr(self, field, data[field])
