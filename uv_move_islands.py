"""
UV岛移动模块

包含移动UV岛相关的操作符和功能。
"""

import bpy
import bmesh
from mathutils import Vector
from . import uv_utils


# 移动UV岛的操作符
class UV_OT_MoveIslands(bpy.types.Operator):
    """移动选中的UV岛"""
    bl_idname = "uv.move_islands"
    bl_label = "移动UV岛"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 移动单位属性
    move_unit: bpy.props.FloatProperty(
        name="移动单位",
        description="UV岛移动的单位距离",
        default=0.1,
        min=0.001,
        max=1.0,
        precision=3
    )
    
    # 移动方向属性
    move_direction: bpy.props.EnumProperty(
        name="移动方向",
        description="选择UV岛移动的方向",
        items=[
            ('LEFT', "左", "向左移动"),
            ('RIGHT', "右", "向右移动"),
            ('DOWN', "下", "向下移动"),
            ('UP', "上", "向上移动")
        ],
        default='RIGHT'
    )
    
    def execute(self, context):
        # 获取当前活动的UV编辑图像编辑器
        if context.area.type != 'IMAGE_EDITOR':
            self.report({'WARNING'}, "请在UV编辑器中使用此工具")
            return {'CANCELLED'}
        
        # 获取当前选中的对象
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "请选择一个网格对象")
            return {'CANCELLED'}
        
        # 进入编辑模式
        if obj.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        
        # 获取BMesh数据
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.active
        
        if not uv_layer:
            self.report({'WARNING'}, "未找到UV层")
            return {'CANCELLED'}
        
        # 使用场景中的移动单位设置，而不是操作符的属性
        move_unit = context.scene.uv_move_unit
        
        # 计算移动向量
        move_vector = Vector((0, 0))
        
        if self.move_direction == 'LEFT':
            move_vector = Vector((-move_unit, 0))
        elif self.move_direction == 'RIGHT':
            move_vector = Vector((move_unit, 0))
        elif self.move_direction == 'DOWN':
            move_vector = Vector((0, -move_unit))
        elif self.move_direction == 'UP':
            move_vector = Vector((0, move_unit))
        
        # 只移动选中的UV坐标
        moved_uvs = 0
        
        # 检查是否有选中的UV点
        selected_uv_loops = []
        
        # 遍历所有面和循环，找到选中的UV点
        for face in bm.faces:
            for loop in face.loops:
                # 检查UV点是否被选中
                if loop[uv_layer].select:
                    selected_uv_loops.append(loop)
        
        if not selected_uv_loops:
            self.report({'WARNING'}, "请选择一个或多个UV点")
            return {'CANCELLED'}
        
        # 移动选中的UV点
        for loop in selected_uv_loops:
            loop[uv_layer].uv += move_vector
            moved_uvs += 1
        
        # 更新网格数据
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        bmesh.update_edit_mesh(obj.data)
        
        # 刷新视图
        for area in context.screen.areas:
            area.tag_redraw()
        
        self.report({'INFO'}, f"已移动 {moved_uvs} 个UV坐标点，移动距离: {move_unit}")
        return {'FINISHED'}


# 注册函数
def register():
    bpy.utils.register_class(UV_OT_MoveIslands)
    
    # 添加场景属性，用于存储用户设置
    bpy.types.Scene.uv_move_unit = bpy.props.FloatProperty(
        name="UV移动单位",
        description="UV岛移动的单位距离",
        default=0.1,
        min=0.001,
        max=1.0,
        precision=3
    )
    
    bpy.types.Scene.uv_move_direction = bpy.props.EnumProperty(
        name="UV移动方向",
        description="选择UV岛移动的方向",
        items=[
            ('LEFT', "左", "向左移动"),
            ('RIGHT', "右", "向右移动"),
            ('DOWN', "下", "向下移动"),
            ('UP', "上", "向上移动")
        ],
        default='RIGHT'
    )


def unregister():
    bpy.utils.unregister_class(UV_OT_MoveIslands)
    
    # 移除场景属性
    del bpy.types.Scene.uv_move_unit
    del bpy.types.Scene.uv_move_direction
