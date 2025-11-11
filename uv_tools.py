import bpy
import bmesh
from mathutils import Vector
from bpy.props import EnumProperty, FloatProperty, IntProperty, BoolProperty

# 基础操作符类，用于统一UV岛尺寸
class UV_OT_UnifyIslandsBase(bpy.types.Operator):
    """统一UV岛尺寸的基础操作符类"""
    bl_idname = "uv.unify_islands_base"
    bl_label = "统一UV岛尺寸基础"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 缩放模式属性
    scale_mode: EnumProperty(
        name="缩放模式",
        description="选择缩放模式",
        items=[
            ('WIDTH', "宽度", "统一宽度"),
            ('HEIGHT', "高度", "统一高度"),
        ],
        default='WIDTH'
    )
    
    def find_uv_islands(self, bm, uv_layer):
        """查找所有UV岛"""
        islands = []
        visited_faces = set()
        
        for face in bm.faces:
            if face in visited_faces:
                continue
                
            # 开始新的UV岛
            island = []
            stack = [face]
            
            while stack:
                current_face = stack.pop()
                if current_face in visited_faces:
                    continue
                    
                visited_faces.add(current_face)
                island.append(current_face)
                
                # 检查相邻面
                for edge in current_face.edges:
                    if edge.is_boundary:
                        continue
                        
                    for other_face in edge.link_faces:
                        if other_face not in visited_faces:
                            # 检查UV边是否匹配
                            uv_edge1 = [loop[uv_layer].uv for loop in edge.link_loops if loop.face == current_face]
                            uv_edge2 = [loop[uv_layer].uv for loop in edge.link_loops if loop.face == other_face]
                            
                            if len(uv_edge1) == 2 and len(uv_edge2) == 2:
                                # 检查UV边是否相同（考虑浮点精度）
                                if (abs((uv_edge1[0] - uv_edge2[0]).length) < 0.001 and 
                                    abs((uv_edge1[1] - uv_edge2[1]).length) < 0.001) or \
                                   (abs((uv_edge1[0] - uv_edge2[1]).length) < 0.001 and 
                                    abs((uv_edge1[1] - uv_edge2[0]).length) < 0.001):
                                    stack.append(other_face)
            
            if island:
                islands.append(island)
        
        return islands
    
    def get_island_bounds(self, island, uv_layer):
        """获取UV岛的边界"""
        min_u = min_v = float('inf')
        max_u = max_v = float('-inf')
        
        for face in island:
            for loop in face.loops:
                u, v = loop[uv_layer].uv
                min_u = min(min_u, u)
                max_u = max(max_u, u)
                min_v = min(min_v, v)
                max_v = max(max_v, v)
        
        return min_u, min_v, max_u, max_v
    
    def scale_island(self, island, uv_layer, scale_u, scale_v):
        """缩放UV岛"""
        # 计算UV岛中心
        min_u, min_v, max_u, max_v = self.get_island_bounds(island, uv_layer)
        center_u = (min_u + max_u) / 2
        center_v = (min_v + max_v) / 2
        
        # 缩放UV岛
        for face in island:
            for loop in face.loops:
                u, v = loop[uv_layer].uv
                # 相对于中心缩放
                loop[uv_layer].uv.x = center_u + (u - center_u) * scale_u
                loop[uv_layer].uv.y = center_v + (v - center_v) * scale_v

