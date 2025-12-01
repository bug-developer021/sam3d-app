import pymeshlab
import xatlas
import trimesh
import numpy as np
import os
import cv2

class MeshOptimizer:
    def __init__(self):
        pass

    def optimize(self, input_mesh_path, output_mesh_path, target_faces=10000, texture_size=2048):
        """
        Optimizes the mesh by remeshing, unwrapping UVs, and baking texture.
        """
        print(f"Optimizing mesh {input_mesh_path}...")
        
        # Temporary paths
        temp_dir = os.path.dirname(output_mesh_path)
        base_name = os.path.splitext(os.path.basename(output_mesh_path))[0]
        remeshed_path = os.path.join(temp_dir, f"{base_name}_remeshed.obj")
        uv_mesh_path = os.path.join(temp_dir, f"{base_name}_uv.obj")
        texture_path = os.path.splitext(output_mesh_path)[0] + ".png"
        
        try:
            # 1. Load High-Res Mesh (Source)
            print("Loading input mesh...")
            ms = pymeshlab.MeshSet()
            ms.load_new_mesh(input_mesh_path)
            
            # 2. Remesh / Simplify (Target Geometry)
            print(f"Simplifying to {target_faces} faces...")
            try:
                ms.apply_filter('meshing_decimation_quadric_edge_collapse', targetfacenum=target_faces, preserveboundary=True)
                ms.save_current_mesh(remeshed_path)
            except Exception as e:
                print(f"Remeshing failed: {e}")
                # List available filters to help debug
                # print(ms.filter_list())
                raise e
            
            # 3. UV Unwrapping with xatlas
            print("Unwrapping UVs...")
            try:
                mesh = trimesh.load(remeshed_path)
                v_mapping, indices, uvs = xatlas.parametrize(mesh.vertices, mesh.faces)
                
                uv_mesh = trimesh.Trimesh(vertices=mesh.vertices[v_mapping], faces=indices, visual=None)
                uv_mesh.visual = trimesh.visual.TextureVisuals(uv=uvs)
                uv_mesh.export(uv_mesh_path)
            except Exception as e:
                print(f"UV Unwrapping failed: {e}")
                raise e
            
            # 4. Texture Baking with PyMeshLab
            print("Baking texture...")
            try:
                ms_bake = pymeshlab.MeshSet()
                ms_bake.load_new_mesh(input_mesh_path) 
                ms_bake.load_new_mesh(uv_mesh_path)
                
                # Transfer color to texture
                # Source is mesh 0, Target is mesh 1
                ms_bake.transfer_attributes_to_texture_per_vertex(
                    sourcemesh=0,
                    targetmesh=1,
                    textname=os.path.basename(texture_path),
                    textw=texture_size,
                    texth=texture_size,
                    overwrite=True,
                    pullpush=True
                )
                
                ms_bake.save_current_mesh(output_mesh_path)
                
                # Fix texture name if needed
                # PyMeshLab often saves as material_0.png or similar based on internal material name
                # We want it to be os.path.basename(texture_path)
                
                generated_texture = os.path.join(os.path.dirname(output_mesh_path), "material_0.png")
                if os.path.exists(generated_texture):
                    if os.path.exists(texture_path):
                        os.remove(texture_path)
                    os.rename(generated_texture, texture_path)
                    
                    # Update MTL file
                    mtl_path = output_mesh_path + ".mtl"
                    if os.path.exists(mtl_path):
                        with open(mtl_path, 'r') as f:
                            mtl_content = f.read()
                        
                        mtl_content = mtl_content.replace("material_0.png", os.path.basename(texture_path))
                        
                        with open(mtl_path, 'w') as f:
                            f.write(mtl_content)
                            
            except Exception as e:
                print(f"Texture baking failed: {e}")
                raise e
            
            print(f"Optimization complete. Saved to {output_mesh_path}")
            
            # Cleanup
            if os.path.exists(remeshed_path):
                os.remove(remeshed_path)
            if os.path.exists(uv_mesh_path):
                os.remove(uv_mesh_path)
                
            return output_mesh_path
            
        except Exception as e:
            print(f"Optimization failed: {e}")
            # Cleanup on failure
            if os.path.exists(remeshed_path):
                os.remove(remeshed_path)
            if os.path.exists(uv_mesh_path):
                os.remove(uv_mesh_path)
            return None
