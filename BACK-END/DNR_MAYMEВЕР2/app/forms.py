from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, BooleanField, TextAreaField, FileField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models import User

class RegistrationForm(FlaskForm):
    inn = StringField('ИНН', validators=[DataRequired(), Length(min=10, max=12)])
    full_name = StringField('ФИО', validators=[DataRequired()])
    phone = StringField('Телефон', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    birth_date = DateField('Дата рождения', format='%Y-%m-%d', validators=[DataRequired()])
    achievements = TextAreaField('Достижения')
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

    def validate_inn(self, inn):
        from flask import current_app
        with current_app.app_context():
            user = User.query.filter_by(inn=inn.data).first()
            if user:
                raise ValidationError('Этот ИНН уже зарегистрирован')

class PartnerRegistrationForm(RegistrationForm):
    company_name = StringField('Название компании', validators=[DataRequired()])
    description = TextAreaField('Описание компании')
    partner_key = StringField('Ключ партнера', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться как партнер')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')  # Добавьте это поле
    submit = SubmitField('Sign In')

class BonusForm(FlaskForm):
    name = StringField('Название бонуса', validators=[DataRequired()])
    description = TextAreaField('Описание бонуса')
    level = SelectField('Уровень бонуса', choices=[
        ('max', 'Максимальный (1-50 место)'),
        ('medium', 'Средний (51-100 место)'),
        ('min', 'Минимальный (101-150 место)')
    ], validators=[DataRequired()])
    submit = SubmitField('Создать бонус')

class CSVUploadForm(FlaskForm):
    csv_file = FileField('CSV файл', validators=[DataRequired()])
    submit = SubmitField('Импортировать')