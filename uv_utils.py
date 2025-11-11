"""
UV工具通用函数模块
包含多个UV工具模块共用的函数和类
"""

import bpy
import bmesh
from mathutils import Vector
from typing import List, Dict, Tuple, Set


def get_uv_islands(bm: bmesh.types.BMesh, uv_layer: bmesh.types.BMLayerItem) -> List[List[bmesh.types.BMFace]]:
    """
    获取所有UV岛
    
    Args:
        bm: BMesh对象
        uv_layer: UV层
        
    Returns:
        UV岛列表，每个岛包含一组面
    """
    islands = []
    visited_faces = set()
    
    for face in bm.faces:
        if face in visited_faces:
            continue
            
        # 创建新岛
        island = []
        stack = [face]
        
        while stack:
            current_face = stack.pop()
            if current_face in visited_faces:
                continue
                
            visited_faces.add(current_face)
            island.append(current_face)
            
            # 查找UV连接的相邻面
            for edge in current_face.edges:
                for other_face in edge.link_faces:
                    if other_face not in visited_faces and uv_edges_match(edge, uv_layer):
                        stack.append(other_face)
        
        islands.append(island)
    
    return islands


def uv_edges_match(edge: bmesh.types.BMEdge, uv_layer: bmesh.types.BMLayerItem) -> bool:
    """
    检查边在UV空间中是否匹配
    
    Args:
        edge: BMesh边
        uv_layer: UV层
        
    Returns:
        如果边在UV空间中匹配返回True，否则返回False
    """
    if len(edge.link_faces) != 2:
        return False
        
    face1, face2 = edge.link_faces
    
    # 获取边的两个顶点在两个面中的索引
    verts1 = [v for v in face1.verts if v in edge.verts]
    verts2 = [v for v in face2.verts if v in edge.verts]
    
    if len(verts1) != 2 or len(verts2) != 2:
        return False
        
    # 获取UV坐标
    uv1 = [loop[uv_layer].uv for loop in face1.loops if loop.vert in verts1]
    uv2 = [loop[uv_layer].uv for loop in face2.loops if loop.vert in verts2]
    
    if len(uv1) != 2 or len(uv2) != 2:
        return False
        
    # 检查UV坐标是否匹配（允许一定误差）
    epsilon = 1e-6
    return (abs(uv1[0].x - uv2[0].x) < epsilon and abs(uv1[0].y - uv2[0].y) < epsilon and
            abs(uv1[1].x - uv2[1].x) < epsilon and abs(uv1[1].y - uv2[1].y) < epsilon) or \
           (abs(uv1[0].x - uv2[1].x) < epsilon and abs(uv1[0].y - uv2[1].y) < epsilon and
            abs(uv1[1].x - uv2[0].x) < epsilon and abs(uv1[1].y - uv2[0].y) < epsilon)


def faces_connected_in_uv(face1: bmesh.types.BMFace, face2: bmesh.types.BMFace, uv_layer: bmesh.types.BMLayerItem) -> bool:
    """
    检查两个面在UV空间中是否连接
    
    Args:
        face1: 第一个面
        face2: 第二个面
        uv_layer: UV层
        
    Returns:
        如果两个面在UV空间中连接返回True，否则返回False
    """
    # 检查是否有共享边
    shared_edges = [edge for edge in face1.edges if edge in face2.edges]
    if not shared_edges:
        return False
        
    # 检查共享边在UV空间中是否匹配
    for edge in shared_edges:
        if uv_edges_match(edge, uv_layer):
            return True
            
    return False


def get_uv_bounds(island: List[bmesh.types.BMFace], uv_layer: bmesh.types.BMLayerItem) -> Tuple[Vector, Vector]:
    """
    获取UV岛的边界框
    
    Args:
        island: UV岛（面的列表）
        uv_layer: UV层
        
    Returns:
        最小和最大UV坐标
    """
    min_uv = Vector((float('inf'), float('inf')))
    max_uv = Vector((float('-inf'), float('-inf')))
    
    for face in island:
        for loop in face.loops:
            uv = loop[uv_layer].uv
            min_uv.x = min(min_uv.x, uv.x)
            min_uv.y = min(min_uv.y, uv.y)
            max_uv.x = max(max_uv.x, uv.x)
            max_uv.y = max(max_uv.y, uv.y)
    
    return min_uv, max_uv


