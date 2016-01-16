import os
from flask import Flask, render_template, session, redirect, url_for, flash
from flask.ext.script import Manager
from flask.ext.bootstrap import Bootstrap
from flask.ext.wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import Required
from flask.ext.moment import Moment
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Shell
from flask.ext.migrate import Migrate, MigrateCommand
from datetime import datetime

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')  # 程序使用的数据库地址
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True  # 每次请求结束后都会自动提交数据库中的变动

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Role(db.Model):  # 模型表示程序使用的持久化实体
    __tablename__ = 'roles'  # 数据库中使用的表名
    id = db.Column(db.Integer, primary_key=True)  # 主键
    name = db.Column(db.String(64), unique=True)  # 不允许重复
    # users为面向对象视角，返回与角色相关联的用户列表
    users = db.relationship('User', backref='role', lazy='dynamic')  # 第一个参数为模型 第二个参数为方向引用  第三个不加载记录，但提供加载记录的查询

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    # role_id是外键
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username


class NameForm(Form):
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)


manager.add_command("shell", Shell(make_context=make_shell_context()))
manager.add_command('db', MigrateCommand)  # 数据库迁移


@app.route('/', methods=['GET', 'POST'])
def index():  # view function
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is not None:
            user = User(username=form.name.data)
            db.session.add(user)
            session['known'] = False
        else:
            session['known'] = True
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('index'))  # 重定向为get模式
    return render_template('index.html', form=form, name=session.get('name'), known=session.get('known', False))


@app.route('/user/<name>')
def user(name):  # view function
    return render_template('user.html', username=name)


@app.route('/home/')
def home():  # view function
    return render_template('home.html')


@app.route('/contact/')
def contact():  # view function
    return render_template('contact.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    manager.run()
