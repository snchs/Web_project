# flask framework
from flask import Flask, render_template, request, make_response, session, redirect, abort
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
# models
from data import db_session
from data.users import User
# sqlite
import sqlite3
# forms
from forms.register_form import RegisterForm
from forms.login_form import LoginForm
# random
import random
# datetime
import datetime

# flask init
app = Flask(__name__)
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
    days=365
)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

# login manager init
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


# home page
@app.route("/")
def index():
    dict_status_user = {'Сотрудник': '/sotrudnik',
                        'Потребитель': '/potreb'}
    if current_user.is_authenticated:
        return render_template("base.html", status_page=dict_status_user[current_user.status])
    return render_template("base.html")


# register page
@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    # register button
    if form.validate_on_submit():
        # check password match
        if form.password.data != form.password_again.data:
            # passwords isn't match
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        # new session
        db_sess = db_session.create_session()
        # check registered
        if db_sess.query(User).filter(User.email == form.email.data).first():
            # this email was registered
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        # если статус пользователя потребитель, потребление случайно 200-500
        if form.status.data == 'Потребитель':
            consumption = random.randint(200, 500)
        # сотрудник, потребелние нет
        else:
            consumption = -1
        # user data
        # генерация, накопление и кошелек потребителя в лк по дефолту -1
        user = User(
            name=form.name.data,
            email=form.email.data,
            status=form.status.data,
            consumption=consumption,
            generation=-1,
            storage=-1,
            wallet=-1
        )
        # объявляем глобальные переменные для использования в функции send_message()
        global cod_authentication, email_for_authentication
        # почта зарег пользователя
        email_for_authentication = form.email.data
        # генерация рандомного 5 значного кода
        cod_authentication = random.randint(10000, 99999)
        # функция отправки письма на почту
        send_message(form.email.data, cod_authentication)
        # установить пароль, коммит бд
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        # переход на страницу подтвержения почты
        return redirect('/authentication')

    return render_template('register.html',
                           title='Регистрация',
                           form=form
                           )


# страница потверждения пороля
@app.route('/authentication', methods=['GET', 'POST'])
def authentication():
    # если 5 значный пороль введен
    if request.method == 'POST':
        # извлекаем из формы пороль
        cod = request.form['cod']
        # проверка на корректность пороля
        if cod and int(cod) == cod_authentication:
            # переход на страницу входа в лк
            return redirect('/login')
        else:
            # вывод сообщения о неправильности кода
            return render_template('authentication.html',
                                   message='Неправильный код',
                                   email_for_authentication=email_for_authentication
                                   )
    return render_template('authentication.html',
                           email_for_authentication=email_for_authentication
                           )


# функция отправки сообщения пользователю, пытающийся зарегаться на сайте
def send_message(email_to, cod_authentications):
    # импорт необх библеотек
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from platform import python_version
    # настройка
    server = 'smtp.mail.ru'
    # аккаунт для рассылки
    user = 'test_acc_web1@mail.ru'
    drowssap = '9LT-Fdn-MyY-UQb'
    # куда отправить
    recipients = [email_to]
    # кто
    sender = 'test_acc_web1@mail.ru'
    # Название письма
    subject = 'VPP - Подтверждение регистрации.'
    # текст письма
    text = f'Добро пожаловать, {email_to} теперь вы часть платформы VPP!!! ' \
           f'Код подтверждения:<b>{cod_authentications}.</b>'
    html = '<html><head></head><body><h1 style="align-text:center;">'+text+'</h1></body></html>'
    # манимкляции с сообщением
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = 'Python script <'+sender+'>'
    msg['To'] = ', '.join(recipients)
    msg['Reply-To'] = sender
    msg['Return-Path'] = sender
    msg['X-Mailer'] = 'Python/'+(python_version())
    part_text = MIMEText(text, 'plain')
    part_html = MIMEText(html, 'html')
    msg.attach(part_text)
    msg.attach(part_html)
    mail = smtplib.SMTP_SSL(server)
    # вход аккаунта рассыльщика
    mail.login(user, drowssap)
    # отправка сообщения
    mail.sendmail(sender, recipients, msg.as_string())
    # выход
    mail.quit()


