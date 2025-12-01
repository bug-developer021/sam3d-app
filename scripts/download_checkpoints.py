import os
import sys
import requests
from tqdm import tqdm

def download_checkpoint(url, dest_path):
    if os.path.exists(dest_path):
        print(f"Checkpoint already exists at {dest_path}")
        return

    print(f"Downloading checkpoint from {url} to {dest_path}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        
        block_size = 1024 # 1 Kibibyte
        t = tqdm(total=total_size, unit='iB', unit_scale=True)
        
        with open(dest_path, 'wb') as f:
            for data in response.iter_content(block_size):
                t.update(len(data))
                f.write(data)
        t.close()
        
        if total_size != 0 and t.n != total_size:
            print("ERROR, something went wrong")
            
        print("Download complete.")
    except Exception as e:
        print(f"Failed to download checkpoint: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path) # Clean up partial download
        raise

if __name__ == "__main__":
    url = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth"
    # Determine destination path relative to project root
    # Assuming this script is in scripts/ and we want the file in root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dest_path = os.path.join(project_root, "sam_vit_h_4b8939.pth")
    
    download_checkpoint(url, dest_path)
