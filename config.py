import os
basedir = os.path.abspath(os.path.dirname(__file__))

# TODO: Parameterize Configuration
class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'KPjnfRG6UkCowFM3KFnkiQmF'
    server_name = "LAPTOP-FUIUHC90"
    database = "fam_test2"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # SQLALCHEMY_DATABASE_URI = "mssql+pyodbc://{}/{}?driver=SQL Server?Trusted_Connection=yes".format(server_name, database)
    # SQLALCHEMY_DATABASE_URI = "mysql://root:1234@localhost/fam_test2"
    SQLALCHEMY_DATABASE_URI = "mysql://wtjes93a2m1bvotz:ncke1c9jonlegfub@g84t6zfpijzwx08q.cbetxkdyhwsb.us-east-1.rds.amazonaws.com:3306/kgtxb4v0gixavn8d"

    # CORS_HEADERS = 'Content-Type'