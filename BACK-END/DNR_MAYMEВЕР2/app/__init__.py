from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# Создаем экземпляры расширений
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login'  # Указываем маршрут для входа

@login_manager.user_loader
def load_user(user_id):
    from app.models import User  # Отложенная загрузка модели User
    return User.query.get(int(user_id))

def create_app(config_class=None):
    app = Flask(__name__)

    app.config.from_object('config.Config')

    # Инициализируем расширения
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Регистрируем Blueprint
    from app.routes import main
    app.register_blueprint(main)

    return app
