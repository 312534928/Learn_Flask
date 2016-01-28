from flask import current_app
import hashlib
from datetime import datetime
from flask import request
from flask.ext.login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from . import db, login_manager


class Permission:
    FOLLOW = 0x01  # 关注
    COMMENT = 0x02  # 评论
    WRITE_ARTICLES = 0x04  # 发表文章
    MODERATE_COMMENTS = 0X08  # 管理评论
    ADMINISTER = 0x80  # 管理网站


class Role(db.Model):  # 模型表示程序使用的持久化实体
    __tablename__ = 'roles'  # 数据库中使用的表名
    id = db.Column(db.Integer, primary_key=True)  # 主键
    name = db.Column(db.String(64), unique=True)  # 不允许重复
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    # users为面向对象视角，返回与角色相关联的用户列表
    users = db.relationship('User', backref='role', lazy='dynamic')  # 第一个参数为模型 第二个参数为方向引用  第三个不加载记录，但提供加载记录的查询

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.FOLLOW |
                     Permission.COMMENT, True),
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    # role_id是外键
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.BOOLEAN, default=False)

    # 用户资料
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    # avatar_hash = db.Column(db.String(32))
    Ico = db.Column(db.Integer, default='2')
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)  # 注册时间，db.Column()参数可以接受函数为参数
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)  # 最后登录时间
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
                # if self.email is not None and self.avatar_hash is None:
                #     self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):  # 过期时间
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})  # 为数据生成加密签名，然后对数据和签名进行序列化生成令牌字符串

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        # self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def can(self, permissions):
        '''
        在请求和赋予角色这两种权限之间进行位与操作。如果角色中包含清酒的所有权限位，返回True
        '''
        return self.role.permissions is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    # 刷新用户最后登录时间
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    # 头像
    # def gravatar(self, size=100, default='identicon', rating='g'):
    #     if request.is_secure:
    #         url = 'https://secure.gravatar.com/avatar'
    #     else:
    #         url = 'https://ww.gravatar.com/avatar'
    #     hash = self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()
    #     return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(url=url, hash=hash, size=size, default=default,
    #                                                                  rating=rating)

    # 头像
    def IDIco(self, size='big'):
        if self.Ico is not None:
            if size == "mid":
                url = '../static/avatar/' + str(self.Ico) + '_mid.jpg'
            elif size == "li":
                url = '../static/avatar/' + str(self.Ico) + '_li.jpg'
            else:
                url = '../static/avatar/' + str(self.Ico) + '.jpg'
            return url

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


# 用户未登录时current_user的值设为AnonymousUser
login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    @staticmethod
    def generate_fake(count=100):
        from random import seed,randint
        import forgery_py

        seed()
        user_count=User.query.count()
        for i in range(count):
            u=User.query.offset(randint(0,user_count-1)).first()
            p=Post(body=forgery_py.lorem_ipsum.sentences(randint(1,3)),
                   timestamp=forgery_py.date.date(True),
                   author=u)
            db.session.add(p)
            db.session.commit()