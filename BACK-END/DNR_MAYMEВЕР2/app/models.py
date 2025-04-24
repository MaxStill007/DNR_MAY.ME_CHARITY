from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from app import db

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    inn = db.Column(db.String(12), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    birth_date = db.Column(db.Date, nullable=True)
    password_hash = db.Column(db.Text, nullable=True)
    role = db.Column(db.String(20), nullable=False)  # 'volunteer', 'partner', 'admin'
    achievements = db.Column(db.Text)
    rating = db.Column(db.Integer)
    partner_key = db.Column(db.String(50))  # только для партнеров
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bonuses = db.relationship('Bonus', back_populates='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

class Partner(db.Model):
    __tablename__ = 'partners'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    verified = db.Column(db.Boolean, default=False)

    bonuses_offered = db.relationship('BonusType', backref='partner', lazy=True)


class BonusType(db.Model):
    __tablename__ = 'bonus_types'

    id = db.Column(db.Integer, primary_key=True)
    partner_id = db.Column(db.Integer, db.ForeignKey('partners.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    level = db.Column(db.String(20))  # 'max', 'medium', 'min'
    expires_in = db.Column(db.Integer, default=6)  # месяцев


class Bonus(db.Model):
    __tablename__ = 'bonuses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bonus_type_id = db.Column(db.Integer, db.ForeignKey('bonus_types.id'), nullable=False)
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Дата выдачи бонуса
    expires_at = db.Column(db.DateTime, nullable=False)  # Дата истечения срока действия
    used = db.Column(db.Boolean, default=False, nullable=False)  # Использован ли бонус

    user = db.relationship('User', back_populates='bonuses')
    bonus_type = db.relationship('BonusType', backref='bonuses')

    def __init__(self, **kwargs):
        super(Bonus, self).__init__(**kwargs)
        self.expires_at = datetime.utcnow() + timedelta(days=180)


class CSVImport(db.Model):
    __tablename__ = 'csv_imports'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    imported_at = db.Column(db.DateTime, default=datetime.utcnow)
    rows_processed = db.Column(db.Integer)