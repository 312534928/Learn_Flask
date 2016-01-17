from . import db


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
