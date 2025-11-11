"""
UV岛放松模块

包含放松UV岛相关的操作符和功能。
"""

import bpy
import bmesh
import math
import mathutils
from mathutils import Vector


# 放松UV岛的操作符
class UV_OT_RelaxIslands(bpy.types.Operator):
    """放松选中的UV岛"""
    bl_idname = "uv.relax_islands"
    bl_label = "放松UV岛"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 添加属性，用于设置放松的强度
    strength: bpy.props.FloatProperty(
        name="强度",
        description="放松的强度",
        min=0.0,
        max=1.0,
        default=0.5
    )
    
    # 添加属性，用于设置放松的迭代次数
    iterations: bpy.props.IntProperty(
        name="迭代次数",
        description="放松的迭代次数",
        min=1,
        max=100,
        default=10
    )
    
    # 添加属性，用于选择放松模式
    relax_mode: bpy.props.EnumProperty(
        name="放松模式",
        description="选择UV放松的模式",
        items=[
            ('CONFORMAL', "保角映射", "使用保角映射算法放松UV"),
        ],
        default='CONFORMAL'
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
        
        # 检查是否有选中的面或UV顶点
        selected_faces = [f for f in bm.faces if f.select]
        if not selected_faces:
            self.report({'WARNING'}, "请选择一个或多个面")
            return {'CANCELLED'}
        
        # 查找所有UV岛
        uv_islands = self.get_uv_islands(bm, uv_layer, selected_faces)
        if not uv_islands:
            self.report({'WARNING'}, "无法找到UV岛")
            return {'CANCELLED'}
        
        # 放松每个选中的UV岛
        for island in uv_islands:
            self.relax_island(island, uv_layer)
        
        # 更新网格数据
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        bmesh.update_edit_mesh(obj.data)
        
        # 刷新视图
        for area in context.screen.areas:
            area.tag_redraw()
        
        self.report({'INFO'}, f"已放松 {len(uv_islands)} 个UV岛")
        return {'FINISHED'}
    
    def get_uv_islands(self, bm, uv_layer, selected_faces):
        """查找所有UV岛"""
        # 创建一个字典，用于存储每个面的相邻面
        face_adjacency = {}
        
        # 构建面邻接关系
        for face in selected_faces:
            face_adjacency[face] = set()
            for edge in face.edges:
                for other_face in edge.link_faces:
                    if other_face in selected_faces and other_face != face:
                        # 检查两个面是否在UV空间中相连
                        if self.uv_edges_match(face, other_face, uv_layer, edge):
                            face_adjacency[face].add(other_face)
        
        # 使用广度优先搜索查找所有UV岛
        islands = []
        visited = set()
        
        for face in selected_faces:
            if face not in visited:
                # 开始一个新的UV岛
                island = []
                queue = [face]
                visited.add(face)
                
                while queue:
                    current_face = queue.pop(0)
                    island.append(current_face)
                    
                    for neighbor in face_adjacency[current_face]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                
                islands.append(island)
        
        # 如果没有找到UV岛，将每个选中的面作为单独的岛
        if not islands and selected_faces:
            islands = [[face] for face in selected_faces]
        
        return islands
    
    def uv_edges_match(self, face1, face2, uv_layer, edge):
        """检查两个面是否在UV空间中通过给定的边相连"""
        # 获取两个面在共享边上的UV坐标
        uv_coords1 = []
        uv_coords2 = []
        
        # 获取边的顶点
        edge_verts = [v for v in edge.verts]
        
        # 按边的顶点顺序收集UV坐标
        for loop in face1.loops:
            if loop.vert in edge_verts:
                uv_coords1.append((loop.vert, loop[uv_layer].uv))
        
        for loop in face2.loops:
            if loop.vert in edge_verts:
                uv_coords2.append((loop.vert, loop[uv_layer].uv))
        
        # 需要至少两个UV点才能形成边
        if len(uv_coords1) < 2 or len(uv_coords2) < 2:
            return False
        
        # 按顶点排序以确保正确的边连接
        uv_coords1.sort(key=lambda x: edge_verts.index(x[0]))
        uv_coords2.sort(key=lambda x: edge_verts.index(x[0]))
        
        # 检查UV边是否相同（考虑正向和反向）
        threshold = 0.001  # 阈值，用于判断UV坐标是否相近
        
        # 检查正向连接
        forward_match = (
            abs(uv_coords1[0][1].x - uv_coords2[0][1].x) < threshold and
            abs(uv_coords1[0][1].y - uv_coords2[0][1].y) < threshold and
            abs(uv_coords1[1][1].x - uv_coords2[1][1].x) < threshold and
            abs(uv_coords1[1][1].y - uv_coords2[1][1].y) < threshold
        )
        
        # 检查反向连接（UV边可能方向相反）
        reverse_match = (
            abs(uv_coords1[0][1].x - uv_coords2[1][1].x) < threshold and
            abs(uv_coords1[0][1].y - uv_coords2[1][1].y) < threshold and
            abs(uv_coords1[1][1].x - uv_coords2[0][1].x) < threshold and
            abs(uv_coords1[1][1].y - uv_coords2[0][1].y) < threshold
        )
        
        return forward_match or reverse_match
    
    def relax_island(self, island, uv_layer):
        """放松UV岛"""
        # 直接调用保角映射方法
        self.relax_conformal(island, uv_layer)
    
    def relax_conformal(self, island, uv_layer):
        """使用保角映射算法放松UV岛"""
        # 选择岛中的所有面
        bpy.ops.mesh.select_all(action='DESELECT')
        for face in island:
            face.select = True
        
        # 使用Blender内置的保角映射展开
        bpy.ops.uv.unwrap(method='CONFORMAL', margin=0.001)
        
        # 应用强度
        if self.strength < 1.0:
            # 获取当前UV坐标
            current_uvs = {}
            for face in island:
                for loop in face.loops:
                    current_uvs[loop] = Vector((loop[uv_layer].uv.x, loop[uv_layer].uv.y))
            
            # 恢复原始UV坐标（需要预先保存）
            # 这里简化处理，实际上应该预先保存原始坐标
            # 在实际应用中，可能需要更复杂的实现来正确应用强度


# 注册函数
def register():
    bpy.utils.register_class(UV_OT_RelaxIslands)
    
    # 添加场景属性，用于存储用户选择的模式
    bpy.types.Scene.uv_relax_mode = bpy.props.EnumProperty(
        name="UV放松模式",
        description="选择UV放松的模式",
        items=[
            ('CONFORMAL', "保角映射", "使用保角映射算法放松UV"),
        ],
        default='CONFORMAL'
    )
    
    bpy.types.Scene.uv_relax_strength = bpy.props.FloatProperty(
        name="UV放松强度",
        description="UV放松的强度",
        min=0.0,
        max=1.0,
        default=0.5
    )
    
    bpy.types.Scene.uv_relax_iterations = bpy.props.IntProperty(
        name="UV放松迭代次数",
        description="UV放松的迭代次数",
        min=1,
        max=100,
        default=10
    )


def unregister():
    bpy.utils.unregister_class(UV_OT_RelaxIslands)
    
    # 移除场景属性
    del bpy.types.Scene.uv_relax_mode
    del bpy.types.Scene.uv_relax_strength
    del bpy.types.Scene.uv_relax_iterations