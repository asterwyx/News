# -*- coding: UTF-8 -*-
# 这个文件是模块主体，提供各种工具函数
import re
from pymysql import *
import settings
import json


class DBConnection(object):
    def __init__(self, host, port, user, passwd, database, charset):
        self.conn = Connect(host=host, port=port, user=user, passwd=passwd, db=database, charset=charset)
        self.cursor = self.conn.cursor(cursors.DictCursor)


# 全局数据连接变量用于配置
set_db = DBConnection(host=settings.setting_dict['host'], port=settings.setting_dict['port'],
                      user=settings.setting_dict['username'], passwd=settings.setting_dict['password'],
                      database=settings.setting_dict['database'], charset=settings.setting_dict['charset'])


# 用来从数据库读取已经存在的表建立类的函数，从数据库自动映射，这个函数采用增量映射，只会更新修改过的表
def generate_string_by_field_desc(field_desc):
    field_string = ""
    field_string += "    %s = " % field_desc['Field']
    # 由于时间问题，目前只支持三种数据类型的映射
    if field_desc['Type'] == "bigint(20)":
        field_string += "IntegerField("
    elif field_desc['Type'] == "double":
        field_string += "DoubleField("
    elif field_desc['Type'].startswith("varchar"):
        field_string += "StringField("
    else:
        pass
    field_string += "name=\"%s\", " % field_desc['Field']
    if field_desc['Null'] == "NO":
        field_string += "null=False, "
    if field_desc['Default'] is not None:
        field_string += "default=%s, " % field_desc['Default']
    if field_desc['Key'] == "PRI":
        field_string += "primary=True, "
    elif field_desc['Key'] == "MUL":
        field_string += "foreign=True, "
    else:
        pass
    if field_desc['Extra'] != "":
        field_string += "auto_increment=True"
    field_string += ")\n"
    return field_string


def generate_string_by_create_desc(table_name, field_list):
    string = ""
    # 根据表名写出类名，使用'_'分割，首字母大写
    name_list = re.split(r"_", table_name)
    new_name_list = []
    for word in name_list:
        new_name_list.append(word.capitalize())
    class_name = "".join(new_name_list)

    string += "class %s(Model):\n" % class_name
    string += "    __table__ = \"%s\"\n" % table_name
    for field in field_list:
        string += generate_string_by_field_desc(field)
    # string += "\n"
    return string


def map_from_database():
    table_desc_list = []
    sql = "SHOW TABLES;"
    set_db.cursor.execute(sql)
    # print("这是描述的内容: %s" % set_db.cursor.description)
    # description中是一个元组，包含这个查询结果的各项信息
    field_name = set_db.cursor.description[0][0]  # 表名的字段名
    # print(field_name)
    results = set_db.cursor.fetchall()
    # print(results)
    # 调试用
    for row in results:
        t_name = row[field_name]
        # print(t_name)
    try:
        # 因为一般的代码文件都不是很大，所以这里选择直接读取整个文件，这样便于做插入
        with open(file=settings.model_path, mode='rt', encoding='utf8') as model_file:
            content = model_file.readlines()
        with open(file=settings.model_structure_path, mode='rt', encoding='utf8') as model_structure_file:
            model_structure = json.load(model_structure_file)
        table_desc_list = model_structure['structure']
        for row in results:
            t_name = row[field_name]
            sql = "SHOW CREATE TABLE %s;" % t_name
            set_db.cursor.execute(sql)
            structure = set_db.cursor.fetchone()
            # print(structure)
            sql = "DESC %s" % t_name
            set_db.cursor.execute(sql)
            desc = set_db.cursor.fetchall()
            # print(desc)
            exist = False
            for i in range(len(table_desc_list)):
                if structure['Table'] == table_desc_list[i]['name']:
                    exist = True
                    if structure['Create Table'] == table_desc_list[i]['create']:
                        break  # 跳出该表的新鲜度对比循环，且不做任何更改
                    else:
                        table_desc_list[i]['create'] = structure['Create Table']  # 更新表的结构
                        table_desc_list[i]['desc'] = desc
                        # 重新生成类
                        start_cursor = 0
                        # 找到model.py文件中对应的类的定义的开头
                        for j in range(0, table_desc_list[i]['serial']):
                            while True:
                                sentence = content[start_cursor]
                                start_cursor += 1
                                if not sentence or sentence.startswith("# start"):
                                    break
                        # 现在文件指针指向类的定义的开头, 找到类的结尾
                        end_cursor = start_cursor
                        while not content[end_cursor].startswith("# end"):
                            end_cursor += 1
                        class_str = generate_string_by_create_desc(table_desc_list[i]['name'], table_desc_list[i]['desc'])
                        content.insert(start_cursor, class_str)   # 插入到原本的开头
                        # 删除原来的内容，重新拼接，注意，因为新插入了一行，所以后面的索引全部加1，也即现在end的位置为end_cursor + 1
                        new_content = content[:start_cursor + 1] + content[end_cursor + 1:]
                        contents = "".join(new_content)
                        with open(file=settings.model_path, mode='wt', encoding='utf8') as model_file:
                            model_file.write(contents)
                        break
            if not exist:
                # 生成新的类，并且直接append原文件的后面
                class_str = generate_string_by_create_desc(structure['Table'], desc)
                with open(file=settings.model_path, mode='a+', encoding='utf8') as model_file:
                    model_file.write("\n\n# start\n")
                    model_file.write(class_str)
                    model_file.write("# end\n")
                new_table = {'name': structure['Table'], 'create': structure['Create Table'], 'serial': len(table_desc_list) + 1, 'desc': desc, }
                table_desc_list.append(new_table)  # 更新记录文件
    except FileNotFoundError:
        return None
    finally:
        with open(file=settings.model_structure_path, mode='wt', encoding='utf8') as model_structure_file:
            if table_desc_list is not []:
                model_structure['structure'] = table_desc_list
            json.dump(model_structure, model_structure_file)


# 将model.py文件中的类映射到数据库，同样采用增量映射
def map_to_database():
    pass

# 为了将类和数据库中的表进行比较，还需要创建一个文件储存类形成的表的结构和model.py同步更新
