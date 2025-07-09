from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail

# Instantiate all extensions here
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

# login_manager settings
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'