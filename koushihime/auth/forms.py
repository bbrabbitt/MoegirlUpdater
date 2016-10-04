# -*- coding: utf-8 -*-

from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField, validators


class LoginForm(Form):
    """
    登录表单。
    
    @attrib email:StringField     邮箱地址，长度 1-32
    @attrib password:StringField  密码，长度 6-30
    @attrib remember:BooleanField 保持登入状态
    @attrib submit:SubmitField    提交
    """
    email = StringField(u'邮箱', [validators.Required(), validators.Length(min=1, max=32), validators.Email()])
    password = PasswordField(u'密码', [validators.Required(), validators.Length(min=6, max=30)])
    remember = BooleanField(u'保持登入状态')
    submit = SubmitField(u'登入')
