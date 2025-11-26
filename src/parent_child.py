# -*- coding: utf-8 -*-
# @Time    : 2024/6/25 0:19
# @Author  : Yuling Hou
# @File    : parent_child.py
# @Software: PyCharm
class Parent:
    def __init__(self, parent_var, *args, **kwargs):
        self.parent_var = parent_var
        self.extra_var = kwargs.get('extra_var', None)  # 示例获取额外的关键字参数
        print(f"Parent initialized with {self.parent_var}")
        if self.extra_var is not None:
            print(f"Received extra_var: {self.extra_var}")

class Child(Parent):
    def __init__(self, parent_var, child_var, **kwargs):
        super().__init__(parent_var, **kwargs)  # 将额外的关键字参数传递给父类的 __init__() 方法
        self.child_var = child_var
        print(f"Child initialized with {self.parent_var} and {self.child_var}")

# 示例用法
parent_obj = Parent("Hello")
child_obj = Child("World", 42, extra_var="Extra Value")

# 输出：
# Parent initialized with Hello
# Parent initialized with World
# Received extra_var: Extra Value
# Child initialized with World and 42

print(parent_obj.parent_var)  # 输出: Hello
print(child_obj.parent_var)   # 输出: World
print(child_obj.child_var)    # 输出: 42
