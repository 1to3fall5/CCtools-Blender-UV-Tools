# Blender插件入口文件
bl_info = {
    "name": "Ctools",
    "author": "Your Name",
    "version": (1, 0, 0),
    "blender": (4, 5, 0),
    "location": "Image Editor > Sidebar > Ctools UV",
    "description": "统一UV岛尺寸工具集",
    "warning": "",
    "doc_url": "",
    "category": "UV",
}

import bpy

# 导入各个模块
from . import uv_tools

# 注册和注销函数
def register():
    # 注册各个模块
    uv_tools.register()

def unregister():
    # 注销各个模块
    uv_tools.unregister()

# 当作为脚本直接运行时
def main():
    # 先尝试注销以避免冲突
    try:
        unregister()
    except:
        pass
    # 然后注册
    register()

if __name__ == "__main__":
    main()