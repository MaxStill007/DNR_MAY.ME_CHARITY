from app import create_app, db
from app.models import User, Partner, BonusType, Bonus
from config import Config

app = create_app(Config)


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Partner': Partner,
        'BonusType': BonusType,
        'Bonus': Bonus
    }

if __name__ == '__main__':
    app.run(debug=True)