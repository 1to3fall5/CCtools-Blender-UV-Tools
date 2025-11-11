import bpy
import bmesh
import math
import mathutils
from mathutils import Vector

# 统一UV岛尺寸的基础操作符
class UV_OT_UnifyIslandsBase(bpy.types.Operator):
    """统一选中UV岛的尺寸基础类"""
    bl_idname = "uv.unify_islands_base"
    bl_label = "统一UV岛尺寸基础类"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 添加属性，用于选择使用最大值、最小值还是平均值
    unify_mode: bpy.props.EnumProperty(
        name="缩放模式",
        description="选择缩放UV岛尺寸的模式",
        items=[
            ('MAX', "最大值", "使用最大尺寸作为目标尺寸"),
            ('MIN', "最小值", "使用最小尺寸作为目标尺寸"),
            ('AVG', "平均值", "使用平均尺寸作为目标尺寸")
        ],
        default='MAX'
    )
    
    # 标识是统一宽度还是高度
    unify_width: bpy.props.BoolProperty(
        name="统一宽度",
        description="是否统一宽度而不是高度",
        default=True,
        options={'HIDDEN'}  # 隐藏属性，不在重做面板中显示
    )
    
    # 子类需要实现的方法
    def get_target_dimension(self, bounds):
        """获取目标尺寸（宽度或高度）"""
        raise NotImplementedError("子类必须实现此方法")
    
    def get_scale_factor(self, bounds, target_dim):
        """计算缩放因子"""
        raise NotImplementedError("子类必须实现此方法")
    
    def get_target_dimension_value(self, island_bounds):
        """根据选择的模式计算目标尺寸（最大值、最小值或平均值）"""
        if not island_bounds:
            return 0
            
        dims = []
        for _, bounds in island_bounds:
            dim = self.get_target_dimension(bounds)
            if dim > 0:
                dims.append(dim)
        
        if not dims:
            return 0
            
        if self.unify_mode == 'MAX':
            return max(dims)
        elif self.unify_mode == 'MIN':
            return min(dims)
        else:  # AVG
            return sum(dims) / len(dims)
    
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
        uv_islands = self.find_uv_islands(bm, uv_layer, selected_faces)
        if not uv_islands:
            self.report({'WARNING'}, "无法找到UV岛")
            return {'CANCELLED'}
        
        # 计算每个岛的边界
        island_bounds = []
        
        for island in uv_islands:
            # 计算岛的边界
            bounds = self.get_island_bounds(island, uv_layer)
            if bounds:
                island_bounds.append((island, bounds))
        
        if not island_bounds:
            self.report({'WARNING'}, "无法计算UV岛边界")
            return {'CANCELLED'}
        
        # 计算目标尺寸（根据选择的模式）
        target_dim = self.get_target_dimension_value(island_bounds)
        if target_dim <= 0:
            self.report({'WARNING'}, "无法计算目标尺寸")
            return {'CANCELLED'}
            
        mode_text = {"MAX": "最大值", "MIN": "最小值", "AVG": "平均值"}[self.unify_mode]
        self.report({'INFO'}, f"使用{mode_text}作为目标尺寸: {target_dim:.4f}")
        
        # 缩放每个选中的UV岛
        for island, bounds in island_bounds:
            self.scale_island(island, bounds, target_dim, uv_layer)
        
        # 更新网格数据
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        bmesh.update_edit_mesh(obj.data)
        
        # 刷新视图
        for area in context.screen.areas:
            area.tag_redraw()
        
        self.report({'INFO'}, f"已统一 {len(uv_islands)} 个UV岛的尺寸")
        return {'FINISHED'}
    
    def find_uv_islands(self, bm, uv_layer, selected_faces):
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
                        if self.faces_connected_in_uv(face, other_face, uv_layer, edge):
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
    
    def faces_connected_in_uv(self, face1, face2, uv_layer, edge):
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
    
    def get_island_bounds(self, island, uv_layer):
        """获取UV岛的边界"""
        if not island:
            return None
            
        min_u = min_v = float('inf')
        max_u = max_v = float('-inf')
        
        for face in island:
            for loop in face.loops:
                uv = loop[uv_layer].uv
                min_u = min(min_u, uv.x)
                min_v = min(min_v, uv.y)
                max_u = max(max_u, uv.x)
                max_v = max(max_v, uv.y)
        
        return (min_u, max_u, min_v, max_v)
    
    def scale_island(self, island, bounds, target_dim, uv_layer):
        """缩放UV岛"""
        min_u, max_u, min_v, max_v = bounds
        
        # 计算岛的中心点
        center = Vector(((min_u + max_u) / 2, (min_v + max_v) / 2))
        
        # 检查是否锁定比例
        if bpy.context.scene.uv_lock_aspect_ratio:
            # 锁定比例：根据统一方向计算缩放因子，但应用到两个方向
            if self.unify_width:
                # 统一宽度：基于宽度计算缩放因子
                current_width = max_u - min_u
                scale_factor = target_dim / current_width if current_width > 0 else 1.0
            else:
                # 统一高度：基于高度计算缩放因子
                current_height = max_v - min_v
                scale_factor = target_dim / current_height if current_height > 0 else 1.0
            
            # 同时缩放U和V方向，保持宽高比
            for face in island:
                for loop in face.loops:
                    uv = loop[uv_layer].uv
                    # 计算相对于中心点的坐标
                    rel_u = uv.x - center.x
                    rel_v = uv.y - center.y
                    # 应用缩放
                    uv.x = center.x + rel_u * scale_factor
                    uv.y = center.y + rel_v * scale_factor
        else:
            # 不锁定比例：根据统一方向选择缩放方式
            scale_factor = self.get_scale_factor(bounds, target_dim)
            
            for face in island:
                for loop in face.loops:
                    uv = loop[uv_layer].uv
                    
                    if self.unify_width:
                        # 统一宽度时，只缩放U方向
                        rel_u = uv.x - center.x
                        uv.x = center.x + rel_u * scale_factor
                        # V方向保持不变
                    else:
                        # 统一高度时，只缩放V方向
                        rel_v = uv.y - center.y
                        uv.y = center.y + rel_v * scale_factor
                        # U方向保持不变