def get_island_center(island: List[bmesh.types.BMFace], uv_layer: bmesh.types.BMLayerItem) -> Vector:
    """
    获取UV岛的中心点
    
    Args:
        island: UV岛（面的列表）
        uv_layer: UV层
        
    Returns:
        UV岛的中心点坐标
    """
    min_uv, max_uv = get_uv_bounds(island, uv_layer)
    return Vector(((min_uv.x + max_uv.x) / 2, (min_uv.y + max_uv.y) / 2))


def get_uv_island_area(island: List[bmesh.types.BMFace], uv_layer: bmesh.types.BMLayerItem) -> float:
    """
    计算UV岛的面积
    
    Args:
        island: UV岛（面的列表）
        uv_layer: UV层
        
    Returns:
        UV岛的面积
    """
    area = 0.0
    
    for face in island:
        if len(face.loops) < 3:
            continue
            
        # 使用鞋带公式计算多边形面积
        uv_coords = [loop[uv_layer].uv for loop in face.loops]
        
        for i in range(len(uv_coords)):
            j = (i + 1) % len(uv_coords)
            area += uv_coords[i].x * uv_coords[j].y
            area -= uv_coords[j].x * uv_coords[i].y
    
    return abs(area) / 2.0


def get_uv_neighbors(vert: bmesh.types.BMVert, uv_layer: bmesh.types.BMLayerItem) -> List[bmesh.types.BMVert]:
    """
    获取UV空间中与顶点相邻的顶点
    
    Args:
        vert: BMesh顶点
        uv_layer: UV层
        
    Returns:
        相邻顶点列表
    """
    neighbors = []
    
    # 获取顶点的UV坐标
    vert_uv = None
    for loop in vert.link_loops:
        if loop.face:
            vert_uv = loop[uv_layer].uv
            break
    
    if vert_uv is None:
        return neighbors
    
    # 查找具有相同UV坐标的相邻顶点
    for edge in vert.link_edges:
        other_vert = edge.other_vert(vert)
        
        for loop in other_vert.link_loops:
            if loop.face:
                other_uv = loop[uv_layer].uv
                if (abs(other_uv.x - vert_uv.x) < 1e-6 and 
                    abs(other_uv.y - vert_uv.y) < 1e-6):
                    neighbors.append(other_vert)
                    break
    
    return neighbors


def get_edge_midpoint_uv(edge: bmesh.types.BMEdge, uv_layer: bmesh.types.BMLayerItem) -> Vector:
    """
    获取边在UV空间中的中点
    
    Args:
        edge: BMesh边
        uv_layer: UV层
        
    Returns:
        边在UV空间中的中点坐标
    """
    uv_sum = Vector((0.0, 0.0))
    count = 0
    
    for vert in edge.verts:
        for loop in vert.link_loops:
            if loop.face and edge in loop.face.edges:
                uv_sum += loop[uv_layer].uv
                count += 1
                break
    
    if count > 0:
        return uv_sum / count
    else:
        return Vector((0.5, 0.5))


def is_island_overlapping(island1: List[bmesh.types.BMFace], island2: List[bmesh.types.BMFace], 
                         uv_layer: bmesh.types.BMLayerItem, threshold: float = 0.01) -> bool:
    """
    检查两个UV岛是否重叠
    
    Args:
        island1: 第一个UV岛
        island2: 第二个UV岛
        uv_layer: UV层
        threshold: 重叠阈值
        
    Returns:
        如果两个岛重叠返回True，否则返回False
    """
    min1, max1 = get_uv_bounds(island1, uv_layer)
    min2, max2 = get_uv_bounds(island2, uv_layer)
    
    # 检查边界框是否重叠
    overlap_x = min(max1.x, max2.x) - max(min1.x, min2.x) > threshold
    overlap_y = min(max1.y, max2.y) - max(min1.y, min2.y) > threshold
    
    return overlap_x and overlap_y


