from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
import os
import bcrypt
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Для работы с сессиями и flash-сообщениями

# Путь к файлу пользователей
USERS_FILE = 'users.json'

# Папка для аватарок
AVATAR_FOLDER = 'static/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Проверка расширения файла
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Загрузка пользователей из файла
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)["users"]
    return []

# Сохранение пользователей в файл
def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as file:
        json.dump({"users": users}, file, ensure_ascii=False, indent=4)

# Хеширование пароля с использованием bcrypt
def hash_password(password):
    # Генерация соли и хеширование пароля
    salt = bcrypt.gensalt()  # Генерация соли
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)  # Хеширование пароля
    return hashed_password.decode('utf-8')  # Возвращаем строку

# Проверка пароля
def check_password(input_password, stored_hash):
    return bcrypt.checkpw(input_password.encode('utf-8'), stored_hash.encode('utf-8'))

# Сохранение аватара
def save_avatar(avatar):
    if avatar and allowed_file(avatar.filename):
        # Генерируем уникальное имя файла для аватара
        filename = str(uuid.uuid4()) + '.' + avatar.filename.rsplit('.', 1)[1].lower()
        filepath = os.path.join(AVATAR_FOLDER, filename)
        avatar.save(filepath)
        return filename
    return None

# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_repeat = request.form['password_repeat']
        name = request.form['name']
        nickname = request.form['nickname']
        phone = request.form['phone']
        gender = request.form['gender']
        avatar = request.files['avatar'] 

        # Проверка совпадения паролей
        if password != password_repeat:
            flash("Пароли не совпадают!", "error")
            return redirect(url_for('register'))

        # Проверка на существующего пользователя
        users = load_users()
        if any(user['username'] == username for user in users):
            flash("Пользователь с таким логином уже существует", "error")
            return redirect(url_for('register'))

        # Хеширование пароля
        hashed_password = hash_password(password)

        # Сохранение аватара
        avatar_filename = save_avatar(avatar)
        avatar_url = f"/static/avatars/{avatar_filename}" if avatar_filename else "/static/avatars/default.png"

        # Сохранение данных
        registration_date = datetime.now().isoformat()
        new_user = {
            "username": username,
            "password": hashed_password,
            "email": request.form['email'],
            "name": name,
            "nickname": nickname,
            "phone": phone,
            "gender": gender,
            "avatar_url": avatar_url,
            "registration_date": registration_date
        }

        users.append(new_user)
        save_users(users)

        flash("Регистрация прошла успешно!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/')
def home():
    return redirect(url_for('login')) 

# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        users = load_users()
        user = next((user for user in users if user['username'] == username), None)

        if user and check_password(password, user['password']):
            flash("Вход выполнен успешно!", "success")
            return redirect(url_for('profile', username=username))
        else:
            flash("Неверно введен логин и/или пароль", "error")
            return redirect(url_for('login'))

    return render_template('login.html')

# Страница профиля
@app.route('/profile/<username>')
def profile(username):
    users = load_users()
    user = next((user for user in users if user['username'] == username), None)
    if user:
        return render_template('profile.html', user=user)
    return redirect(url_for('login'))

# Выход из аккаунта
@app.route('/logout')
def logout():
    return redirect(url_for('login'))

if __name__ == '__main__':
    if not os.path.exists(AVATAR_FOLDER):
        os.makedirs(AVATAR_FOLDER)  # Создаём папку для аватарок, если её нет
    app.run(debug=True)