# 统一UV岛宽度的操作符
class UV_OT_UnifyIslandsWidth(bpy.types.Operator):
    """统一选中的UV岛宽度"""
    bl_idname = "uv.unify_islands_width"
    bl_label = "统一宽度"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 锁定比例选项
    lock_aspect: BoolProperty(
        name="锁定比例",
        description="在调整宽度时保持宽高比",
        default=False
    )
    
    def execute(self, context):
        # 获取当前对象
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "需要选择一个网格对象")
            return {'CANCELLED'}
        
        # 进入编辑模式
        bpy.ops.object.mode_set(mode='EDIT')
        
        # 获取bmesh和UV层
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()
        
        # 检查是否有选中的面
        selected_faces = [face for face in bm.faces if face.select]
        if not selected_faces:
            self.report({'WARNING'}, "没有选中的面")
            bpy.ops.object.mode_set(mode='OBJECT')
            return {'CANCELLED'}
        
        # 查找UV岛
        islands = []
        visited_faces = set()
        
        for face in selected_faces:
            if face in visited_faces:
                continue
                
            # 开始新的UV岛
            island = []
            stack = [face]
            
            while stack:
                current_face = stack.pop()
                if current_face in visited_faces:
                    continue
                    
                visited_faces.add(current_face)
                island.append(current_face)
                
                # 检查相邻面
                for edge in current_face.edges:
                    if edge.is_boundary:
                        continue
                        
                    for other_face in edge.link_faces:
                        if other_face not in visited_faces and other_face.select:
                            # 检查UV边是否匹配
                            uv_edge1 = [loop[uv_layer].uv for loop in edge.link_loops if loop.face == current_face]
                            uv_edge2 = [loop[uv_layer].uv for loop in edge.link_loops if loop.face == other_face]
                            
                            if len(uv_edge1) == 2 and len(uv_edge2) == 2:
                                # 检查UV边是否相同（考虑浮点精度）
                                if (abs((uv_edge1[0] - uv_edge2[0]).length) < 0.001 and 
                                    abs((uv_edge1[1] - uv_edge2[1]).length) < 0.001) or \
                                   (abs((uv_edge1[0] - uv_edge2[1]).length) < 0.001 and 
                                    abs((uv_edge1[1] - uv_edge2[0]).length) < 0.001):
                                    stack.append(other_face)
            
            if island:
                islands.append(island)
        
        if not islands:
            self.report({'WARNING'}, "没有找到选中的UV岛")
            bpy.ops.object.mode_set(mode='OBJECT')
            return {'CANCELLED'}
        
        # 计算目标宽度（使用第一个UV岛的宽度）
        target_min_u, _, target_max_u, _ = self.get_island_bounds(islands[0], uv_layer)
        target_width = target_max_u - target_min_u
        
        # 统一所有UV岛的宽度
        for island in islands:
            min_u, min_v, max_u, max_v = self.get_island_bounds(island, uv_layer)
            current_width = max_u - min_u
            
            if current_width > 0:
                scale_u = target_width / current_width
                
                if self.lock_aspect:
                    # 保持宽高比
                    scale_v = scale_u
                else:
                    scale_v = 1.0
                
                self.scale_island(island, uv_layer, scale_u, scale_v)
        
        # 更新网格
        bmesh.update_edit_mesh(obj.data)
        
        # 返回对象模式
        bpy.ops.object.mode_set(mode='OBJECT')
        
        self.report({'INFO'}, f"已统一{len(islands)}个UV岛的宽度")
        return {'FINISHED'}
    
    def get_island_bounds(self, island, uv_layer):
        """获取UV岛的边界"""
        min_u = min_v = float('inf')
        max_u = max_v = float('-inf')
        
        for face in island:
            for loop in face.loops:
                u, v = loop[uv_layer].uv
                min_u = min(min_u, u)
                max_u = max(max_u, u)
                min_v = min(min_v, v)
                max_v = max(max_v, v)
        
        return min_u, min_v, max_u, max_v
    
    def scale_island(self, island, uv_layer, scale_u, scale_v):
        """缩放UV岛"""
        # 计算UV岛中心
        min_u, min_v, max_u, max_v = self.get_island_bounds(island, uv_layer)
        center_u = (min_u + max_u) / 2
        center_v = (min_v + max_v) / 2
        
        # 缩放UV岛
        for face in island:
            for loop in face.loops:
                u, v = loop[uv_layer].uv
                # 相对于中心缩放
                loop[uv_layer].uv.x = center_u + (u - center_u) * scale_u
                loop[uv_layer].uv.y = center_v + (v - center_v) * scale_v

