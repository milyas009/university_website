from application import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.objects(user_id=int(user_id)).first()

class User(UserMixin, db.Document):
    user_id     = db.IntField(unique=True)
    first_name  = db.StringField(max_length=50)
    last_name   = db.StringField(max_length=50)
    email       = db.StringField(max_length=30, unique=True)
    password    = db.StringField()
    notification_preferences = db.DictField(default={
        'email_notifications': True,
        'course_updates': True,
        'newsletter': False
    })
    privacy_settings = db.DictField(default={
        'profile_visible': True,
        'show_progress': True
    })
    last_login = db.DateTimeField()

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def get_id(self):
        return str(self.user_id)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Course(db.Document):
    course_id = db.StringField(max_length=10, unique=True, required=True)
    title = db.StringField(max_length=100, required=True)
    description = db.StringField(max_length=255)
    credits = db.IntField()
    term = db.StringField(max_length=25)

class Enrollment(db.Document):
    user = db.ReferenceField('User', required=True)
    course = db.ReferenceField('Course', required=True)
    completed = db.BooleanField(default=False)
    progress = db.IntField(default=0)
    enrollment_date = db.DateTimeField(default=datetime.utcnow)
    meta = {'allow_inheritance': True}