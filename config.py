import os

WTF_CSRF_ENABLED = True
SECRET_KEY = 'intro-project'

basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

# admins list
ADMINS = ['aristaintroproj@gmail.com', 'tinaw6212@gmail.com', 'shakilrafi0@gmail.com']

# email server
DEBUG = True
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USERNAME = 'aristaintroproj@gmail.com'
MAIL_PASSWORD = 'not a secure password'
