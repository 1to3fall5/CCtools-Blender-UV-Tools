# UV工具模块
# 包含统一UV岛尺寸的核心功能

import bpy
from bpy.props import BoolProperty, FloatProperty
from bpy.types import Operator, Panel

# 统一宽度操作符类
class UV_OT_UnifyIslandsWidth(Operator):
    """统一所有选中UV岛的宽度"""
    bl_idname = "uv.unify_islands_width"
    bl_label = "统一宽度"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 添加锁定比例属性，默认为False
    lock_aspect_ratio: BoolProperty(
        name="锁定比例",
        description="在缩放时保持UV岛的宽高比",
        default=False
    )
    
    def execute(self, context):
        # 检查是否处于正确的上下文
        if context.space_data.type != 'IMAGE_EDITOR':
            self.report({'ERROR'}, "此功能只能在UV编辑器中使用")
            return {'CANCELLED'}
        
        # 检查是否有选中的UV
        if not context.selected_uv_faces:
            self.report({'WARNING'}, "请先选择UV面")
            return {'CANCELLED'}
        
        # 获取所有选中的UV岛
        selected_islands = []
        for face in context.selected_uv_faces:
            island = face.uv_island
            if island not in selected_islands:
                selected_islands.append(island)
        
        if not selected_islands:
            self.report({'WARNING'}, "未找到UV岛")
            return {'CANCELLED'}
        
        # 计算目标宽度（使用第一个岛的宽度）
        target_width = selected_islands[0].bounds[2] - selected_islands[0].bounds[0]
        
        # 统一所有岛的宽度
        for island in selected_islands:
            current_width = island.bounds[2] - island.bounds[0]
            if current_width <= 0:
                continue
                
            # 计算缩放比例
            scale_factor = target_width / current_width
            
            # 计算缩放中心（使用岛的中心）
            center_x = (island.bounds[0] + island.bounds[2]) / 2
            center_y = (island.bounds[1] + island.bounds[3]) / 2
            
            # 应用缩放
            for face in island.uv_faces:
                for loop in face.loops:
                    uv = loop.uv
                    # 计算相对于中心的坐标
                    rel_x = uv.x - center_x
                    rel_y = uv.y - center_y
                    
                    # 应用缩放
                    if self.lock_aspect_ratio:
                        uv.x = center_x + rel_x * scale_factor
                        uv.y = center_y + rel_y * scale_factor
                    else:
                        uv.x = center_x + rel_x * scale_factor
                        # 不改变y坐标
        
        self.report({'INFO'}, f"已统一 {len(selected_islands)} 个UV岛的宽度")
        return {'FINISHED'}

# 统一高度操作符类
class UV_OT_UnifyIslandsHeight(Operator):
    """统一所有选中UV岛的高度"""
    bl_idname = "uv.unify_islands_height"
    bl_label = "统一高度"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 添加锁定比例属性，默认为False
    lock_aspect_ratio: BoolProperty(
        name="锁定比例",
        description="在缩放时保持UV岛的宽高比",
        default=False
    )
    
    def execute(self, context):
        # 检查是否处于正确的上下文
        if context.space_data.type != 'IMAGE_EDITOR':
            self.report({'ERROR'}, "此功能只能在UV编辑器中使用")
            return {'CANCELLED'}
        
        # 检查是否有选中的UV
        if not context.selected_uv_faces:
            self.report({'WARNING'}, "请先选择UV面")
            return {'CANCELLED'}
        
        # 获取所有选中的UV岛
        selected_islands = []
        for face in context.selected_uv_faces:
            island = face.uv_island
            if island not in selected_islands:
                selected_islands.append(island)
        
        if not selected_islands:
            self.report({'WARNING'}, "未找到UV岛")
            return {'CANCELLED'}
        
        # 计算目标高度（使用第一个岛的高度）
        target_height = selected_islands[0].bounds[3] - selected_islands[0].bounds[1]
        
        # 统一所有岛的高度
        for island in selected_islands:
            current_height = island.bounds[3] - island.bounds[1]
            if current_height <= 0:
                continue
                
            # 计算缩放比例
            scale_factor = target_height / current_height
            
            # 计算缩放中心（使用岛的中心）
            center_x = (island.bounds[0] + island.bounds[2]) / 2
            center_y = (island.bounds[1] + island.bounds[3]) / 2
            
            # 应用缩放
            for face in island.uv_faces:
                for loop in face.loops:
                    uv = loop.uv
                    # 计算相对于中心的坐标
                    rel_x = uv.x - center_x
                    rel_y = uv.y - center_y
                    
                    # 应用缩放
                    if self.lock_aspect_ratio:
                        uv.x = center_x + rel_x * scale_factor
                        uv.y = center_y + rel_y * scale_factor
                    else:
                        # 不改变x坐标
                        uv.y = center_y + rel_y * scale_factor
        
        self.report({'INFO'}, f"已统一 {len(selected_islands)} 个UV岛的高度")
        return {'FINISHED'}

# UV工具面板类
class UV_PT_CtoolsPanel(Panel):
    """Ctools UV工具面板"""
    bl_label = "Ctools UV"
    bl_idname = "UV_PT_CtoolsPanel"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Ctools UV"
    
    def draw(self, context):
        layout = self.layout
        
        # 添加操作按钮
        col = layout.column(align=True)
        
        # 统一宽度按钮
        width_op = col.operator(UV_OT_UnifyIslandsWidth.bl_idname, text="统一宽度")
        width_op.lock_aspect_ratio = False  # 默认不锁定比例
        
        # 统一高度按钮
        height_op = col.operator(UV_OT_UnifyIslandsHeight.bl_idname, text="统一高度")
        height_op.lock_aspect_ratio = False  # 默认不锁定比例
        
        # 添加分隔线
        col.separator()
        
        # 添加锁定比例的选项
        lock_col = col.column(align=True)
        lock_width_op = lock_col.operator(UV_OT_UnifyIslandsWidth.bl_idname, text="统一宽度 (锁定比例)")
        lock_width_op.lock_aspect_ratio = True
        
        lock_height_op = lock_col.operator(UV_OT_UnifyIslandsHeight.bl_idname, text="统一高度 (锁定比例)")
        lock_height_op.lock_aspect_ratio = True
        
        # 添加说明
        box = layout.box()
        box.label(text="使用说明:")
        box.label(text="1. 选择要处理的UV岛")
        box.label(text="2. 点击相应按钮执行操作")
        box.label(text="3. 可选择是否锁定宽高比")

# 注册函数
def register():
    # 注册操作符和面板
    bpy.utils.register_class(UV_OT_UnifyIslandsWidth)
    bpy.utils.register_class(UV_OT_UnifyIslandsHeight)
    bpy.utils.register_class(UV_PT_CtoolsPanel)

# 注销函数
def unregister():
    # 注销操作符和面板
    bpy.utils.unregister_class(UV_OT_UnifyIslandsWidth)
    bpy.utils.unregister_class(UV_OT_UnifyIslandsHeight)
    bpy.utils.unregister_class(UV_PT_CtoolsPanel)