# -*- coding: utf-8 -*-

from datetime import datetime
from flask.ext.login import UserMixin
from constants import Permission
from koushihime import db, login_manager
from koushihime.utils import CRUDMixin
from werkzeug.security import generate_password_hash, check_password_hash


@login_manager.user_loader
def load_user(user_id):
    """
    flask-login 要求完成的方法
    """
    return User.query.get(int(user_id))


class Role(db.Model, CRUDMixin):
    """
    权限组
    
    @tablename roles
    @column id:Integer              Identifier, primary_key
    @column name:String(64)         name, unique
    @column permissions:Integer     permissions
    
    @attrib users:relationship->User.role
    """
    __tablename__ = 'roles'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64), unique=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def init_roles():
        """
        初始化预定义的各组入数据库
        
        @returns None
        """
        roles = {
            'Blocked': Permission.BLOCKED,
            'Watchman': Permission.READ | Permission.MANUAL_PUSH,
            'Administrator': 0xff
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r]
            db.session.add(role)
        db.session.commit()


class User(UserMixin, db.Model, CRUDMixin):
    """
    用户
    
    @tablename users
    @column id:Integer                  ID；主键
    @column email:String(64)            邮件；唯一，不可为空
    @column username:String(64)         用户名；唯一，索引，不可为空
    @column role_id:Integer             ForeignKey=roles.id
    @column password_hash:String(128)   werkzeug password hash
    @column aboutme:Text                关于我
    @column member_since:DateTime       注册日期；default=utcnow
    @column last_seen:DateTime          最后出现；default=utcnow
    @column deleted:Boolean             是否蒸发
    
    @attrib push_records:relationship->UserOperation.handlers
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(64), unique=True, nullable=False)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    push_records = db.relationship('UserOperation', backref='handlers', lazy='dynamic')
    password_hash = db.Column(db.String(128))
    aboutme = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    deleted = db.Column(db.Boolean(), default=False)

    @property
    def password(self):
        """
        告诉你不能设置密码
        """
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        """
        设置密码，存储 hash
        
        @returns None
        """
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """
        验证提供的密码是否符合 hash
        
        @returns bool
        """
        return check_password_hash(self.password_hash, password)

    def change_password(self, new_password):
        """
        设置密码，调用 password 的 setter
        
        @returns True
        """
        self.password = new_password
        db.session.add(self)
        return True

    def change_profile(self, new_email=None, new_aboutme=None):
        """
        设置个人信息：
        
        @param new_email:   <=None, nop> 新邮箱
        @param new_aboutme: <=None, nop> 新“关于”
        
        @returns True
        """
        if new_email:
            self.email = new_email
        if new_aboutme:
            self.aboutme = new_aboutme
        db.session.add(self)
        return True

    def can(self, permissions):
        """
        @returns bool 权限位设定与否
        """
        return self.role is not None and \
            (self.role.permissions & permissions) == permissions

    @property
    def is_blocked(self):
        """
        @returns bool 是否被屏蔽
        """
        return self.role.permissions == Permission.BLOCKED

    @property
    def is_administrator(self):
        """
        @returns bool 是否管理员
        """
        return self.can(Permission.ADMINISTER)


class UserOperation(db.Model, CRUDMixin):
    """
    用户进行的操作
    
    @tablename user_operations
    @column id:Integer ID；主键
    @column operation:SmallInteger 操作号
        @see auth/constants.py:translate(operation)
    @column title:Text 标题党的乐园
    @column created_time:DateTime 搞事时间
    """
    __tablename__ = 'user_operations'

    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    operation = db.Column(db.SmallInteger())
    title = db.Column(db.Text())
    created_time = db.Column(db.DateTime(), default=datetime.utcnow)
