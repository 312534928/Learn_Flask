from flask import render_template, session, redirect, url_for,current_app

from . import main
from .forms import NameForm
from .. import db
from ..models import User
from ..email import send_email

@main.route('/user/<name>')
def user(name):  # view function
    return render_template('user.html', username=name)


@main.route('/home/')
def home():  # view function
    return render_template('home.html')


@main.route('/contact/')
def contact():  # view function
    return render_template('contact.html')


@main.route('/', methods=['GET', 'POST'])
def index():  # view function
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            session['known'] = False
            if current_app.config['FLASKY_ADMIN']:
                send_email(current_app.config['FLASKY_ADMIN'], 'New User', 'mail/new_user', user=user)
        else:
            session['known'] = True
        session['name'] = form.name.data
        return redirect(url_for('.index'))  # 重定向为get模式
    return render_template('index.html', form=form, name=session.get('name'), known=session.get('known', False))
