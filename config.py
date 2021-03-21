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
    SQLALCHEMY_DATABASE_URI = "mysql://b73f82e2343771:b135b809@us-cdbr-east-03.cleardb.com/heroku_98dcd394ec262de"

    # CORS_HEADERS = 'Content-Type'