def scale_uv_island(island: List[bmesh.types.BMFace], uv_layer: bmesh.types.BMLayerItem, 
                   scale_factor: float, center: Vector = None) -> None:
    """
    缩放UV岛
    
    Args:
        island: UV岛（面的列表）
        uv_layer: UV层
        scale_factor: 缩放因子
        center: 缩放中心点，如果为None则使用岛的中心
    """
    if center is None:
        center = get_island_center(island, uv_layer)
    
    for face in island:
        for loop in face.loops:
            uv = loop[uv_layer].uv
            # 相对于中心点进行缩放
            uv.x = center.x + (uv.x - center.x) * scale_factor
            uv.y = center.y + (uv.y - center.y) * scale_factor


def move_uv_island(island: List[bmesh.types.BMFace], uv_layer: bmesh.types.BMLayerItem, 
                  offset: Vector) -> None:
    """
    移动UV岛
    
    Args:
        island: UV岛（面的列表）
        uv_layer: UV层
        offset: 移动偏移量
    """
    for face in island:
        for loop in face.loops:
            uv = loop[uv_layer].uv
            uv.x += offset.x
            uv.y += offset.y


def rotate_uv_island(island: List[bmesh.types.BMFace], uv_layer: bmesh.types.BMLayerItem, 
                   angle: float, center: Vector = None) -> None:
    """
    旋转UV岛
    
    Args:
        island: UV岛（面的列表）
        uv_layer: UV层
        angle: 旋转角度（弧度）
        center: 旋转中心点，如果为None则使用岛的中心
    """
    if center is None:
        center = get_island_center(island, uv_layer)
    
    import math
    cos_angle = math.cos(angle)
    sin_angle = math.sin(angle)
    
    for face in island:
        for loop in face.loops:
            uv = loop[uv_layer].uv
            # 相对于中心点进行旋转
            rel_x = uv.x - center.x
            rel_y = uv.y - center.y
            
            uv.x = center.x + rel_x * cos_angle - rel_y * sin_angle
            uv.y = center.y + rel_x * sin_angle + rel_y * cos_angle


def flip_uv_island(island: List[bmesh.types.BMFace], uv_layer: bmesh.types.BMLayerItem, 
                  axis: str = 'horizontal', center: Vector = None) -> None:
    """
    翻转UV岛
    
    Args:
        island: UV岛（面的列表）
        uv_layer: UV层
        axis: 翻转轴，'horizontal'或'vertical'
        center: 翻转中心点，如果为None则使用岛的中心
    """
    if center is None:
        center = get_island_center(island, uv_layer)
    
    for face in island:
        for loop in face.loops:
            uv = loop[uv_layer].uv
            
            if axis == 'horizontal':
                # 水平翻转
                uv.x = center.x - (uv.x - center.x)
            elif axis == 'vertical':
                # 垂直翻转
                uv.y = center.y - (uv.y - center.y)


def get_uv_layer(obj: bpy.types.Object) -> bmesh.types.BMLayerItem:
    """
    获取对象的UV层
    
    Args:
        obj: Blender对象
        
    Returns:
        UV层，如果不存在则返回None
    """
    if obj.type != 'MESH':
        return None
        
    bm = bmesh.from_edit_mesh(obj.data)
    uv_layers = bm.loops.layers.uv
    
    if not uv_layers:
        return None
        
    # 获取活动UV层
    active_uv_layer = bm.loops.layers.active
    
    if active_uv_layer and active_uv_layer.is_uv:
        return active_uv_layer
    
    # 如果没有活动UV层，返回第一个UV层
    return uv_layers[0]


def ensure_uv_layer(obj: bpy.types.Object, name: str = "UVMap") -> bmesh.types.BMLayerItem:
    """
    确保对象有UV层，如果没有则创建
    
    Args:
        obj: Blender对象
        name: UV层名称
        
    Returns:
        UV层
    """
    if obj.type != 'MESH':
        return None
        
    bm = bmesh.from_edit_mesh(obj.data)
    uv_layers = bm.loops.layers.uv
    
    # 检查是否已存在指定名称的UV层
    for layer in uv_layers:
        if layer.name == name:
            return layer
    
    # 创建新的UV层
    new_layer = uv_layers.new(name=name)
    bm.loops.layers.active = new_layer
    
    return new_layer