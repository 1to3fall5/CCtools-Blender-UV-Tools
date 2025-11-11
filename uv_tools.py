"""
UV工具主入口文件

导入并注册所有UV工具相关的模块。
"""

# 导入所有模块
from . import uv_unify_islands
from . import uv_relax_islands
from . import uv_panels
from . import uv_utils


# 注册函数
def register():
    # 注册所有模块
    uv_unify_islands.register()
    uv_relax_islands.register()
    uv_panels.register()
    uv_utils.register()


# 注销函数
def unregister():
    # 注销所有模块（与注册顺序相反）
    uv_utils.unregister()
    uv_panels.unregister()
    uv_relax_islands.unregister()
    uv_unify_islands.unregister()


# 添加到blender的插件信息中
bl_info = {
    "name": "UV工具",
    "author": "AI Assistant",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "UV编辑器 > 侧边栏 > UV工具",
    "description": "提供UV编辑工具，包括统一UV岛尺寸和放松UV岛功能",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "UV"
}