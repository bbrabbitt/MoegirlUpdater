# -*- coding:utf-8 -*-
"""设置 URL 到 View 的对应规则"""
from koushihime.auth import auth
from views import Login, Logout


auth.add_url_rule('/login', view_func=Login.as_view('login'))
auth.add_url_rule('/logout', view_func=Logout.as_view('logout'))
