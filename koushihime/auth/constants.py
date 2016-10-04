# -*- coding: utf-8 -*-

class Permission:
    """
    使用位域标记用户权限
    每一位表示一种权限
    """
    BLOCKED = 0
    READ = 1 << 0
    MANUAL_PUSH = 1 << 1
    ADMINISTER = 1 << 3  # unused


class Operation:
    BAN = 1
    DELETE = 2
    PUSH = 3

    @staticmethod
    def translate(operation):
        return [u'屏蔽', u'删除', u'推送'][operation - 1]
