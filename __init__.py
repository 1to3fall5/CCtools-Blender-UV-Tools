# Blender插件入口文件
bl_info = {
    "name": "Ctools",
    "author": "Your Name",
    "version": (1, 3, 0),  # 更新版本号
    "blender": (4, 5, 0),
    "location": "Image Editor > Sidebar > Ctools UV",
    "description": "UV编辑工具集，包括统一尺寸和放松UV岛功能",
    "warning": "",
    "doc_url": "",
    "category": "UV",
}

import bpy

# 导入各个模块
from . import uv_tools

# 尝试导入新功能模块（可选）
try:
    from . import example_new_feature
    NEW_FEATURE_AVAILABLE = True
except ImportError:
    NEW_FEATURE_AVAILABLE = False

# 注册和注销函数
def register():
    # 注册核心模块
    uv_tools.register()
    
    # 注册新功能模块（如果可用）
    if NEW_FEATURE_AVAILABLE:
        example_new_feature.register()

def unregister():
    # 注销核心模块
    uv_tools.unregister()
    
    # 注销新功能模块（如果可用）
    if NEW_FEATURE_AVAILABLE:
        example_new_feature.unregister()

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