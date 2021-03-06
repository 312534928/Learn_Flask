'''
装饰器：使视图函数只对某些具有特定权限的用户开放
'''
from functools import wraps
from flask import abort, redirect, url_for
from flask.ext.login import current_user
from .models import Permission


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def admin_required(f):
    return permission_required(Permission.ADMINISTER)(f)


def confirmed_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.confirmed:
                return redirect(url_for('auth.unconfirmed'))
            return f(*args, **kwargs)

        return decorated_function


