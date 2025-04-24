import os   #5462
from flask import Flask, render_template, url_for, session, redirect, request
import csv
from psycopg2 import sql
import database

#filepath = 'testdata.csv'
#with open(filepath, mode='r', encoding='utf-8') as file:
    #csv_reader = csv.reader(file)
    #for row in csv_reader:
        #print(row)

app = Flask(__name__)
app.secret_key = '12345'

app.config['uploads'] = 'uploads'
allowed_extentions = {'csv'}

#os.makedirs(filesfolder, exist_ok=True)

@app.route('/')#главная страница: если зареган то главная с профилем, если нет то вместо профиля будет кнопка войти
def main():
    reg = 0
    if 'user_id' in session:
        reg = 1
    else:
        reg = 0
    return render_template('home.html', regged=reg)


@app.route('/reg')         #страница регистрации
def reg():
    return render_template('register.html')

@app.route('/logged')      #дает статус залогиненного
def logged():
    session['user_id'] = 1
    return redirect(url_for('main'))

@app.route('/log')         #страница входа
def log():
    return render_template('login.html')

@app.route('/logout')      #дает статус незалогиненного, в главной вместо профиля кнопка войти
def logout():
    session.pop('user_id', None)
    return redirect(url_for('main'))

@app.route('/download', methods=['GET','POST'])  #страница загрузки, просто демка, удалить потом
def load():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        else:
            os.makedirs('uploads', exist_ok=True)
            filepath = os.path.join(app.config['uploads'], file.filename)
            file.save(filepath)
    return render_template('load.html')

@app.route('/test')
def test():
    print(database.get_info())
    return render_template('error-500.html')


@app.route('/dashboard')         #страница профиля
def dash():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)