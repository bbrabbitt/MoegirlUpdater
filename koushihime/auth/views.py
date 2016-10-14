# -*- coding: utf-8 -*-

from models import User
from forms import LoginForm
from flask.views import MethodView
from flask import render_template, request, flash, redirect, url_for
from flask.ext.login import login_user, login_required, logout_user


class Login(MethodView):
    """
    Login View
    
    @attrib form:LoginForm
    """
    def __init__(self):
        self.form = LoginForm

    def get(self):
        """
        GET handler.
        
        @return 一个渲染好的登录页面
        """
        return render_template('auth/login.html', form=self.form())

    def post(self):
        """
        POST handler.
        
        @post_param next 目标页面
        @return 登录成功则重定向到 next 给定的目标或主页；否则给渲染好的登录页面
        """
        form = self.form(request.form)
        if form.validate():
            email = form.email.data
            try:
                user = User.query.filter_by(email=email, deleted=False).first()
            except Exception, e:
                flash(u"程序内部错误，看见此条信息请尝试刷新或联系管理员")
                raise e
            if user is not None and user.verify_password(form.password.data):
                login_user(user, form.remember.data)
                return redirect(request.args.get('next') or url_for('main.index'))
            flash(u"用户名或密码不正确")
        return render_template('auth/login.html', form=form)


class Logout(MethodView):
    """
    退出登录
    """
    decorators = [login_required]

    def get(self):
        """
        GET handler.
        
        @return 重定向到首页
        """
        logout_user()
        flash(u"已登出")
        return redirect(url_for('main.index'))
