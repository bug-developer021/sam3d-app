import os
import sys
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Download SAM 3D Objects checkpoints from Hugging Face.")
    parser.add_argument("--token", type=str, help="Hugging Face User Access Token (Read). If not provided, will look for HF_TOKEN env var or prompt user.")
    parser.add_argument("--output-dir", type=str, default="sam-3d-objects/checkpoints", help="Directory to save checkpoints to.")
    args = parser.parse_args()

    # Determine target directory
    # If script is run from root, default is sam-3d-objects/checkpoints
    # If script is run from scripts/, we might need to adjust, but let's assume run from root for now or use absolute path logic if needed.
    # Better to resolve relative to the script location if possible, or just trust the user/default.
    # Let's try to be smart: find the project root.
    
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    # Default output dir relative to project root if not absolute
    output_path = Path(args.output_dir)
    if not output_path.is_absolute():
        output_path = project_root / output_path
        
    print(f"Target checkpoint directory: {output_path}")

    # Check for huggingface_hub
    try:
        from huggingface_hub import hf_hub_download, login
    except ImportError:
        print("Error: huggingface_hub is not installed.")
        print("Please install it with: pip install huggingface_hub")
        sys.exit(1)

    # Handle Authentication
    token = args.token or os.environ.get("HF_TOKEN")
    
    if not token:
        print("\n⚠️  Authentication Required ⚠️")
        print("The 'facebook/sam-3d-objects' model is gated.")
        print("You need to accept the terms at: https://huggingface.co/facebook/sam-3d-objects")
        print("And provide a User Access Token (Read) from: https://huggingface.co/settings/tokens")
        token = input("\nEnter your Hugging Face Token: ").strip()
        if not token:
            print("Token is required. Exiting.")
            sys.exit(1)
    
    print(f"\nLogging in to Hugging Face...")
    try:
        login(token=token, add_to_git_credential=False)
    except Exception as e:
        print(f"Failed to login: {e}")
        sys.exit(1)

    # Download files
    repo_id = "facebook/sam-3d-objects"
    # The structure in the repo seems to be flat or specific? 
    # Based on setup.md:
    # hf download ... facebook/sam-3d-objects
    # mv checkpoints/hf-download/checkpoints checkpoints/hf
    # It seems the repo contains a 'checkpoints' folder? Or we just download specific files?
    # Let's look at the demo.py: config_path = f"checkpoints/{tag}/pipeline.yaml" (tag="hf")
    # So we need `sam-3d-objects/checkpoints/hf/pipeline.yaml`
    
    # Let's try to download the entire repo content to a temp dir and move, or just download specific files if we knew them.
    # But `snapshot_download` is better for entire repo.
    
    from huggingface_hub import snapshot_download

    print(f"\nDownloading checkpoints from {repo_id}...")
    try:
        # We want the contents of the repo to end up in `sam-3d-objects/checkpoints/hf`
        # If the repo HAS a `checkpoints` folder inside it, we need to be careful.
        # The setup.md says:
        # mv checkpoints/${TAG}-download/checkpoints checkpoints/${TAG}
        # This implies the repo has a `checkpoints` folder at its root.
        
        # Let's download to a temporary location first
        download_path = output_path / "temp_download"
        snapshot_download(repo_id=repo_id, local_dir=download_path, local_dir_use_symlinks=False)
        
        # Now move the files
        # We expect download_path/checkpoints to exist
        source_checkpoints = download_path / "checkpoints"
        target_hf_dir = output_path / "hf"
        
        if source_checkpoints.exists():
            print(f"Found 'checkpoints' directory in download. Moving to {target_hf_dir}...")
            if target_hf_dir.exists():
                print(f"Warning: {target_hf_dir} already exists. Merging/Overwriting...")
            
            import shutil
            # shutil.move can be tricky with existing dirs, let's use copytree with dirs_exist_ok=True (Python 3.8+)
            shutil.copytree(source_checkpoints, target_hf_dir, dirs_exist_ok=True)
            
            # Cleanup temp
            import shutil
            shutil.rmtree(download_path)
            print("Download and extraction complete!")
            
        else:
            print(f"Structure mismatch: 'checkpoints' directory not found in {download_path}")
            print(f"Contents: {[p.name for p in download_path.iterdir()]}")
            print("You may need to manually arrange the files.")
            
    except Exception as e:
        print(f"An error occurred during download: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
