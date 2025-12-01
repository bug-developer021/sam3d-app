import open3d as o3d
import numpy as np
import os

class MeshScaler:
    def __init__(self):
        pass

    def scale_mesh(self, mesh_path, target_dimension, axis='y'):
        """
        Scales the mesh so that its dimension along the specified axis matches target_dimension.
        axis: 'x', 'y', 'z', or 'max' (longest dimension)
        """
        print(f"Scaling mesh {mesh_path} to {target_dimension} along {axis} axis...")
        
        try:
            mesh = o3d.io.read_triangle_mesh(mesh_path)
            if not mesh.has_triangles():
                print("Error: Mesh has no triangles.")
                return False

            # Compute bounding box
            bbox = mesh.get_axis_aligned_bounding_box()
            extent = bbox.get_extent() # [x_size, y_size, z_size]
            
            current_size = 0.0
            if axis == 'x':
                current_size = extent[0]
            elif axis == 'y':
                current_size = extent[1]
            elif axis == 'z':
                current_size = extent[2]
            elif axis == 'max':
                current_size = np.max(extent)
            else:
                print(f"Invalid axis: {axis}")
                return False
            
            if current_size == 0:
                print("Error: Mesh has zero size.")
                return False
            
            scale_factor = target_dimension / current_size
            print(f"Current size: {current_size}, Scale factor: {scale_factor}")
            
            # Scale around center
            center = bbox.get_center()
            mesh.scale(scale_factor, center)
            
            # Save (overwrite)
            o3d.io.write_triangle_mesh(mesh_path, mesh)
            print(f"Scaled mesh saved to {mesh_path}")
            return True
            
        except Exception as e:
            print(f"Scaling failed: {e}")
            return False
