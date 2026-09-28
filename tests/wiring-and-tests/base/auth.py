from functools import wraps

from flask import abort, g


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not getattr(g, "user", None) or not g.user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapper
