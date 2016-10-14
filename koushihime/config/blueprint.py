# -*- coding:utf-8 -*-
from koushihime.main import main as main_blueprint
from koushihime.auth import auth as auth_blueprint


def regist(app):
    """
    为指定的 app:Flask 注册蓝图
    """
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