# 统一UV岛宽度的操作符
class UV_OT_UnifyIslandsWidth(UV_OT_UnifyIslandsBase):
    """统一选中UV岛的宽度"""
    bl_idname = "uv.unify_islands_width"
    bl_label = "统一UV岛X轴尺寸"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 添加锁定比例属性，用于重做面板
    lock_aspect_ratio: bpy.props.BoolProperty(
        name="锁定比例",
        description="缩放时锁定UV岛的宽高比",
        default=False  # 改为默认关闭
    )
    
    def execute(self, context):
        # 设置为统一宽度模式
        self.unify_width = True
        
        # 使用操作自身的锁定比例设置
        # 临时保存锁定比例状态
        original_lock_aspect = context.scene.uv_lock_aspect_ratio
        context.scene.uv_lock_aspect_ratio = self.lock_aspect_ratio
        
        # 执行操作
        result = super().execute(context)
        
        # 恢复原始锁定比例状态
        context.scene.uv_lock_aspect_ratio = original_lock_aspect
        
        return result
    
    def get_target_dimension(self, bounds):
        """获取岛的宽度"""
        min_u, max_u, _, _ = bounds
        return max_u - min_u
    
    def get_scale_factor(self, bounds, target_dim):
        """计算宽度缩放因子"""
        min_u, max_u, _, _ = bounds
        current_width = max_u - min_u
        if current_width > 0:
            return target_dim / current_width
        return 1.0

# 统一UV岛高度的操作符
class UV_OT_UnifyIslandsHeight(UV_OT_UnifyIslandsBase):
    """统一选中UV岛的高度"""
    bl_idname = "uv.unify_islands_height"
    bl_label = "统一UV岛Y轴尺寸"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 添加锁定比例属性，用于重做面板
    lock_aspect_ratio: bpy.props.BoolProperty(
        name="锁定比例",
        description="缩放时锁定UV岛的宽高比",
        default=False  # 改为默认关闭
    )
    
    def execute(self, context):
        # 设置为统一高度模式
        self.unify_width = False
        
        # 使用操作自身的锁定比例属性，默认为True，确保与面板中的锁定比例功能相同
        original_lock_aspect = context.scene.uv_lock_aspect_ratio
        context.scene.uv_lock_aspect_ratio = self.lock_aspect_ratio
        
        # 执行操作
        result = super().execute(context)
        
        # 恢复原始锁定比例状态
        context.scene.uv_lock_aspect_ratio = original_lock_aspect
        
        return result
    
    def get_target_dimension(self, bounds):
        """获取岛的高度"""
        _, _, min_v, max_v = bounds
        return max_v - min_v
    
    def get_scale_factor(self, bounds, target_dim):
        """计算高度缩放因子"""
        _, _, min_v, max_v = bounds
        current_height = max_v - min_v
        if current_height > 0:
            return target_dim / current_height
        return 1.0



