import os
import open3d as o3d
import numpy as np
from scaling import MeshScaler

def create_dummy_mesh(filename, size=1.0):
    # Create a simple cube of size 1
    mesh = o3d.geometry.TriangleMesh.create_box(width=size, height=size, depth=size)
    o3d.io.write_triangle_mesh(filename, mesh)
    return filename

def test_scaling():
    input_mesh = "test_scale_input.obj"
    
    # Create dummy mesh of size 1
    create_dummy_mesh(input_mesh, size=1.0)
    
    scaler = MeshScaler()
    
    print("Running scaling test...")
    target_size = 5.0
    
    # Scale to 5.0 along Y axis
    success = scaler.scale_mesh(input_mesh, target_size, axis='y')
    
    if success:
        # Verify
        mesh = o3d.io.read_triangle_mesh(input_mesh)
        bbox = mesh.get_axis_aligned_bounding_box()
        extent = bbox.get_extent()
        print(f"New extent: {extent}")
        
        if np.isclose(extent[1], target_size, atol=1e-3):
            print("SUCCESS: Mesh scaled correctly.")
        else:
            print(f"FAILURE: Mesh size {extent[1]} does not match target {target_size}.")
    else:
        print("FAILURE: Scaling operation failed.")

    # Cleanup
    if os.path.exists(input_mesh):
        os.remove(input_mesh)

if __name__ == "__main__":
    test_scaling()
