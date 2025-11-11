# 示例新功能模块
# 此文件展示如何安全地添加新功能而不影响现有功能

import bpy
from bpy.props import BoolProperty
from bpy.types import Operator, Panel

# 新功能操作符类
class EXAMPLE_OT_NewOperator(Operator):
    """示例新功能操作符"""
    bl_idname = "uv.example_new_operator"
    bl_label = "示例新功能"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # 检查是否处于正确的上下文
        if context.space_data.type != 'IMAGE_EDITOR':
            self.report({'ERROR'}, "此功能只能在UV编辑器中使用")
            return {'CANCELLED'}
        
        # 检查是否有选中的UV
        if not context.selected_uv_faces:
            self.report({'WARNING'}, "请先选择UV面")
            return {'CANCELLED'}
        
        # 执行新功能的具体逻辑
        selected_count = len(context.selected_uv_faces)
        self.report({'INFO'}, f"已处理 {selected_count} 个UV面")
        
        return {'FINISHED'}

# 新功能面板类
class EXAMPLE_PT_NewPanel(Panel):
    """示例新功能面板"""
    bl_label = "示例新功能"
    bl_idname = "EXAMPLE_PT_NewPanel"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Ctools UV"
    
    # 只有在启用新功能时才显示面板
    @classmethod
    def poll(cls, context):
        return context.scene.enable_example_new_feature
    
    def draw(self, context):
        layout = self.layout
        
        # 添加操作按钮
        col = layout.column(align=True)
        col.operator(EXAMPLE_OT_NewOperator.bl_idname, text="执行示例功能")
        
        # 添加说明
        box = layout.box()
        box.label(text="这是一个示例新功能，展示如何安全地添加功能而不影响现有功能。")

# 注册函数
def register():
    # 注册操作符和面板
    bpy.utils.register_class(EXAMPLE_OT_NewOperator)
    bpy.utils.register_class(EXAMPLE_PT_NewPanel)
    
    # 添加场景属性用于控制新功能开关
    bpy.types.Scene.enable_example_new_feature = BoolProperty(
        name="启用示例新功能",
        description="启用示例新功能面板",
        default=False
    )

# 注销函数
def unregister():
    # 注销操作符和面板
    bpy.utils.unregister_class(EXAMPLE_OT_NewOperator)
    bpy.utils.unregister_class(EXAMPLE_PT_NewPanel)
    
    # 删除场景属性
    del bpy.types.Scene.enable_example_new_feature