# 统一UV岛高度的操作符
class UV_OT_UnifyIslandsHeight(bpy.types.Operator):
    """统一选中的UV岛高度"""
    bl_idname = "uv.unify_islands_height"
    bl_label = "统一高度"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 锁定比例选项
    lock_aspect: BoolProperty(
        name="锁定比例",
        description="在调整高度时保持宽高比",
        default=False
    )
    
    def execute(self, context):
        # 获取当前对象
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "需要选择一个网格对象")
            return {'CANCELLED'}
        
        # 进入编辑模式
        bpy.ops.object.mode_set(mode='EDIT')
        
        # 获取bmesh和UV层
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()
        
        # 检查是否有选中的面
        selected_faces = [face for face in bm.faces if face.select]
        if not selected_faces:
            self.report({'WARNING'}, "没有选中的面")
            bpy.ops.object.mode_set(mode='OBJECT')
            return {'CANCELLED'}
        
        # 查找UV岛
        islands = []
        visited_faces = set()
        
        for face in selected_faces:
            if face in visited_faces:
                continue
                
            # 开始新的UV岛
            island = []
            stack = [face]
            
            while stack:
                current_face = stack.pop()
                if current_face in visited_faces:
                    continue
                    
                visited_faces.add(current_face)
                island.append(current_face)
                
                # 检查相邻面
                for edge in current_face.edges:
                    if edge.is_boundary:
                        continue
                        
                    for other_face in edge.link_faces:
                        if other_face not in visited_faces and other_face.select:
                            # 检查UV边是否匹配
                            uv_edge1 = [loop[uv_layer].uv for loop in edge.link_loops if loop.face == current_face]
                            uv_edge2 = [loop[uv_layer].uv for loop in edge.link_loops if loop.face == other_face]
                            
                            if len(uv_edge1) == 2 and len(uv_edge2) == 2:
                                # 检查UV边是否相同（考虑浮点精度）
                                if (abs((uv_edge1[0] - uv_edge2[0]).length) < 0.001 and 
                                    abs((uv_edge1[1] - uv_edge2[1]).length) < 0.001) or \
                                   (abs((uv_edge1[0] - uv_edge2[1]).length) < 0.001 and 
                                    abs((uv_edge1[1] - uv_edge2[0]).length) < 0.001):
                                    stack.append(other_face)
            
            if island:
                islands.append(island)
        
        if not islands:
            self.report({'WARNING'}, "没有找到选中的UV岛")
            bpy.ops.object.mode_set(mode='OBJECT')
            return {'CANCELLED'}
        
        # 计算目标高度（使用第一个UV岛的高度）
        _, target_min_v, _, target_max_v = self.get_island_bounds(islands[0], uv_layer)
        target_height = target_max_v - target_min_v
        
        # 统一所有UV岛的高度
        for island in islands:
            min_u, min_v, max_u, max_v = self.get_island_bounds(island, uv_layer)
            current_height = max_v - min_v
            
            if current_height > 0:
                scale_v = target_height / current_height
                
                if self.lock_aspect:
                    # 保持宽高比
                    scale_u = scale_v
                else:
                    scale_u = 1.0
                
                self.scale_island(island, uv_layer, scale_u, scale_v)
        
        # 更新网格
        bmesh.update_edit_mesh(obj.data)
        
        # 返回对象模式
        bpy.ops.object.mode_set(mode='OBJECT')
        
        self.report({'INFO'}, f"已统一{len(islands)}个UV岛的高度")
        return {'FINISHED'}
    
    def get_island_bounds(self, island, uv_layer):
        """获取UV岛的边界"""
        min_u = min_v = float('inf')
        max_u = max_v = float('-inf')
        
        for face in island:
            for loop in face.loops:
                u, v = loop[uv_layer].uv
                min_u = min(min_u, u)
                max_u = max(max_u, u)
                min_v = min(min_v, v)
                max_v = max(max_v, v)
        
        return min_u, min_v, max_u, max_v
    
    def scale_island(self, island, uv_layer, scale_u, scale_v):
        """缩放UV岛"""
        # 计算UV岛中心
        min_u, min_v, max_u, max_v = self.get_island_bounds(island, uv_layer)
        center_u = (min_u + max_u) / 2
        center_v = (min_v + max_v) / 2
        
        # 缩放UV岛
        for face in island:
            for loop in face.loops:
                u, v = loop[uv_layer].uv
                # 相对于中心缩放
                loop[uv_layer].uv.x = center_u + (u - center_u) * scale_u
                loop[uv_layer].uv.y = center_v + (v - center_v) * scale_v