# 放松选中UV岛的操作符
class UV_OT_RelaxIslands(bpy.types.Operator):
    """放松选中的UV岛"""
    bl_idname = "uv.relax_islands"
    bl_label = "放松选中UV岛"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 放松强度属性
    relax_strength: bpy.props.FloatProperty(
        name="放松强度",
        description="控制UV放松的强度",
        default=0.5,
        min=0.0,
        max=1.0,
        step=0.1,
        precision=2
    )
    
    # 放松迭代次数
    relax_iterations: bpy.props.IntProperty(
        name="迭代次数",
        description="放松算法的迭代次数",
        default=5,
        min=1,
        max=20
    )
    
    # 放松模式
    relax_mode: bpy.props.EnumProperty(
        name="放松模式",
        description="选择放松UV的方式",
        items=[
            ('EDGE_LENGTH', "边长度", "基于边长度的放松"),
            ('ANGLE', "角度", "基于角度的放松"),
            ('AREA', "面积", "基于面积的放松")
        ],
        default='EDGE_LENGTH'
    )
    
    def execute(self, context):
        """执行放松UV岛操作"""
        # 获取当前对象
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "请先选择一个网格对象")
            return {'CANCELLED'}
        
        # 确保处于编辑模式
        if obj.mode != 'EDIT':
            self.report({'ERROR'}, "请切换到编辑模式")
            return {'CANCELLED'}
        
        # 获取BMesh对象
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.active
        
        if not uv_layer:
            self.report({'ERROR'}, "对象没有UV层")
            return {'CANCELLED'}
        
        # 获取选中的面
        selected_faces = [face for face in bm.faces if face.select]
        if not selected_faces:
            self.report({'ERROR'}, "请选择要放松的UV岛")
            return {'CANCELLED'}
        
        # 将选中的面分组为UV岛
        islands = self.get_uv_islands(selected_faces, uv_layer)
        
        if not islands:
            self.report({'ERROR'}, "没有找到UV岛")
            return {'CANCELLED'}
        
        # 对每个UV岛执行放松操作
        for island in islands:
            self.relax_island(island, uv_layer)
        
        # 更新显示
        bmesh.update_edit_mesh(obj.data)
        
        self.report({'INFO'}, f"已放松 {len(islands)} 个UV岛")
        return {'FINISHED'}
    
    def get_uv_islands(self, faces, uv_layer):
        """将选中的面分组为UV岛"""
        islands = []
        unprocessed_faces = faces.copy()
        
        while unprocessed_faces:
            # 创建新岛
            island = []
            queue = [unprocessed_faces.pop(0)]
            
            while queue:
                current_face = queue.pop(0)
                island.append(current_face)
                
                # 检查相邻的面
                for edge in current_face.edges:
                    for face in unprocessed_faces:
                        if edge in face.edges:
                            # 检查UV边是否匹配
                            if self.uv_edges_match(current_face, face, uv_layer):
                                queue.append(face)
                                unprocessed_faces.remove(face)
                                break
            
            islands.append(island)
        
        return islands
    
    def uv_edges_match(self, face1, face2, uv_layer):
        """检查两个面是否有匹配的UV边"""
        # 检查所有边
        for edge1 in face1.edges:
            for edge2 in face2.edges:
                if edge1 == edge2:
                    # 找到共享边，检查UV坐标是否匹配
                    return True
        
        return False
    
    def relax_island(self, island, uv_layer):
        """放松单个UV岛"""
        # 根据模式选择放松算法
        if self.relax_mode == 'EDGE_LENGTH':
            self.relax_edge_length(island, uv_layer)
        elif self.relax_mode == 'ANGLE':
            self.relax_angle(island, uv_layer)
        elif self.relax_mode == 'AREA':
            self.relax_area(island, uv_layer)
    
    def relax_edge_length(self, island, uv_layer):
        """基于边长度的放松算法 - 保持UV岛整体性"""
        for iteration in range(self.relax_iterations):
            # 收集岛中所有UV点
            island_uvs = []
            for face in island:
                for loop in face.loops:
                    island_uvs.append(loop[uv_layer].uv)
            
            # 计算UV岛的中心点
            center_x = sum(uv.x for uv in island_uvs) / len(island_uvs)
            center_y = sum(uv.y for uv in island_uvs) / len(island_uvs)
            center = mathutils.Vector((center_x, center_y))
            
            # 计算每个UV点到中心的平均距离
            avg_distance = sum((uv - center).length for uv in island_uvs) / len(island_uvs)
            
            # 对每个UV点应用放松，但保持相对位置
            for face in island:
                for loop in face.loops:
                    uv = loop[uv_layer].uv
                    direction = uv - center
                    
                    if direction.length > 0:
                        # 归一化方向并应用放松
                        direction.normalize()
                        new_distance = uv.length + (avg_distance - uv.length) * self.relax_strength
                        new_pos = center + direction * new_distance
                        
                        # 更新UV位置
                        loop[uv_layer].uv.x = new_pos.x
                        loop[uv_layer].uv.y = new_pos.y
    
    def relax_angle(self, island, uv_layer):
        """基于角度的放松算法 - 保持UV岛整体性"""
        for iteration in range(self.relax_iterations):
            # 收集岛中所有UV点
            island_uvs = []
            for face in island:
                for loop in face.loops:
                    island_uvs.append(loop[uv_layer].uv)
            
            # 计算UV岛的中心点
            center_x = sum(uv.x for uv in island_uvs) / len(island_uvs)
            center_y = sum(uv.y for uv in island_uvs) / len(island_uvs)
            center = mathutils.Vector((center_x, center_y))
            
            # 计算每个UV点的角度和距离
            uv_data = []
            for uv in island_uvs:
                direction = uv - center
                if direction.length > 0:
                    angle = math.atan2(direction.y, direction.x)
                    distance = direction.length
                    uv_data.append((uv, angle, distance))
            
            # 计算平均角度变化
            if len(uv_data) > 1:
                angles = [data[1] for data in uv_data]
                avg_angle = sum(angles) / len(angles)
                
                # 对每个UV点应用角度放松
                for face in island:
                    for loop in face.loops:
                        uv = loop[uv_layer].uv
                        direction = uv - center
                        
                        if direction.length > 0:
                            current_angle = math.atan2(direction.y, direction.x)
                            new_angle = current_angle + (avg_angle - current_angle) * self.relax_strength * 0.7
                            
                            # 保持距离不变，只改变角度
                            new_pos = center + mathutils.Vector((
                                direction.length * math.cos(new_angle),
                                direction.length * math.sin(new_angle)
                            ))
                            
                            # 更新UV位置
                            loop[uv_layer].uv.x = new_pos.x
                            loop[uv_layer].uv.y = new_pos.y
    
    def relax_area(self, island, uv_layer):
        """基于面积的放松算法 - 保持UV岛整体性"""
        for iteration in range(self.relax_iterations):
            # 收集岛中所有UV点
            island_uvs = []
            for face in island:
                for loop in face.loops:
                    island_uvs.append(loop[uv_layer].uv)
            
            # 计算UV岛的中心点
            center_x = sum(uv.x for uv in island_uvs) / len(island_uvs)
            center_y = sum(uv.y for uv in island_uvs) / len(island_uvs)
            center = mathutils.Vector((center_x, center_y))
            
            # 计算UV岛的当前面积（使用凸包近似）
            if len(island_uvs) < 3:
                continue  # 需要至少3个点才能形成面积
                
            # 计算当前面积
            current_area = 0
            for i in range(len(island_uvs)):
                j = (i + 1) % len(island_uvs)
                current_area += island_uvs[i].x * island_uvs[j].y
                current_area -= island_uvs[j].x * island_uvs[i].y
            current_area = abs(current_area) / 2
            
            # 计算目标面积（基于平均距离）
            avg_distance = sum((uv - center).length for uv in island_uvs) / len(island_uvs)
            target_area = math.pi * avg_distance * avg_distance  # 使用圆形面积作为参考
            
            # 计算缩放因子
            if current_area > 0:
                scale_factor = 1 + (target_area - current_area) / current_area * self.relax_strength * 0.5
                scale_factor = max(0.1, min(3.0, scale_factor))  # 限制缩放范围
                
                # 对每个UV点应用缩放
                for face in island:
                    for loop in face.loops:
                        uv = loop[uv_layer].uv
                        direction = uv - center
                        
                        # 缩放方向向量
                        new_pos = center + direction * scale_factor
                        
                        # 更新UV位置
                        loop[uv_layer].uv.x = new_pos.x
                        loop[uv_layer].uv.y = new_pos.y
    
    def get_uv_neighbors(self, face, uv_layer, current_loop):
        """获取UV邻居点"""
        neighbors = []
        
        # 获取当前循环的UV坐标
        current_uv = current_loop[uv_layer].uv
        
        # 遍历面的所有循环
        for loop in face.loops:
            if loop != current_loop:
                # 检查UV坐标是否相同（避免重复）
                if (loop[uv_layer].uv.x != current_uv.x or 
                    loop[uv_layer].uv.y != current_uv.y):
                    neighbors.append((loop[uv_layer].uv.x, loop[uv_layer].uv.y))
        
        # 检查相邻面
        for edge in face.edges:
            for linked_face in edge.link_faces:
                if linked_face != face:
                    for loop in linked_face.loops:
                        # 检查UV坐标是否相同（避免重复）
                        if (loop[uv_layer].uv.x != current_uv.x or 
                            loop[uv_layer].uv.y != current_uv.y):
                            neighbors.append((loop[uv_layer].uv.x, loop[uv_layer].uv.y))
        
        return neighbors


