"""
UV工具UI面板模块

包含所有UV工具的UI面板类。
"""

import bpy


# 统一UV岛尺寸面板
class UV_PT_UnifyIslandsPanel(bpy.types.Panel):
    """统一UV岛尺寸面板"""
    bl_label = "统一UV岛尺寸"
    bl_idname = "UV_PT_UnifyIslandsPanel"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "UV工具"
    
    def draw(self, context):
        layout = self.layout
        
        # 添加缩放模式选择
        layout.prop(context.scene, "uv_unify_mode", text="缩放模式")
        
        # 添加锁定比例选项
        layout.prop(context.scene, "uv_lock_aspect_ratio", text="锁定比例")
        
        # 添加按钮
        col = layout.column(align=True)
        col.operator("uv.unify_islands_width", text="统一X轴尺寸")
        col.operator("uv.unify_islands_height", text="统一Y轴尺寸")


# 放松UV岛面板
class UV_PT_RelaxIslandsPanel(bpy.types.Panel):
    """放松UV岛面板"""
    bl_label = "放松UV岛"
    bl_idname = "UV_PT_RelaxIslandsPanel"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "UV工具"
    
    def draw(self, context):
        layout = self.layout
        
        # 添加放松模式选择
        layout.prop(context.scene, "uv_relax_mode", text="放松模式")
        
        # 添加强度滑块
        layout.prop(context.scene, "uv_relax_strength", text="强度")
        
        # 添加迭代次数滑块
        layout.prop(context.scene, "uv_relax_iterations", text="迭代次数")
        
        # 添加按钮
        layout.operator("uv.relax_islands", text="放松UV岛")


# UV工具集合面板
class UV_PT_UVToolsCollection(bpy.types.Panel):
    """UV工具集合面板"""
    bl_label = "UV工具集合"
    bl_idname = "UV_PT_UVToolsCollection"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "UV工具"
    
    def draw(self, context):
        layout = self.layout
        
        # 统一UV岛尺寸部分
        box = layout.box()
        box.label(text="统一UV岛尺寸", icon='MOD_SIZE')
        
        # 添加缩放模式选择
        box.prop(context.scene, "uv_unify_mode", text="缩放模式")
        
        # 添加锁定比例选项
        box.prop(context.scene, "uv_lock_aspect_ratio", text="锁定比例")
        
        # 添加按钮
        col = box.column(align=True)
        col.operator("uv.unify_islands_width", text="统一X轴尺寸")
        col.operator("uv.unify_islands_height", text="统一Y轴尺寸")
        
        # 放松UV岛部分
        box = layout.box()
        box.label(text="放松UV岛", icon='MOD_SMOOTH')
        
        # 添加放松模式选择
        box.prop(context.scene, "uv_relax_mode", text="放松模式")
        
        # 添加强度滑块
        box.prop(context.scene, "uv_relax_strength", text="强度")
        
        # 添加迭代次数滑块
        box.prop(context.scene, "uv_relax_iterations", text="迭代次数")
        
        # 添加按钮
        box.operator("uv.relax_islands", text="放松UV岛")


# 注册函数
def register():
    bpy.utils.register_class(UV_PT_UnifyIslandsPanel)
    bpy.utils.register_class(UV_PT_RelaxIslandsPanel)
    bpy.utils.register_class(UV_PT_UVToolsCollection)


def unregister():
    bpy.utils.unregister_class(UV_PT_UVToolsCollection)
    bpy.utils.unregister_class(UV_PT_RelaxIslandsPanel)
    bpy.utils.unregister_class(UV_PT_UnifyIslandsPanel)