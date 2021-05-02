# from app import db

# class ClientAccount(db.Model):
#     # id = db.Column(db.Integer, primary_key=True)
#     balance = db.Column(db.Float, default=0.0)
#     outstanding = db.Column(db.Float, default=0.0)

#     client_id = db.Column(db.Integer, db.ForeignKey('client.id') , primary_key=True)
#     account_id = db.Column(db.Integer, db.ForeignKey('account.id'), primary_key=True)

#     client = db.relationship('Client',  backref = 'client_assoc')
#     account = db.relationship('Account',  backref = 'account_assoc')
    