# UV工具面板
class UV_PT_UnifyIslandsPanel(bpy.types.Panel):
    """统一UV岛尺寸面板"""
    bl_label = "统一UV岛XY尺寸"
    bl_idname = "UV_PT_unify_islands_panel"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Ctools UV"
    
    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label(text="统一选中UV岛的尺寸")
        
        # 添加模式选择
        box.prop(context.scene, "uv_unify_mode", text="缩放模式")
        
        # 锁定比例开关
        row = box.row()
        row.prop(context.scene, "uv_lock_aspect_ratio", text="锁定比例")
        
        # X和Y按钮横向排列
        row = box.row()
        op = row.operator(UV_OT_UnifyIslandsWidth.bl_idname, text="X")
        op.unify_mode = context.scene.uv_unify_mode
        op = row.operator(UV_OT_UnifyIslandsHeight.bl_idname, text="Y")
        op.unify_mode = context.scene.uv_unify_mode


# 放松UV岛面板
class UV_PT_RelaxIslandsPanel(bpy.types.Panel):
    """放松UV岛面板"""
    bl_label = "放松UV岛"
    bl_idname = "UV_PT_relax_islands_panel"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Ctools UV"
    
    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label(text="放松选中的UV岛")
        
        # 放松模式选择
        box.prop(context.scene, "uv_relax_mode", text="放松模式")
        
        # 放松强度滑块
        box.prop(context.scene, "uv_relax_strength", text="放松强度")
        
        # 迭代次数滑块
        box.prop(context.scene, "uv_relax_iterations", text="迭代次数")
        
        # 放松按钮
        op = box.operator(UV_OT_RelaxIslands.bl_idname, text="放松UV岛")
        op.relax_mode = context.scene.uv_relax_mode
        op.relax_strength = context.scene.uv_relax_strength
        op.relax_iterations = context.scene.uv_relax_iterations


