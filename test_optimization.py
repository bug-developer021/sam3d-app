import os
import open3d as o3d
import numpy as np
from optimization import MeshOptimizer

def create_dummy_colored_mesh(filename):
    # Create a simple cube
    mesh = o3d.geometry.TriangleMesh.create_box()
    mesh.compute_vertex_normals()
    
    # Add vertex colors (gradient)
    colors = np.array(mesh.vertices)
    colors = (colors - colors.min()) / (colors.max() - colors.min())
    mesh.vertex_colors = o3d.utility.Vector3dVector(colors)
    
    o3d.io.write_triangle_mesh(filename, mesh)
    return filename

def test_optimization():
    input_mesh = "test_input_mesh.obj"
    output_mesh = "test_optimized_mesh.obj"
    
    # Create dummy mesh
    create_dummy_colored_mesh(input_mesh)
    
    optimizer = MeshOptimizer()
    
    print("Running optimization test...")
    result = optimizer.optimize(input_mesh, output_mesh, target_faces=100) # Low face count for speed/test
    
    if result and os.path.exists(output_mesh):
        print("SUCCESS: Optimized mesh generated.")
        
        # Check for texture
        texture_path = output_mesh.replace(".obj", ".png")
        if os.path.exists(texture_path):
            print(f"SUCCESS: Texture map generated at {texture_path}")
        else:
            print("FAILURE: Texture map not generated.")
            
    else:
        print("FAILURE: Optimization failed.")

    # Cleanup
    if os.path.exists(input_mesh):
        os.remove(input_mesh)

if __name__ == "__main__":
    test_optimization()
