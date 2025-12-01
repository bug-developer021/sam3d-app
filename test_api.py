import requests
import time
import sys
import os

BASE_URL = "http://localhost:8000/api/v1"
# Avoid heavy model initialization when running API smoke test
os.environ.setdefault("FORMA3D_SKIP_MODEL_INIT", "true")

def test_flow():
    # Wait for server to start
    print("Waiting for server...")
    for _ in range(10):
        try:
            requests.get("http://localhost:8000/")
            break
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    else:
        print("Server not reachable")
        sys.exit(1)

    print("Uploading image...")
    if not os.path.exists("test_image.jpg"):
        print("test_image.jpg not found")
        sys.exit(1)

    with open("test_image.jpg", "rb") as f:
        response = requests.post(f"{BASE_URL}/jobs/upload", files={"file": f})
    
    if response.status_code != 200:
        print(f"Upload failed: {response.text}")
        sys.exit(1)
        
    job_id = response.json()["job_id"]
    print(f"Job ID: {job_id}")
    
    while True:
        response = requests.get(f"{BASE_URL}/jobs/status/{job_id}")
        status = response.json()["status"]
        print(f"Status: {status}")
        
        if status in ["completed", "completed_partial", "failed"]:
            break
        
        time.sleep(2)
        
    if status == "failed":
        print(f"Job failed: {response.json().get('error')}")
        # We expect failure because SAM/SAM3D models might not be loaded/downloaded
        # But the API flow should work.
    
    if status in ["completed", "completed_partial"]:
        print("Downloading result (OBJ)...")
        response = requests.get(f"{BASE_URL}/jobs/download/{job_id}")
        if response.status_code == 200:
            with open("result.obj", "wb") as f:
                f.write(response.content)
            print("Result saved to result.obj")
        else:
            print(f"Download (OBJ) failed: {response.text}")

        print("Downloading result (STL)...")
        response = requests.get(f"{BASE_URL}/jobs/download/{job_id}?format=stl")
        if response.status_code == 200:
            with open("result.stl", "wb") as f:
                f.write(response.content)
            print("Result saved to result.stl")
        else:
            print(f"Download (STL) failed: {response.text}")

        print("Downloading result (GLTF)...")
        response = requests.get(f"{BASE_URL}/jobs/download/{job_id}?format=gltf")
        if response.status_code == 200:
            with open("result.gltf", "wb") as f:
                f.write(response.content)
            print("Result saved to result.gltf")
        else:
            print(f"Download (GLTF) failed: {response.text}")

if __name__ == "__main__":
    test_flow()
