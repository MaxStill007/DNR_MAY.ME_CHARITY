from werkzeug.http import parse_date
from werkzeug.utils import secure_filename
from app.models import db, User, Partner, BonusType, Bonus, CSVImport
from .forms import RegistrationForm, PartnerRegistrationForm, LoginForm, BonusForm, CSVUploadForm
import csv
from datetime import datetime
import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from app.models import User
from app.forms import LoginForm, RegistrationForm
from app import db
from .utils import volunteer_required, partner_required, admin_required
from functools import wraps
import codecs
from datetime import datetime
from werkzeug.security import generate_password_hash

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html')

@main.route('/register/volunteer', methods=['GET', 'POST'])
def register_volunteer():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            inn=form.inn.data,
            full_name=form.full_name.data,
            phone=form.phone.data,
            email=form.email.data,
            birth_date=form.birth_date.data,
            role='volunteer',
            achievements=form.achievements.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация прошла успешно!', 'success')
        return redirect(url_for('main.login'))
    return render_template('register_volunteer.html', form=form)

@main.route('/register/partner', methods=['GET', 'POST'])
def register_partner():
    form = PartnerRegistrationForm()
    if form.validate_on_submit():
        if form.partner_key.data != current_app.config['PARTNER_REGISTRATION_KEY']:
            flash('Неверный ключ партнера', 'danger')
            return redirect(url_for('main.register_partner'))

        user = User(
            inn=form.inn.data,
            full_name=form.full_name.data,
            phone=form.phone.data,
            email=form.email.data,
            birth_date=form.birth_date.data,
            role='partner',
            partner_key=form.partner_key.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        partner = Partner(
            user_id=user.id,
            company_name=form.company_name.data,
            description=form.description.data
        )
        db.session.add(partner)
        db.session.commit()

        flash('Регистрация партнера прошла успешно! Ожидайте подтверждения.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register_partner.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Неверный email или пароль', 'danger')
    return render_template('login.html', form=form)

@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('main.admin_dashboard'))
    elif current_user.role == 'partner':
        return redirect(url_for('main.partner_dashboard'))
    return redirect(url_for('main.volunteer_dashboard'))

@main.route('/manage/volunteers')
@login_required
def manage_volunteers():
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))

    volunteers = User.query.filter_by(role='volunteer').all()
    return render_template('admin/manage_volunteers.html', volunteers=volunteers)


