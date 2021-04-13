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
# extra modules
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

        # user data
        user = User(
            name=form.name.data,
            email=form.email.data,
            status=form.status.data
        )
        # объявляем глобальные переменные для использования в функции send_message()
        global cod_authentication, email_for_authentication
        email_for_authentication = form.email.data
        # генерация рандомного 5 значного кода
        cod_authentication = random.randint(10000, 99999)
        # функция отправки письма на почту
        send_message(form.email.data, cod_authentication)

        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()

        return redirect('/authentication')

    return render_template('register.html',
                           title='Регистрация',
                           form=form
                           )


@app.route('/authentication', methods=['GET', 'POST'])
def authentication():
    if request.method == 'POST':
        cod = request.form['cod']
        if cod and int(cod) == cod_authentication:
            return redirect('/login')
        else:
            return render_template('authentication.html',
                                   message='Неправильный код',
                                   email_for_authentication=email_for_authentication
                                   )
    return render_template('authentication.html', email_for_authentication=email_for_authentication)


def send_message(email_to, cod_authentications):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from platform import python_version

    server = 'smtp.mail.ru'
    user = 'test_acc_web1@mail.ru'
    drowssap = '9LT-Fdn-MyY-UQb'
    recipients = [email_to]
    sender = 'test_acc_web1@mail.ru'
    subject = 'VPP - Рассылка сообщений'
    text = f'Добро пожаловать, {email_to} теперь вы часть платформы VPP!!! ' \
           f'Код подтверждения:<b>{cod_authentications}.</b>'
    html = '<html><head></head><body><h1 style="align-text:center;">'+text+'</h1></body></html>'
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
    mail.login(user, drowssap)
    mail.sendmail(sender, recipients, msg.as_string())
    mail.quit()


# login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    # login form
    form = LoginForm()

    # submit button
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        # user search

        sotrudnik = db_sess.query(User).filter(User.email == form.email.data,
                                               User.status == 'Сотрудник').first()
        potreb = db_sess.query(User).filter(User.email == form.email.data,
                                            User.status == 'Потребитель').first()
        # check password
        if sotrudnik and sotrudnik.check_password(form.password.data):
            login_user(sotrudnik, remember=form.remember_me.data)
            # go home
            return redirect("/sotrudnik")

        if potreb and potreb.check_password(form.password.data):
            login_user(potreb)
            # go home
            return redirect("/potreb")
        # user error
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)

    # return template
    return render_template('login.html', form=form)


# personal account
@app.route('/sotrudnik', methods=['GET', 'POST'])
def sotrudnik():
    con = sqlite3.connect("db/data.db")
    cur = con.cursor()
    info_sotrudniki = cur.execute("SELECT email FROM users WHERE status='Сотрудник'").fetchall()
    info_potreb = cur.execute("SELECT email FROM users WHERE status='Потребитель'").fetchall()
    # return template
    return render_template('sotrudnik.html',
                           len_sotrudnik=len(info_sotrudniki),
                           len_potreb=len(info_potreb))


# personal account
@app.route('/potreb', methods=['GET', 'POST'])
def potreb():
    # return template
    return render_template('potreb.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


def main():
    # initilize database
    db_session.global_init("db/data.db")

    app.run(port=8080, host='127.0.0.1', debug=True)


if __name__ == '__main__':
    main()