# UV工具集合面板
class UV_PT_UVToolsCollection(bpy.types.Panel):
    """UV工具集合面板"""
    bl_label = "Ctools UV工具集"
    bl_idname = "UV_PT_uv_tools_collection"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Ctools UV"
    
    def draw(self, context):
        layout = self.layout
        
        # 统一尺寸部分
        box = layout.box()
        box.label(text="统一UV岛尺寸", icon='MOD_LENGTH')
        
        # 添加模式选择
        box.prop(context.scene, "uv_unify_mode", text="缩放模式")
        
        # 锁定比例开关
        row = box.row()
        row.prop(context.scene, "uv_lock_aspect_ratio", text="锁定比例")
        
        # X和Y按钮横向排列
        row = box.row()
        op = row.operator(UV_OT_UnifyIslandsWidth.bl_idname, text="X")
        op.unify_mode = context.scene.uv_unify_mode
        op = row.operator(UV_OT_UnifyIslandsHeight.bl_idname, text="Y")
        op.unify_mode = context.scene.uv_unify_mode
        
        # 放松UV岛部分
        box = layout.box()
        box.label(text="放松UV岛", icon='MOD_SOFT')
        
        # 放松模式选择
        box.prop(context.scene, "uv_relax_mode", text="放松模式")
        
        # 放松强度滑块
        box.prop(context.scene, "uv_relax_strength", text="放松强度")
        
        # 迭代次数滑块
        box.prop(context.scene, "uv_relax_iterations", text="迭代次数")
        
        # 放松按钮
        op = box.operator(UV_OT_RelaxIslands.bl_idname, text="放松UV岛")
        op.relax_mode = context.scene.uv_relax_mode
        op.relax_strength = context.scene.uv_relax_strength
        op.relax_iterations = context.scene.uv_relax_iterations

