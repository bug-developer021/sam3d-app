import os
import shutil
import open3d as o3d
import numpy as np
from pipeline import Forma3DPipeline
from unittest.mock import MagicMock

# Ensure heavy model initialization is skipped during tests
os.environ.setdefault("FORMA3D_SKIP_MODEL_INIT", "true")

def create_dummy_ply(filename):
    pcd = o3d.geometry.PointCloud()
    points = np.random.rand(100, 3)
    pcd.points = o3d.utility.Vector3dVector(points)
    o3d.io.write_point_cloud(filename, pcd)
    return filename

def test_multiview():
    # Setup
    if not os.path.exists("test_image.jpg"):
        # Create dummy image if not exists
        import cv2
        cv2.imwrite("test_image.jpg", np.zeros((100, 100, 3), dtype=np.uint8))

    img1 = "test_image.jpg"
    img2 = "test_image_2.jpg"
    shutil.copy(img1, img2)
    
    output_base = "test_multiview_output"
    
    pipeline = Forma3DPipeline()
    
    # Mock segment to return a dummy mask
    pipeline.segment = MagicMock(return_value=np.zeros((100, 100), dtype=bool))
    
    # Mock reconstruct to return a dummy PLY
    dummy_ply = "dummy_view.ply"
    create_dummy_ply(dummy_ply)
    pipeline.reconstruct = MagicMock(return_value=dummy_ply)
    
    print("Running multi-view pipeline with mocks...")
    pipeline.run_multiview([img1, img2], output_base)
    
    # Check outputs
    if os.path.exists(output_base + ".ply"):
        print("SUCCESS: Fused PLY generated.")
    else:
        print("FAILURE: Fused PLY not generated.")
        
    if os.path.exists(output_base + ".obj"):
        print("SUCCESS: Fused OBJ generated.")
    else:
        print("FAILURE: Fused OBJ not generated.")

    # Cleanup
    if os.path.exists(img2):
        os.remove(img2)
    if os.path.exists(dummy_ply):
        os.remove(dummy_ply)

if __name__ == "__main__":
    test_multiview()
