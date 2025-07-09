import os
from flask import Flask
from config import Config
from extensions import db, login_manager, mail
from models import User, Role, Category # Central models file
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone
import pytz # For datetime localization
from flask_migrate import Migrate

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
        
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate = Migrate(app, db)
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.now(timezone.utc)}

    # Custom Jinja2 Filter for Datetime Localization
    @app.template_filter('localize_datetime')
    def localize_datetime_filter(dt, format='%Y-%m-%d ', tz_name='UTC'):
        """
        Localizes a datetime object to a specific timezone and formats it.
        Assumes incoming dt is timezone-aware (preferably UTC).
        """
        if dt is None:
            return "" # Handle None datetime objects gracefully

        # Ensure dt is timezone-aware. If naive, assume UTC.
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        try:
            target_tz = pytz.timezone(tz_name) # pytz.timezone requires a string
            dt_localized = dt.astimezone(target_tz)
            return dt_localized.strftime(format)
        except Exception as e:
            # Fallback if pytz is not used, tz_name is invalid, or any other conversion error
            print(f"Error in localize_datetime_filter: {e}. Falling back to UTC format.")
            return dt.astimezone(timezone.utc).strftime(format) 

    # Import and Register Blueprints
    from auth import auth_bp
    from event_routes import event_bp
    from admin_routes import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(event_bp) # Assumed default prefix '/' for main blueprint

    with app.app_context():
        db.create_all() # Will create tables if they don't exist

        if not User.query.filter_by(email='admin@example.com').first():
            admin_user = User(username='admin', email='admin@example.com', role=Role.ADMIN)
            admin_user.set_password('password')
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user 'admin@example.com' created.")

        if not Category.query.first():
            default_categories = ['Academic', 'Social', 'Sport', 'Workshop', 'Conference', 'Concert', 'Festival']
            for cat_name in default_categories:
                db.session.add(Category(name=cat_name))
            db.session.commit()
            print("Default categories created.")


    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)