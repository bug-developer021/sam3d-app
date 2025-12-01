# Uninstall existing versions first to avoid conflicts
pip uninstall -y torch torchvision pytorch3d

# Install PyTorch 2.5.1 and Torchvision 0.20.1 with CUDA 12.1 support
pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu121

# Install Pytorch3D from the specific wheel builder (must match PyTorch version)
pip install "pytorch3d==0.7.8+pt2.5.1cu121" --extra-index-url https://miropsota.github.io/torch_packages_builder

# Verify installation
python scripts/test_pytorch3d.py