@main.route('/admin/dashboard', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_dashboard():
    # Статистика
    volunteers_count = User.query.filter_by(role='volunteer').count()
    partners_count = Partner.query.count()
    active_bonuses_count = Bonus.query.filter_by(used=False).count()

    # Список волонтеров с их достижениями и активными бонусами
    volunteers = User.query.filter_by(role='volunteer').all()
    for volunteer in volunteers:
        volunteer.active_bonuses = Bonus.query.filter_by(user_id=volunteer.id, used=False).all()

    # История выданных бонусов
    bonuses_history = Bonus.query.order_by(Bonus.awarded_at.desc()).limit(10).all()

    # Последние импорты
    last_imports = CSVImport.query.order_by(CSVImport.imported_at.desc()).limit(10).all()

    # Обработка загрузки файла
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Файл не найден.', 'danger')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('Файл не выбран.', 'danger')
            return redirect(request.url)

        # Сохранение файла
        os.makedirs('uploads', exist_ok=True)
        filepath = os.path.join('uploads', secure_filename(file.filename))
        file.save(filepath)

        # Обработка CSV-файла (пример)
        try:
            rows_processed = process_csv(filepath)
            new_import = CSVImport(
                filename=file.filename,
                rows_processed=rows_processed
            )
            db.session.add(new_import)
            db.session.commit()
            flash(f'Файл успешно загружен. Загружено записей: {rows_processed}', 'success')
        except Exception as e:
            flash(f'Ошибка при обработке файла: {str(e)}', 'danger')

    return render_template(
        'admin/dashboard.html',
        volunteers_count=volunteers_count,
        partners_count=partners_count,
        active_bonuses_count=active_bonuses_count,
        volunteers=volunteers,
        bonuses_history=bonuses_history,
        last_imports=last_imports
    )

@main.route('/partner/dashboard')
@login_required
@partner_required
def partner_dashboard():
    """Панель партнера с управлением бонусами"""
    partner_data = {
        'profile': Partner.query.filter_by(user_id=current_user.id).first_or_404(),
        'bonuses': BonusType.query.filter_by(partner_id=current_user.id).all(),
        'volunteers': User.query.filter_by(role='partner')
                              .order_by(User.rating.desc())
                              .limit(50)
                              .all()
    }
    return render_template('partner/dashboard.html', **partner_data)

@main.route('/volunteer/dashboard')
@login_required
@volunteer_required
def volunteer_dashboard():
    active_bonuses = Bonus.query.filter(
        Bonus.user_id == current_user.id,
        Bonus.expires_at > datetime.utcnow(),
        Bonus.used == False
    ).all()

    partners = Partner.query.filter_by(verified=True).all()

    bonus_level = get_bonus_level(current_user.rating)

    return render_template('volunteer/dashboard.html',
                           active_bonuses=active_bonuses,
                           partners=partners,
                           bonus_level=bonus_level)

@main.route('/reports')
@login_required
@admin_required
def reports():
    # Логика для генерации отчётов
    return render_template('admin/reports.html')

@main.route('/import_csv', methods=['GET', 'POST'])
@login_required
def import_csv():
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))

    form = CSVUploadForm()
    if form.validate_on_submit():
        filename = secure_filename(form.csv_file.data.filename)
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        form.csv_file.data.save(upload_path)

        # Обработка CSV
        processed_rows = process_csv(upload_path)

        # Сохраняем информацию об импорте
        csv_import = CSVImport(
            filename=filename,
            rows_processed=processed_rows
        )
        db.session.add(csv_import)
        db.session.commit()

        flash(f'Файл успешно импортирован. Обработано {processed_rows} строк.', 'success')
        return redirect(url_for('main.admin_dashboard'))

    return render_template('/import_csv.html', form=form)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Доступ запрещён. Только для администраторов.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def parse_date(date_str):
    """Пытается преобразовать дату в один из поддерживаемых форматов."""
    for fmt in ('%d.%m.%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Неверный формат даты: {date_str}")

def process_csv(filepath):
    try:
        with codecs.open(filepath, 'r', encoding='utf-8-sig') as f:  # Удаляем BOM
            reader = csv.DictReader(f, delimiter=';')  # Указываем разделитель
            rows_processed = 0

            # Генерация хеша для фиктивного пароля
            default_password_hash = generate_password_hash("default_password")

            for row in reader:
                # Проверка наличия обязательных полей
                if 'ИНН' not in row or not row['ИНН']:
                    flash(f"Отсутствует или пустое поле 'ИНН' в строке: {row.get('ФИО')}", 'warning')
                    continue  # Пропускаем эту строку

                user = User.query.filter_by(inn=row['ИНН']).first()

                if not user:
                    # Создаем нового пользователя
                    birth_date = None
                    if row.get('Дата рождения'):
                        try:
                            birth_date = parse_date(row['Дата рождения'])
                        except ValueError:
                            flash(f"Некорректная дата рождения: {row['Дата рождения']} для пользователя {row['ФИО']}", 'warning')
                            birth_date = datetime(1900, 1, 1)  # Значение по умолчанию
                    else:
                        birth_date = datetime(1900, 1, 1)  # Значение по умолчанию для пустых дат

                    user = User(
                        inn=row['ИНН'],
                        full_name=row.get('ФИО', ''),
                        phone=row.get('Номер телефона', ''),
                        email=row.get('Электронная почта', ''),
                        birth_date=birth_date,
                        password_hash=default_password_hash,  # Фиктивный пароль
                        achievements=row.get('Достижения', ''),
                        rating=0,  # Если рейтинг не указан, используем значение по умолчанию
                        role='volunteer'
                    )
                    db.session.add(user)
                else:
                    # Обновляем существующего пользователя
                    if row.get('Дата рождения'):
                        try:
                            user.birth_date = parse_date(row['Дата рождения'])
                        except ValueError:
                            flash(f"Некорректная дата рождения: {row['Дата рождения']} для пользователя {row['ФИО']}", 'warning')
                            user.birth_date = datetime(1900, 1, 1)  # Значение по умолчанию
                    else:
                        user.birth_date = datetime(1900, 1, 1)  # Значение по умолчанию для пустых дат

                    user.full_name = row.get('ФИО', user.full_name)
                    user.phone = row.get('Номер телефона', user.phone)
                    user.email = row.get('Электронная почта', user.email)
                    user.achievements = row.get('Достижения', user.achievements)

                rows_processed += 1

            db.session.commit()
            return rows_processed
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Ошибка при обработке CSV: {e}")

@main.route('/test_db')
def test_db():
    try:
        db.create_all()  # Попробуем создать все таблицы (если они не существуют)
        return "Подключение к базе данных успешно!"
    except Exception as e:
        return f"Ошибка подключения к базе данных: {e}"

def get_bonus_level(rating):
    if rating is None:
        rating = 0  # Устанавливаем значение по умолчанию

    if rating <= 50:
        return 'max'
    elif rating <= 100:
        return 'medium'
    else:
        return 'min'