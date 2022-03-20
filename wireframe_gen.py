
bl_info = {
    "name": "Wireframe Gen",
    "author": "Latidoremi",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Object > Wireframe Gen",
    "description": "Adds a new Mesh Object",
    "warning": "",
    "doc_url": "",
    "category": "Object",
}

import bpy, bmesh
from mathutils import Vector, Matrix

base_vertices=[
    (-1, -1, -1), (-1, -1, 1), (1, -1, 1), (1, -1, -1),
    (-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1),
]

edge_indices=[
    (0,1), (1,2), (2,3), (3,0),
    (4,5), (5,6), (6,7), (7,4),
    (0,4), (1,5), (2,6), (3,7),
]

face_indices=[
    (0,1,5,4),
    (1,2,6,5),
    (2,3,7,6),
    (3,0,4,7),
]


def calc_normal_binormal(v):
    max_index = max(range(len(v)), key=list(map(lambda x:abs(x), v)).__getitem__)
    if max_index == 0:
        return Vector((0,0,1)), Vector((0,1,0))
    elif max_index == 1:
        return Vector((0,0,1)), Vector((1,0,0))
    elif max_index == 2:
        return Vector((1,0,0)), Vector((0,1,0))

def join_bmesh(bm1, bm2):
    bm1_v_count=len(bm1.verts)
    for v in bm2.verts:
        bm1.verts.new(v.co)
    bm1.verts.ensure_lookup_table()
    
    for e in bm2.edges:
        bm1.edges.new((bm1.verts[v.index+bm1_v_count] for v in e.verts))
    
    for f in bm2.faces:
        bm1.faces.new((bm1.verts[v.index+bm1_v_count] for v in f.verts))



class OBJECT_OT_wireframe_gen(bpy.types.Operator):
    bl_idname = 'object.wireframe_gen'
    bl_label = 'Wireframe Gen'
    bl_options = {'UNDO', 'REGISTER'}
    
    thickness:bpy.props.FloatProperty(name='Thickness', default=0.1, min=0)
    
    def execute(self, context):
        dg = context.evaluated_depsgraph_get()
        tgt_me = bpy.data.meshes.new('Wireframe')
        tgt_ob = bpy.data.objects.new('Wireframe',tgt_me)
        context.scene.collection.objects.link(tgt_ob)
        
        bm = bmesh.new()
        bm.from_object(context.active_object, dg)
        
        tgt_bm = bmesh.new()
        tgt_v_count=0
        
        temp = bmesh.new()
        #add cube to each vertex
        for v in bm.verts:
            bmesh.ops.create_cube(temp, size=self.thickness*2, matrix=Matrix.Translation(v.co))
            temp.faces.ensure_lookup_table()
            
            edge_vectors=[(e.other_vert(v).co-v.co).normalized() for e in v.link_edges]
            del_faces=[]
            for f in temp.faces:
                for ev in edge_vectors:
                    if f.normal.dot(ev) > 0.9:
                        del_faces.append(f)
#            print(del_faces)
            bmesh.ops.delete(temp, geom=del_faces, context='FACES')
            join_bmesh(tgt_bm, temp)
            tgt_v_count += len(temp.verts)
            temp.clear()
        
        #add tube to each edge
        for i,edge in enumerate(bm.edges):
            v1 = edge.verts[0].co
            v2 = edge.verts[1].co
            
            edge_vector = v1-v2
            normal, binormal = calc_normal_binormal(edge_vector)
            vertices=[]
            
            for bv in base_vertices[:4]:
                vertices.append( bv[0]*normal*self.thickness + bv[2]*binormal*self.thickness + v1 - self.thickness*edge_vector.normalized() )
            
            for bv in base_vertices[4:]:
                vertices.append( bv[0]*normal*self.thickness + bv[2]*binormal*self.thickness + v2 + self.thickness*edge_vector.normalized() )
            
            
            for v in vertices:
                tgt_bm.verts.new(v)
            tgt_bm.verts.ensure_lookup_table()
            
            for e in edge_indices:
                tgt_bm.edges.new((tgt_bm.verts[i+tgt_v_count] for i in e))
            
            for f in face_indices:
                tgt_bm.faces.new((tgt_bm.verts[i+tgt_v_count] for i in f))
            
            tgt_v_count += len(vertices)
        
        bmesh.ops.remove_doubles(tgt_bm, verts=tgt_bm.verts, dist=self.thickness)
        bmesh.ops.recalc_face_normals(tgt_bm, faces=tgt_bm.faces)
        
        tgt_bm.to_mesh(tgt_me)
        tgt_me.update()
        return {'FINISHED'}

def add_wireframe_gen(self, context):
    self.layout.operator('object.wireframe_gen')
    

def register():
    bpy.utils.register_class(OBJECT_OT_wireframe_gen)
    bpy.types.VIEW3D_MT_object.append(add_wireframe_gen)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_wireframe_gen)
    bpy.types.VIEW3D_MT_object.remove(add_wireframe_gen)


if __name__ == "__main__":
    register()