# login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    # login form
    form = LoginForm()

    # submit button
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        # поиск пользователя в базе данных
        sotrudnik_inf = db_sess.query(User).filter(User.email == form.email.data,
                                                   User.status == 'Сотрудник').first()
        potreb_inf = db_sess.query(User).filter(User.email == form.email.data,
                                                User.status == 'Потребитель').first()
        # если пользователь сотрудник и пороль совпадает, отправляет в лк сотрудника
        if sotrudnik_inf and sotrudnik_inf.check_password(form.password.data):
            login_user(sotrudnik_inf)
            # go home
            return redirect("/sotrudnik")
        # если пользователь потребитель и пороль совпадает, отправляет в лк потребителя
        if potreb_inf and potreb_inf.check_password(form.password.data):
            login_user(potreb_inf)
            # go home
            return redirect("/potreb")
        # user error
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)

    # return template
    return render_template('login.html', form=form)


# лк сотрудника
@app.route('/sotrudnik', methods=['GET', 'POST'])
def sotrudnik():
    # подключение к бд
    con = sqlite3.connect("db/data.db")
    cur = con.cursor()
    # поиск колва  сотрудников и потребителей
    info_sotrudniki = cur.execute("SELECT email FROM users WHERE status='Сотрудник'").fetchall()
    info_potreb = cur.execute("SELECT email FROM users WHERE status='Потребитель'").fetchall()
    # return template
    return render_template('sotrudnik.html',
                           len_sotrudnik=len(info_sotrudniki),
                           len_potreb=len(info_potreb)
                           )


# лк потребителя
@app.route('/potreb', methods=['GET', 'POST'])
def potreb():
    # подключение к бд
    con = sqlite3.connect("db/data.db")
    cur = con.cursor()
    # получение всех данных
    info_consumption, info_generation, \
    info_storage, info_wallet = cur.execute(f"SELECT consumption, generation,"
                                            f" storage, wallet FROM users "
                                            f"WHERE email='{current_user.email}'").fetchall()[0]
    # если одна из форм отправлена, нажата кнопка (первых раз, -1)
    if request.method == 'POST' and info_storage == -1 \
            and info_generation == -1 and info_wallet == -1:
        # случайное значение генерации
        info_generation = random.randint(200, 500)
        # если потребление не меньше генерации, то накопитель 0
        if info_consumption >= info_generation:
            info_storage = 0
        # иначе разница
        else:
            info_storage = info_generation - info_consumption
        # случаное значение баланса энергии т.е сколько стоит энергия из накопителя
        info_wallet = round(3.8 * info_storage, 2)
        # обновить данные -> изменение данных с -1 на соответсвующие
        res = cur.execute(f"UPDATE users SET storage = {info_storage} "
                          f"WHERE email = '{current_user.email}'").fetchall()
        res = cur.execute(f"UPDATE users SET generation = {info_generation} "
                          f"WHERE email = '{current_user.email}'").fetchall()
        res = cur.execute(f"UPDATE users SET wallet = {info_wallet} "
                          f"WHERE email = '{current_user.email}'").fetchall()
        # добавление пользователя в бд для уведомления сотрудника
        res = cur.execute(f"INSERT INTO message(email, datetime) VALUES('{current_user.email}',"
                          f" '{datetime.datetime.now()}')").fetchall()
        #  применение изменений
        con.commit()

        return render_template('potreb.html',
                               info_consumption=info_consumption,
                               info_storage=info_storage,
                               info_generation=info_generation,
                               info_wallet=info_wallet
                               )

    return render_template('potreb.html',
                           info_consumption=info_consumption,
                           info_generation=info_generation,
                           info_storage=info_storage,
                           info_wallet=info_wallet
                           )


# таблица с запросом потребителя к сотруднику ЭСК
@app.route('/message_sotrud')
def message_sotrud():
    # подкл к бд
    con = sqlite3.connect("db/data.db")
    cur = con.cursor()
    # создание списка потребителей, сделавшие запрос сотруднику
    email_message = cur.execute("SELECT email, datetime FROM message").fetchall()

    print(email_message)
    return render_template('message_sotrud.html', email_message=email_message)


# выход пользователя
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

# главная функция
def main():
    # initilize database
    db_session.global_init("db/data.db")
    app.run(port=8080, host='127.0.0.1', debug=True)


if __name__ == '__main__':
    main()
