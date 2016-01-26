from flask import render_template, session, redirect, url_for,current_app
from flask.ext.login import login_required
from ..decorators import permission_required,admin_required
from . import main
from .forms import NameForm
from .. import db
from ..models import User,Permission
from ..email import send_email


@main.route('/admin')
@login_required
@admin_required
def for_admins_only():  # view function
    return "For Administrators"

@main.route('/moderator')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def for_moderators_only():  # view function
    return "For comment Moderators"


@main.route('/home/')
def home():  # view function
    return render_template('home.html')


@main.route('/contact/')
def contact():  # view function
    return render_template('contact.html')


@main.route('/hello/', methods=['GET', 'POST'])
def hello():  # view function
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
        form.name.data=''
        return redirect(url_for('.hello'))  # 重定向为get模式
    return render_template('hello.html', form=form, name=session.get('name'), known=session.get('known', False))

@main.route('/')
def index():
    return render_template('index.html')