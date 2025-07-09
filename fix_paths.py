from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'  # Database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Event model (same as your original)
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    poster = db.Column(db.String(100), nullable=False)

# Function to clean the paths
def clean_poster_paths():
    # Query all events
    events = Event.query.all()

    for event in events:
        # Fix incorrect paths
        if '\\' in event.poster:  # If backslashes are in the path (Windows-style paths)
            event.poster = event.poster.replace("\\", "/")  # Change backslashes to forward slashes
            db.session.commit()  # Commit the change to the database
            print(f"Updated path for event: {event.id}")

    print("Path cleanup completed!")

# Call the function to clean paths
if __name__ == "__main__":
    with app.app_context():
        clean_poster_paths()
