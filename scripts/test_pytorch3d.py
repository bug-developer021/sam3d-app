import torch
import os
import sys

# Windows-specific fix for DLL loading
if os.name == 'nt':
    lib_path = os.path.join(os.path.dirname(torch.__file__), 'lib')
    if os.path.exists(lib_path):
        os.add_dll_directory(lib_path)

import pytorch3d
from pytorch3d.structures import Meshes
from pytorch3d.ops import sample_points_from_meshes

def test_pytorch3d():
    print(f"PyTorch version: {torch.__version__}")
    print(f"Pytorch3D version: {pytorch3d.__version__}")
    
    if torch.cuda.is_available():
        device = torch.device("cuda:0")
        print(f"CUDA available: {torch.cuda.get_device_name(0)}")
    else:
        device = torch.device("cpu")
        print("CUDA not available, using CPU")

    # Test basic mesh creation and operations (requires C++ ops)
    # Create a simple triangle mesh
    verts = torch.tensor([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.5, 1.0, 0.0],
        [0.5, 0.5, 1.0]
    ], device=device)
    faces = torch.tensor([
        [0, 1, 2],
        [0, 1, 3],
        [1, 2, 3],
        [0, 2, 3]
    ], device=device)
    
    mesh = Meshes(verts=[verts], faces=[faces])
    print(f"Mesh created successfully. Verts: {mesh.verts_list()[0].shape}, Faces: {mesh.faces_list()[0].shape}")
    
    # Test sample_points_from_meshes (uses C++ ops)
    points = sample_points_from_meshes(mesh, num_samples=100)
    print(f"Point sampling successful. Sampled {points.shape[1]} points")

if __name__ == "__main__":
    try:
        test_pytorch3d()
        print("Pytorch3D test passed!")
    except Exception as e:
        print(f"Pytorch3D test failed: {e}")
        exit(1)