# 放松UV岛的操作符
class UV_OT_RelaxIslands(bpy.types.Operator):
    """放松选中的UV岛"""
    bl_idname = "uv.relax_islands"
    bl_label = "放松UV岛"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 放松模式
    relax_mode: EnumProperty(
        name="放松模式",
        description="选择放松算法",
        items=[
            ('AVERAGE', "平均", "均匀分布UV顶点"),
            ('BOUNDARY', "边界", "保持边界形状，放松内部顶点"),
            ('ANGLE', "角度", "优化UV角度，减少变形"),
        ],
        default='AVERAGE'
    )
    
    # 放松强度
    relax_strength: FloatProperty(
        name="放松强度",
        description="控制放松效果的强度",
        default=0.5,
        min=0.1,
        max=1.0,
        step=0.1,
        precision=1
    )
    
    # 迭代次数
    iterations: IntProperty(
        name="迭代次数",
        description="放松算法的迭代次数",
        default=3,
        min=1,
        max=10
    )
    
    def execute(self, context):
        # 获取当前对象
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "需要选择一个网格对象")
            return {'CANCELLED'}
        
        # 进入编辑模式
        bpy.ops.object.mode_set(mode='EDIT')
        
        # 获取bmesh和UV层
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()
        
        # 检查是否有选中的面
        selected_faces = [face for face in bm.faces if face.select]
        if not selected_faces:
            self.report({'WARNING'}, "没有选中的面")
            bpy.ops.object.mode_set(mode='OBJECT')
            return {'CANCELLED'}
        
        # 查找UV岛
        islands = []
        visited_faces = set()
        
        for face in selected_faces:
            if face in visited_faces:
                continue
                
            # 开始新的UV岛
            island = []
            stack = [face]
            
            while stack:
                current_face = stack.pop()
                if current_face in visited_faces:
                    continue
                    
                visited_faces.add(current_face)
                island.append(current_face)
                
                # 检查相邻面
                for edge in current_face.edges:
                    if edge.is_boundary:
                        continue
                        
                    for other_face in edge.link_faces:
                        if other_face not in visited_faces and other_face.select:
                            # 检查UV边是否匹配
                            uv_edge1 = [loop[uv_layer].uv for loop in edge.link_loops if loop.face == current_face]
                            uv_edge2 = [loop[uv_layer].uv for loop in edge.link_loops if loop.face == other_face]
                            
                            if len(uv_edge1) == 2 and len(uv_edge2) == 2:
                                # 检查UV边是否相同（考虑浮点精度）
                                if (abs((uv_edge1[0] - uv_edge2[0]).length) < 0.001 and 
                                    abs((uv_edge1[1] - uv_edge2[1]).length) < 0.001) or \
                                   (abs((uv_edge1[0] - uv_edge2[1]).length) < 0.001 and 
                                    abs((uv_edge1[1] - uv_edge2[0]).length) < 0.001):
                                    stack.append(other_face)
            
            if island:
                islands.append(island)
        
        if not islands:
            self.report({'WARNING'}, "没有找到选中的UV岛")
            bpy.ops.object.mode_set(mode='OBJECT')
            return {'CANCELLED'}
        
        # 对每个UV岛应用放松算法
        for island in islands:
            self.relax_island(island, uv_layer, self.relax_mode, self.relax_strength, self.iterations)
        
        # 更新网格
        bmesh.update_edit_mesh(obj.data)
        
        # 返回对象模式
        bpy.ops.object.mode_set(mode='OBJECT')
        
        self.report({'INFO'}, f"已放松{len(islands)}个UV岛")
        return {'FINISHED'}
    
    def relax_island(self, island, uv_layer, mode, strength, iterations):
        """对UV岛应用放松算法"""
        # 收集所有UV顶点
        uv_verts = []
        for face in island:
            for loop in face.loops:
                uv_verts.append(loop[uv_layer])
        
        # 识别边界顶点
        boundary_verts = set()
        for face in island:
            for edge in face.edges:
                if edge.is_boundary:
                    for loop in edge.link_loops:
                        if loop.face in island:
                            boundary_verts.add(loop[uv_layer])
        
        # 应用放松算法
        for _ in range(iterations):
            if mode == 'AVERAGE':
                self.relax_average(uv_verts, boundary_verts, strength)
            elif mode == 'BOUNDARY':
                self.relax_boundary(uv_verts, boundary_verts, strength)
            elif mode == 'ANGLE':
                self.relax_angle(island, uv_layer, strength)
    
    def relax_average(self, uv_verts, boundary_verts, strength):
        """平均模式放松算法"""
        for uv in uv_verts:
            if uv in boundary_verts:
                continue  # 跳过边界顶点
            
            # 获取相邻顶点
            neighbors = self.get_uv_neighbors(uv)
            if not neighbors:
                continue
            
            # 计算邻居的平均位置
            avg_pos = Vector((0, 0))
            for neighbor in neighbors:
                avg_pos += neighbor.uv
            avg_pos /= len(neighbors)
            
            # 向平均位置移动
            uv.uv = uv.uv.lerp(avg_pos, strength)
    
    def relax_boundary(self, uv_verts, boundary_verts, strength):
        """边界模式放松算法"""
        for uv in uv_verts:
            if uv in boundary_verts:
                continue  # 跳过边界顶点
            
            # 获取相邻顶点
            neighbors = self.get_uv_neighbors(uv)
            if not neighbors:
                continue
            
            # 计算邻居的平均位置，但考虑边界约束
            avg_pos = Vector((0, 0))
            weight_sum = 0
            
            for neighbor in neighbors:
                # 边界顶点权重更高
                weight = 2.0 if neighbor in boundary_verts else 1.0
                avg_pos += neighbor.uv * weight
                weight_sum += weight
            
            avg_pos /= weight_sum
            
            # 向平均位置移动
            uv.uv = uv.uv.lerp(avg_pos, strength)
    
    def relax_angle(self, island, uv_layer, strength):
        """角度模式放松算法"""
        # 收集所有面和边
        faces = island
        edges = set()
        for face in faces:
            for edge in face.edges:
                edges.add(edge)
        
        # 计算每个边的理想角度
        for edge in edges:
            # 获取共享此边的两个面
            edge_faces = [f for f in edge.link_faces if f in faces]
            if len(edge_faces) != 2:
                continue
            
            # 计算当前角度
            face1, face2 = edge_faces
            
            # 获取UV顶点
            uv_verts1 = [loop[uv_layer].uv for loop in face1.loops]
            uv_verts2 = [loop[uv_layer].uv for loop in face2.loops]
            
            # 简化处理：调整共享边的顶点位置
            # 这里可以实现更复杂的角度优化算法
            for loop in edge.link_loops:
                if loop.face in faces:
                    uv = loop[uv_layer]
                    # 获取相邻顶点
                    neighbors = self.get_uv_neighbors(uv)
                    if len(neighbors) >= 2:
                        # 计算理想位置
                        v1 = neighbors[0].uv
                        v2 = neighbors[1].uv
                        ideal_pos = (v1 + v2) / 2
                        
                        # 向理想位置移动
                        uv.uv = uv.uv.lerp(ideal_pos, strength)
    
    def get_uv_neighbors(self, uv_vert):
        """获取UV顶点的邻居"""
        neighbors = []
        
        # 获取包含此UV顶点的所有边
        for edge in uv_vert.edge.link_edges:
            for loop in edge.link_loops:
                if loop != uv_vert and loop.vert == uv_vert.vert:
                    neighbors.append(loop)
        
        return neighbors

