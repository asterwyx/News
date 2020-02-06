# -*- coding: UTF-8 -*-
from orm_util import *

# 用metaclass实现一个ORM框架
# 最基本的字段类，负责保存数据库中的字段名和字段类型
db = DBConnection(host=settings.setting_dict['host'], port=settings.setting_dict['port'],
                  user=settings.setting_dict['username'], passwd=settings.setting_dict['password'],
                  database=settings.setting_dict['database'], charset=settings.setting_dict['charset'])


class Field(object):
    def __init__(self, name, column_type, null, default, primary, foreign, auto_increment):
        self.name = name
        self.column_type = column_type
        self.null = null
        self.default = default
        self.primary = primary
        self.foreign = foreign
        self.auto_increment = auto_increment
        self.value = None

    def __str__(self):
        return '<%s:%s>' % (self.__class__.__name__, self.name)

    # 让子类重写的方法
    def print_value(self):
        pass


# 继承自字段类的字符串字段类，具有字符串类型的字段
class StringField(Field):
    def __init__(self, name, null=True, default=None, primary=False, foreign=False, auto_increment=False):
        super(StringField, self).__init__(name, "VARCHAR(100)", null, default, primary, foreign, auto_increment)

    def print_value(self):
        if self.value:
            return "\"%s\"" % self.value
        else:
            return None


# 继承自字段类的整数型字段类，具有整数类型的字段
class IntegerField(Field):
    def __init__(self, name, null=True, default=None, primary=False, foreign=False, auto_increment=False):
        super(IntegerField, self).__init__(name, "BIGINT", null, default, primary, foreign, auto_increment)

    def print_value(self):
        if self.value:
            return "%d" % self.value
        else:
            return None


class DoubleField(Field):
    def __init__(self, name, null=True, default=None, primary=False, foreign=False, auto_increment=False):
        super(DoubleField, self).__init__(name, "DOUBLE", null, default, primary, foreign, auto_increment)

    def print_value(self):
        if self.value:
            return "%f" % self.value
        else:
            return None


# 元类
class ModelMetaclass(type):
    def __new__(mcs, name, bases, attrs):
        if name == 'Model':
            return type.__new__(mcs, name, bases, attrs)
        print('Found model: %s' % name)
        mappings = dict()
        for k, v in attrs.items():
            # print("\"%s\": %s" % (k, v))
            if isinstance(v, Field):
                print('Found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
        for k in mappings.keys():
            attrs.pop(k)
        attrs['__mappings__'] = mappings  # 保存属性和列的映射关系
        return type.__new__(mcs, name, bases, attrs)


class Model(dict, metaclass=ModelMetaclass):
    def __init__(self, **kw):
        super(Model, self).__init__(**kw)
        for k in self.__mappings__.keys():
            self.__mappings__[k].value = self[k]

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute %s" % key)

    def __setattr__(self, key, value):
        self[key] = value
        self.__mappings__[key].value = value

    # 新建对象的时候初次存储使用的函数，因为主键可能是自增的，所以主键是不准确的，但是参数一定要传
    def save(self):
        fields = []
        params = []
        args = []
        for k, v in self.__mappings__.items():
            if k == "id":
                if v.value is None:
                    continue
            else:
                fields.append(v.name)
                params.append(v.print_value())
                args.append(getattr(self, k, None))
        sql = "INSERT INTO %s (%s) VALUES (%s);" % (self.__table__, ", ".join(fields), ", ".join(params))
        # print('SQL: %s' % sql)
        # print('ARGS: %s' % str(args))
        try:
            db.cursor.execute(sql)
            db.conn.commit()
            # print("操作成功")
        except Error:
            db.conn.rollback()
            print("操作失败")

    def get_by_id(self, record_id):
        sql = "SELECT * FROM %s WHERE %s=%s;" % (self.__table__, self.__mappings__['id'].name, record_id)
        try:
            db.cursor.execute(sql)
            db.conn.commit()
            # print("操作成功")
        except Error:
            db.conn.rollback()
            print("操作失败")
        result = db.cursor.fetchone()
        # print(result)
        param_list = []
        for k, v in result.items():
            # print("%s=%s" % (k, v))
            param_list.append("%s=\"%s\"" % (k, v) if isinstance(v, str) else "%s=%s" % (k, v))
        param_str = ", ".join(param_list)
        eval_str = self.__class__ .__name__ + "(" + param_str + ")"
        return eval(eval_str)

    def get_all(self):
        sql = "SELECT * FROM %s;" % self.__table__
        results = []
        try:
            db.cursor.execute(sql)
            db.conn.commit()
            # print("操作成功")
        except Error:
            db.conn.rollback()
            print("操作失败")
        results = db.cursor.fetchall()
        object_list = []
        if results:
            # print("查询结果:")
            # print(results)
            for result in results:
                param_list = []
                for k, v in result.items():
                    # print("%s=%s" % (k, v))
                    param_list.append("%s=\"%s\"" % (k, v) if isinstance(v, str) else "%s=%s" % (k, v))
                param_str = ", ".join(param_list)
                eval_str = self.__class__.__name__ + "(" + param_str + ")"
                object_list.append(eval(eval_str))
        return object_list

    def update_self(self):
        field_dict = {}
        param_list = []
        args = []
        id_field = None
        for k, v in self.__mappings__.items():
            if k == "id":
                id_field = v
            else:
                field_dict[v.name] = v.print_value()
            args.append(getattr(self, k, None))
        for k, v in field_dict.items():
            param_list.append("%s=%s" % (k, v))
        set_str = ", ".join(param_list)
        sql = "UPDATE %s SET %s WHERE %s=%s;" % (self.__table__, set_str, id_field.name, id_field.print_value())
        # print('SQL: %s' % sql)
        # print('ARGS: %s' % str(args))
        try:
            db.cursor.execute(sql)
            db.conn.commit()
            # print("操作成功")
        except Error:
            db.conn.rollback()
            print("操作失败")

    def delete_self(self):
        sql = "DELETE FROM %s WHERE %s=%s;" % (self.__table__, self.__mappings__['id'].name, self.__mappings__['id'].print_value())
        try:
            db.cursor.execute(sql)
            db.conn.commit()
            # print("操作成功")
        except Error:
            db.conn.rollback()
            print("操作失败")
# 为了方便对类进行修改，在类的开头和结尾使用特殊注释，不要修改这些注释和它们的位置


# start
class SinaNews(Model):
    __table__ = "sina_news"
    id = IntegerField(name="id", null=False, primary=True, auto_increment=True)
    title = StringField(name="title", null=False)
    date = StringField(name="date", null=False)
    link = StringField(name="link", null=False)
# end
