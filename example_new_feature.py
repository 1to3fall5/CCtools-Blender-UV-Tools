# 示例新功能模块
# 此文件展示如何安全地添加新功能而不影响现有功能

import bpy
import bmesh

# 新功能开关
def is_new_feature_enabled(context):
    """检查是否启用了新功能"""
    return hasattr(context.scene, 'ctools_enable_new_feature') and context.scene.ctools_enable_new_feature

# 示例新功能类
class UV_OT_ExampleNewFeature(bpy.types.Operator):
    """示例新功能操作符"""
    bl_idname = "uv.example_new_feature"
    bl_label = "示例新功能"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 功能描述
    bl_description = "这是一个示例新功能，展示如何安全地添加功能"
    
    def execute(self, context):
        # 检查功能是否启用
        if not is_new_feature_enabled(context):
            self.report({'WARNING'}, "此功能当前未启用，请在设置中启用")
            return {'CANCELLED'}
        
        # 获取当前活动的UV编辑图像编辑器
        if context.area.type != 'IMAGE_EDITOR':
            self.report({'WARNING'}, "请在UV编辑器中使用此工具")
            return {'CANCELLED'}
        
        # 获取当前选中的对象
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "请选择一个网格对象")
            return {'CANCELLED'}
        
        # 这里实现新功能的具体逻辑
        # ...
        
        self.report({'INFO'}, "示例新功能执行完成")
        return {'FINISHED'}

# 新功能面板类
class UV_PT_ExampleNewFeaturePanel(bpy.types.Panel):
    """示例新功能面板"""
    bl_label = "示例新功能"
    bl_idname = "UV_PT_example_new_feature_panel"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Ctools UV"
    
    # 只有启用新功能时才显示面板
    @classmethod
    def poll(cls, context):
        return is_new_feature_enabled(context)
    
    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label(text="示例新功能")
        box.operator(UV_OT_ExampleNewFeature.bl_idname)

# 注册和注销函数
def register():
    # 注册新功能类
    bpy.utils.register_class(UV_OT_ExampleNewFeature)
    bpy.utils.register_class(UV_PT_ExampleNewFeaturePanel)
    
    # 添加新功能开关属性
    if not hasattr(bpy.types.Scene, 'ctools_enable_new_feature'):
        bpy.types.Scene.ctools_enable_new_feature = bpy.props.BoolProperty(
            name="启用示例新功能",
            description="启用实验性的示例新功能",
            default=False
        )

def unregister():
    # 注销新功能类
    bpy.utils.unregister_class(UV_PT_ExampleNewFeaturePanel)
    bpy.utils.unregister_class(UV_OT_ExampleNewFeature)
    
    # 移除新功能开关属性
    if hasattr(bpy.types.Scene, 'ctools_enable_new_feature'):
        del bpy.types.Scene.ctools_enable_new_feature