# 统一UV岛尺寸的面板
class UV_PT_UnifyIslandsPanel(bpy.types.Panel):
    """统一UV岛尺寸的面板"""
    bl_label = "统一UV岛尺寸"
    bl_idname = "UV_PT_UnifyIslandsPanel"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Ctools UV"
    
    def draw(self, context):
        layout = self.layout
        
        # 缩放模式选择
        layout.prop(context.scene, "uv_scale_mode", expand=True)
        
        # 锁定比例选项
        layout.prop(context.scene, "uv_lock_aspect")
        
        # 操作按钮
        row = layout.row(align=True)
        row.operator(UV_OT_UnifyIslandsWidth.bl_idname, text="统一宽度")
        row.operator(UV_OT_UnifyIslandsHeight.bl_idname, text="统一高度")

# 放松UV岛的面板
class UV_PT_RelaxIslandsPanel(bpy.types.Panel):
    """放松UV岛的面板"""
    bl_label = "放松UV岛"
    bl_idname = "UV_PT_RelaxIslandsPanel"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Ctools UV"
    
    def draw(self, context):
        layout = self.layout
        
        # 放松模式选择
        layout.prop(context.scene, "uv_relax_mode", text="模式")
        
        # 放松强度
        layout.prop(context.scene, "uv_relax_strength", text="强度")
        
        # 迭代次数
        layout.prop(context.scene, "uv_relax_iterations", text="迭代次数")
        
        # 操作按钮
        layout.operator(UV_OT_RelaxIslands.bl_idname, text="放松UV岛")