# 注册和注销函数
def register():
    bpy.utils.register_class(UV_OT_UnifyIslandsWidth)
    bpy.utils.register_class(UV_OT_UnifyIslandsHeight)
    bpy.utils.register_class(UV_OT_RelaxIslands)
    bpy.utils.register_class(UV_PT_UnifyIslandsPanel)
    bpy.utils.register_class(UV_PT_RelaxIslandsPanel)
    bpy.utils.register_class(UV_PT_UVToolsCollection)
    
    # 添加场景属性，用于存储用户选择的模式
    bpy.types.Scene.uv_unify_mode = bpy.props.EnumProperty(
        name="UV缩放模式",
        description="选择缩放UV岛尺寸的模式",
        items=[
            ('MAX', "最大值", "使用最大尺寸作为目标尺寸"),
            ('MIN', "最小值", "使用最小尺寸作为目标尺寸"),
            ('AVG', "平均值", "使用平均尺寸作为目标尺寸")
        ],
        default='MAX'
    )
    
    bpy.types.Scene.uv_lock_aspect_ratio = bpy.props.BoolProperty(
        name="UV锁定比例",
        description="缩放时锁定UV岛的宽高比",
        default=False  # 改为默认关闭
    )
    
    # 添加放松UV岛的场景属性
    bpy.types.Scene.uv_relax_mode = bpy.props.EnumProperty(
        name="UV放松模式",
        description="选择放松UV的方式",
        items=[
            ('EDGE_LENGTH', "边长度", "基于边长度的放松"),
            ('ANGLE', "角度", "基于角度的放松"),
            ('AREA', "面积", "基于面积的放松")
        ],
        default='EDGE_LENGTH'
    )
    
    bpy.types.Scene.uv_relax_strength = bpy.props.FloatProperty(
        name="UV放松强度",
        description="控制UV放松的强度",
        default=0.5,
        min=0.0,
        max=1.0,
        step=0.1,
        precision=2
    )
    
    bpy.types.Scene.uv_relax_iterations = bpy.props.IntProperty(
        name="UV放松迭代次数",
        description="放松算法的迭代次数",
        default=5,
        min=1,
        max=20
    )

def unregister():
    bpy.utils.unregister_class(UV_PT_UVToolsCollection)
    bpy.utils.unregister_class(UV_PT_RelaxIslandsPanel)
    bpy.utils.unregister_class(UV_PT_UnifyIslandsPanel)
    bpy.utils.unregister_class(UV_OT_RelaxIslands)
    bpy.utils.unregister_class(UV_OT_UnifyIslandsHeight)
    bpy.utils.unregister_class(UV_OT_UnifyIslandsWidth)
    
    # 移除场景属性
    del bpy.types.Scene.uv_unify_mode
    del bpy.types.Scene.uv_lock_aspect_ratio
    del bpy.types.Scene.uv_relax_mode
    del bpy.types.Scene.uv_relax_strength
    del bpy.types.Scene.uv_relax_iterations