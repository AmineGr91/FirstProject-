from extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum
import datetime
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy import func # Import func for aggregate functions

# Association table for followers
followers = db.Table('followers', db.metadata,
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

# Enums for roles and registration status
class Role(Enum):
    STUDENT = 'student'
    ORGANIZER = 'organizer'
    ADMIN = 'admin'

class RegistrationStatus(Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    CANCELLED = 'cancelled'

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum(Role), default=Role.STUDENT, nullable=False)
    profile_picture = db.Column(db.String(50), nullable=False, default='default.jpg') # Increased length for full path
    
    # Relationships
    events = db.relationship('Event', backref='organizer', lazy=True)
    registrations = db.relationship('Registration', backref='user', lazy=True)
    ratings = db.relationship('Rating', backref='user', lazy=True)
    # FIX: Change lazy=True to lazy='dynamic' for notifications
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    
    # Many-to-many self-referencing relationship for followers
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            return True
        return False

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            return True
        return False

    def is_following(self, user):
        # Ensure 'user' is a User object before accessing its ID
        if isinstance(user, User):
            return self.followed.filter(followers.c.followed_id == user.id).count() > 0
        return False

# Flask-Login user loader function
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id)) # Use db.session.get for by-primary-key fetches

# Event Model
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    max_attendees = db.Column(db.Integer, nullable=True) # Max attendees is optional
    poster = db.Column(db.String(50), nullable=False, default='default_event_poster.jpg')
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    
    # Relationships
    registrations = db.relationship('Registration', backref='event', lazy='dynamic', cascade="all, delete-orphan")
    ratings = db.relationship('Rating', backref='event', lazy='dynamic', cascade="all, delete-orphan")

    # Hybrid property for average_rating calculation
    @hybrid_property
    def average_rating(self):
        if self.ratings.count() == 0:
            return 0.0
        return sum(rating.rating for rating in self.ratings.all()) / self.ratings.count()

    @average_rating.expression
    def average_rating(cls):
        return db.session.query(func.avg(Rating.rating)).filter(Rating.event_id == cls.id).label("average_rating")

# Registration Model
class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    registration_date = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    status = db.Column(db.Enum(RegistrationStatus), default=RegistrationStatus.PENDING, nullable=False)

# Category Model
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    events = db.relationship('Event', backref='category', lazy='dynamic') # lazy='dynamic' for .count()

# Rating Model
class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

# Notification Model
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)