# UV工具集合面板
class UV_PT_UVToolsCollection(bpy.types.Panel):
    """UV工具集合面板"""
    bl_label = "UV工具集"
    bl_idname = "UV_PT_UVToolsCollection"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Ctools UV"
    
    def draw(self, context):
        layout = self.layout
        
        # 统一尺寸部分
        box = layout.box()
        box.label(text="统一尺寸", icon='MODIFIER')
        row = box.row(align=True)
        row.operator(UV_OT_UnifyIslandsWidth.bl_idname, text="统一宽度")
        row.operator(UV_OT_UnifyIslandsHeight.bl_idname, text="统一高度")
        
        # 放松部分
        box = layout.box()
        box.label(text="放松UV岛", icon='MOD_SMOOTH')
        box.prop(context.scene, "uv_relax_mode", text="模式")
        row = box.row(align=True)
        row.prop(context.scene, "uv_relax_strength", text="强度")
        row.prop(context.scene, "uv_relax_iterations", text="迭代")
        box.operator(UV_OT_RelaxIslands.bl_idname, text="放松UV岛")

# 注册和注销函数
def register():
    # 注册操作符
    bpy.utils.register_class(UV_OT_UnifyIslandsWidth)
    bpy.utils.register_class(UV_OT_UnifyIslandsHeight)
    bpy.utils.register_class(UV_OT_RelaxIslands)
    
    # 注册面板
    bpy.utils.register_class(UV_PT_UnifyIslandsPanel)
    bpy.utils.register_class(UV_PT_RelaxIslandsPanel)
    bpy.utils.register_class(UV_PT_UVToolsCollection)
    
    # 添加场景属性
    bpy.types.Scene.uv_scale_mode = EnumProperty(
        name="缩放模式",
        description="选择缩放模式",
        items=[
            ('WIDTH', "宽度", "统一宽度"),
            ('HEIGHT', "高度", "统一高度"),
        ],
        default='WIDTH'
    )
    
    bpy.types.Scene.uv_lock_aspect = BoolProperty(
        name="锁定比例",
        description="在调整尺寸时保持宽高比",
        default=False
    )
    
    bpy.types.Scene.uv_relax_mode = EnumProperty(
        name="放松模式",
        description="选择放松算法",
        items=[
            ('AVERAGE', "平均", "均匀分布UV顶点"),
            ('BOUNDARY', "边界", "保持边界形状，放松内部顶点"),
            ('ANGLE', "角度", "优化UV角度，减少变形"),
        ],
        default='AVERAGE'
    )
    
    bpy.types.Scene.uv_relax_strength = FloatProperty(
        name="放松强度",
        description="控制放松效果的强度",
        default=0.5,
        min=0.1,
        max=1.0,
        step=0.1,
        precision=1
    )
    
    bpy.types.Scene.uv_relax_iterations = IntProperty(
        name="迭代次数",
        description="放松算法的迭代次数",
        default=3,
        min=1,
        max=10
    )

def unregister():
    # 注销操作符
    bpy.utils.unregister_class(UV_OT_UnifyIslandsWidth)
    bpy.utils.unregister_class(UV_OT_UnifyIslandsHeight)
    bpy.utils.unregister_class(UV_OT_RelaxIslands)
    
    # 注销面板
    bpy.utils.unregister_class(UV_PT_UnifyIslandsPanel)
    bpy.utils.unregister_class(UV_PT_RelaxIslandsPanel)
    bpy.utils.unregister_class(UV_PT_UVToolsCollection)
    
    # 删除场景属性
    del bpy.types.Scene.uv_scale_mode
    del bpy.types.Scene.uv_lock_aspect
    del bpy.types.Scene.uv_relax_mode
    del bpy.types.Scene.uv_relax_strength
    del bpy.types.Scene.uv_relax_iterations

# 当作为脚本直接运行时
if __name__ == "__main__":
    register()