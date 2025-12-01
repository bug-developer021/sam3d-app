#!/usr/bin/env python3
"""
Forma3D System Health Check Script

This script tests whether all components of the Forma3D system are working correctly.
It checks:
1. Backend API server connectivity
2. Frontend server connectivity
3. API endpoints (health, ready, root)
4. File upload functionality
5. Job status tracking
6. File system structure
7. Python dependencies
8. Docker availability (optional)

Usage:
    python test_system.py [--full] [--backend-only] [--frontend-only]

Options:
    --full          Run all tests including upload test (requires test image)
    --backend-only  Only test backend components
    --frontend-only Only test frontend components
    --verbose       Show detailed output
"""

import sys
import os
import time
import json
import argparse
import subprocess
from datetime import datetime
from typing import Tuple, List, Dict, Any, Optional

# Avoid heavy model initialization
os.environ.setdefault("FORMA3D_SKIP_MODEL_INIT", "true")

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def colorize(text: str, color: str) -> str:
    """Wrap text in color codes."""
    return f"{color}{text}{Colors.END}"

def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(colorize(f"  {title}", Colors.BOLD + Colors.CYAN))
    print("=" * 60)

def print_test(name: str, passed: bool, message: str = ""):
    """Print a test result."""
    status = colorize("✓ PASS", Colors.GREEN) if passed else colorize("✗ FAIL", Colors.RED)
    msg = f" - {message}" if message else ""
    print(f"  {status}  {name}{msg}")

def print_warning(message: str):
    """Print a warning message."""
    print(f"  {colorize('⚠ WARN', Colors.YELLOW)}  {message}")

def print_info(message: str):
    """Print an info message."""
    print(f"  {colorize('ℹ INFO', Colors.BLUE)}  {message}")


class SystemTester:
    """Main system tester class."""
    
    def __init__(self, backend_url: str = "http://localhost:8000", 
                 frontend_url: str = "http://localhost:3000",
                 verbose: bool = False):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.verbose = verbose
        self.results: List[Dict[str, Any]] = []
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
    def add_result(self, category: str, test: str, passed: bool, message: str = ""):
        """Record a test result."""
        self.results.append({
            "category": category,
            "test": test,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
    def check_python_dependencies(self) -> Tuple[int, int]:
        """Check if required Python packages are installed."""
        print_header("Python Dependencies")
        
        required_packages = [
            ("fastapi", "FastAPI web framework"),
            ("uvicorn", "ASGI server"),
            ("pydantic", "Data validation"),
            ("pydantic_settings", "Settings management"),
            ("requests", "HTTP client"),
            ("numpy", "Numerical computing"),
            ("PIL", "Image processing (Pillow)"),
            ("cv2", "Computer vision (OpenCV)"),
            ("open3d", "3D processing"),
            ("trimesh", "Mesh processing"),
            ("torch", "PyTorch deep learning"),
            ("torchvision", "PyTorch vision"),
            ("scipy", "Scientific computing"),
            ("matplotlib", "Plotting"),
            ("tqdm", "Progress bars"),
            ("hydra", "Configuration management"),
        ]
        
        passed = 0
        failed = 0
        
        for package, description in required_packages:
            try:
                if package == "PIL":
                    import PIL
                    version = PIL.__version__
                elif package == "cv2":
                    import cv2
                    version = cv2.__version__
                elif package == "hydra":
                    import hydra
                    version = getattr(hydra, '__version__', 'installed')
                else:
                    mod = __import__(package)
                    version = getattr(mod, '__version__', 'installed')
                print_test(f"{description} ({package})", True, f"v{version}")
                self.add_result("dependencies", package, True, f"v{version}")
                passed += 1
            except ImportError as e:
                print_test(f"{description} ({package})", False, str(e))
                self.add_result("dependencies", package, False, str(e))
                failed += 1
                
        # Check optional packages
        print("\n  Optional packages:")
        optional_packages = [
            ("pytorch3d", "PyTorch3D (3D deep learning)"),
        ]
        
        for package, description in optional_packages:
            try:
                mod = __import__(package)
                version = getattr(mod, '__version__', 'installed')
                print_test(f"{description}", True, f"v{version}")
            except ImportError:
                print_warning(f"{description} not installed (required for full 3D reconstruction)")
                
        return passed, failed
    
    def check_file_system(self) -> Tuple[int, int]:
        """Check required directories and files exist."""
        print_header("File System Structure")
        
        required_dirs = [
            ("storage", "Storage root directory"),
            ("storage/uploads", "Upload directory"),
            ("storage/outputs", "Output directory"),
            ("app", "Application package"),
            ("app/api", "API module"),
            ("app/core", "Core module"),
            ("app/services", "Services module"),
            ("frontend", "Frontend application"),
        ]
        
        required_files = [
            ("app/main.py", "FastAPI application"),
            ("app/api/api.py", "API router"),
            ("app/api/endpoints/jobs.py", "Jobs endpoints"),
            ("app/core/config.py", "Configuration"),
            ("requirements.txt", "Python requirements"),
            ("frontend/package.json", "Frontend package.json"),
        ]
        
        passed = 0
        failed = 0
        
        print("\n  Directories:")
        for dir_path, description in required_dirs:
            full_path = os.path.join(self.base_dir, dir_path)
            exists = os.path.isdir(full_path)
            print_test(f"{description} ({dir_path})", exists)
            self.add_result("filesystem", f"dir:{dir_path}", exists)
            if exists:
                passed += 1
            else:
                failed += 1
                
        print("\n  Files:")
        for file_path, description in required_files:
            full_path = os.path.join(self.base_dir, file_path)
            exists = os.path.isfile(full_path)
            print_test(f"{description}", exists)
            self.add_result("filesystem", f"file:{file_path}", exists)
            if exists:
                passed += 1
            else:
                failed += 1
                
        return passed, failed
    
    def check_backend_server(self, timeout: int = 5) -> Tuple[int, int]:
        """Check if backend server is running and responsive."""
        print_header("Backend Server")
        
        import requests
        
        passed = 0
        failed = 0
        
        # Test root endpoint
        try:
            resp = requests.get(f"{self.backend_url}/", timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                print_test("Root endpoint (/)", True, data.get("message", "OK"))
                self.add_result("backend", "root", True)
                passed += 1
            else:
                print_test("Root endpoint (/)", False, f"Status: {resp.status_code}")
                self.add_result("backend", "root", False)
                failed += 1
        except requests.exceptions.ConnectionError:
            print_test("Root endpoint (/)", False, "Connection refused - is the server running?")
            self.add_result("backend", "root", False, "Connection refused")
            failed += 1
            return passed, failed + 4  # Skip other tests if server not running
        except Exception as e:
            print_test("Root endpoint (/)", False, str(e))
            self.add_result("backend", "root", False, str(e))
            failed += 1
            return passed, failed + 4
            
        # Test health endpoint
        try:
            resp = requests.get(f"{self.backend_url}/health", timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status", "unknown")
                print_test("Health endpoint (/health)", status == "healthy", f"Status: {status}")
                self.add_result("backend", "health", status == "healthy")
                passed += 1 if status == "healthy" else 0
                failed += 0 if status == "healthy" else 1
            else:
                print_test("Health endpoint (/health)", False, f"Status: {resp.status_code}")
                self.add_result("backend", "health", False)
                failed += 1
        except Exception as e:
            print_test("Health endpoint (/health)", False, str(e))
            self.add_result("backend", "health", False, str(e))
            failed += 1
            
        # Test ready endpoint
        try:
            resp = requests.get(f"{self.backend_url}/ready", timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status", "unknown")
                checks = data.get("checks", {})
                all_ready = all(checks.values()) if checks else False
                print_test("Readiness endpoint (/ready)", all_ready, f"Status: {status}")
                if self.verbose and checks:
                    for check, value in checks.items():
                        print_info(f"  {check}: {value}")
                self.add_result("backend", "ready", all_ready)
                passed += 1 if all_ready else 0
                failed += 0 if all_ready else 1
            else:
                print_test("Readiness endpoint (/ready)", False, f"Status: {resp.status_code}")
                self.add_result("backend", "ready", False)
                failed += 1
        except Exception as e:
            print_test("Readiness endpoint (/ready)", False, str(e))
            self.add_result("backend", "ready", False, str(e))
            failed += 1
            
        # Test API docs endpoint
        try:
            resp = requests.get(f"{self.backend_url}/docs", timeout=timeout)
            docs_available = resp.status_code == 200
            print_test("API docs (/docs)", docs_available)
            self.add_result("backend", "docs", docs_available)
            passed += 1 if docs_available else 0
            failed += 0 if docs_available else 1
        except Exception as e:
            print_test("API docs (/docs)", False, str(e))
            self.add_result("backend", "docs", False, str(e))
            failed += 1
            
        # Test OpenAPI schema
        try:
            resp = requests.get(f"{self.backend_url}/openapi.json", timeout=timeout)
            if resp.status_code == 200:
                schema = resp.json()
                has_paths = "paths" in schema
                print_test("OpenAPI schema (/openapi.json)", has_paths, f"{len(schema.get('paths', {}))} endpoints")
                self.add_result("backend", "openapi", has_paths)
                passed += 1 if has_paths else 0
                failed += 0 if has_paths else 1
            else:
                print_test("OpenAPI schema (/openapi.json)", False, f"Status: {resp.status_code}")
                self.add_result("backend", "openapi", False)
                failed += 1
        except Exception as e:
            print_test("OpenAPI schema (/openapi.json)", False, str(e))
            self.add_result("backend", "openapi", False, str(e))
            failed += 1
            
        return passed, failed
    
    def check_api_endpoints(self, timeout: int = 5) -> Tuple[int, int]:
        """Check API endpoints functionality."""
        print_header("API Endpoints")
        
        import requests
        
        passed = 0
        failed = 0
        api_base = f"{self.backend_url}/api/v1"
        
        # Test jobs list endpoint
        try:
            resp = requests.get(f"{api_base}/jobs/jobs", timeout=timeout)
            if resp.status_code == 200:
                jobs = resp.json()
                print_test("List jobs endpoint", True, f"{len(jobs)} jobs found")
                self.add_result("api", "list_jobs", True)
                passed += 1
            else:
                print_test("List jobs endpoint", False, f"Status: {resp.status_code}")
                self.add_result("api", "list_jobs", False)
                failed += 1
        except requests.exceptions.ConnectionError:
            print_test("List jobs endpoint", False, "Server not reachable")
            self.add_result("api", "list_jobs", False, "Server not reachable")
            failed += 1
            return passed, failed
        except Exception as e:
            print_test("List jobs endpoint", False, str(e))
            self.add_result("api", "list_jobs", False, str(e))
            failed += 1
            
        # Test non-existent job status (should return 404)
        try:
            resp = requests.get(f"{api_base}/jobs/status/nonexistent-job-id", timeout=timeout)
            correct_response = resp.status_code == 404
            print_test("Job not found returns 404", correct_response, f"Status: {resp.status_code}")
            self.add_result("api", "job_not_found", correct_response)
            passed += 1 if correct_response else 0
            failed += 0 if correct_response else 1
        except Exception as e:
            print_test("Job not found returns 404", False, str(e))
            self.add_result("api", "job_not_found", False, str(e))
            failed += 1
            
        # Test upload endpoint exists (OPTIONS)
        try:
            resp = requests.options(f"{api_base}/jobs/upload", timeout=timeout)
            # CORS should be configured
            has_cors = "access-control-allow-origin" in resp.headers or resp.status_code in [200, 204, 405]
            print_test("Upload endpoint exists", has_cors)
            self.add_result("api", "upload_exists", has_cors)
            passed += 1 if has_cors else 0
            failed += 0 if has_cors else 1
        except Exception as e:
            print_test("Upload endpoint exists", False, str(e))
            self.add_result("api", "upload_exists", False, str(e))
            failed += 1
            
        return passed, failed
    
    def check_frontend_server(self, timeout: int = 5) -> Tuple[int, int]:
        """Check if frontend server is running."""
        print_header("Frontend Server")
        
        import requests
        
        passed = 0
        failed = 0
        
        try:
            resp = requests.get(self.frontend_url, timeout=timeout)
            if resp.status_code == 200:
                # Check if it's a Next.js page
                is_nextjs = "next" in resp.text.lower() or "_next" in resp.text
                print_test("Frontend accessible", True, "Next.js app detected" if is_nextjs else "OK")
                self.add_result("frontend", "accessible", True)
                passed += 1
            else:
                print_test("Frontend accessible", False, f"Status: {resp.status_code}")
                self.add_result("frontend", "accessible", False)
                failed += 1
        except requests.exceptions.ConnectionError:
            print_test("Frontend accessible", False, "Connection refused - is the dev server running?")
            self.add_result("frontend", "accessible", False, "Connection refused")
            failed += 1
        except Exception as e:
            print_test("Frontend accessible", False, str(e))
            self.add_result("frontend", "accessible", False, str(e))
            failed += 1
            
        return passed, failed
    
    def check_docker(self) -> Tuple[int, int]:
        """Check Docker availability."""
        print_header("Docker (Optional)")
        
        passed = 0
        failed = 0
        
        # Check Docker installation
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                print_test("Docker installed", True, version)
                self.add_result("docker", "installed", True, version)
                passed += 1
            else:
                print_warning("Docker not available")
                self.add_result("docker", "installed", False)
                failed += 1
                return passed, failed
        except FileNotFoundError:
            print_warning("Docker not installed")
            self.add_result("docker", "installed", False, "Not installed")
            return 0, 0  # Not a failure, just not available
        except Exception as e:
            print_warning(f"Docker check failed: {e}")
            self.add_result("docker", "installed", False, str(e))
            return 0, 0
            
        # Check Docker daemon running
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=10
            )
            daemon_running = result.returncode == 0
            print_test("Docker daemon running", daemon_running)
            self.add_result("docker", "daemon", daemon_running)
            passed += 1 if daemon_running else 0
            failed += 0 if daemon_running else 1
        except Exception as e:
            print_test("Docker daemon running", False, str(e))
            self.add_result("docker", "daemon", False, str(e))
            failed += 1
            
        # Check for project Docker files
        dockerfile_backend = os.path.exists(os.path.join(self.base_dir, "Dockerfile.backend"))
        dockerfile_frontend = os.path.exists(os.path.join(self.base_dir, "frontend", "Dockerfile"))
        docker_compose = os.path.exists(os.path.join(self.base_dir, "docker-compose.yml"))
        
        print_test("Dockerfile.backend exists", dockerfile_backend)
        print_test("Frontend Dockerfile exists", dockerfile_frontend)
        print_test("docker-compose.yml exists", docker_compose)
        
        return passed, failed
    
    def check_upload_flow(self, timeout: int = 30) -> Tuple[int, int]:
        """Test the full upload flow with a test image."""
        print_header("Upload Flow Test")
        
        import requests
        
        passed = 0
        failed = 0
        
        # Check for test image
        test_images = ["test_image.jpg", "test_image.png", "test.jpg", "test.png"]
        test_image_path = None
        
        for img in test_images:
            path = os.path.join(self.base_dir, img)
            if os.path.exists(path):
                test_image_path = path
                break
                
        # If no test image, create a simple one
        if not test_image_path:
            print_info("No test image found, creating a simple test image...")
            try:
                from PIL import Image
                import numpy as np
                
                # Create a simple colored test image
                img_array = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
                img = Image.fromarray(img_array)
                test_image_path = os.path.join(self.base_dir, "test_image_generated.jpg")
                img.save(test_image_path, "JPEG")
                print_test("Test image created", True, test_image_path)
                passed += 1
            except Exception as e:
                print_test("Test image creation", False, str(e))
                self.add_result("upload", "test_image", False, str(e))
                return 0, 1
        else:
            print_test("Test image found", True, os.path.basename(test_image_path))
            passed += 1
            
        api_base = f"{self.backend_url}/api/v1"
        
        # Upload test image
        try:
            with open(test_image_path, "rb") as f:
                resp = requests.post(
                    f"{api_base}/jobs/upload",
                    files={"files": (os.path.basename(test_image_path), f, "image/jpeg")},
                    timeout=timeout
                )
                
            if resp.status_code == 200:
                data = resp.json()
                job_id = data.get("job_id")
                print_test("Image upload", True, f"Job ID: {job_id}")
                self.add_result("upload", "upload", True, job_id)
                passed += 1
            else:
                print_test("Image upload", False, f"Status: {resp.status_code} - {resp.text}")
                self.add_result("upload", "upload", False, resp.text)
                failed += 1
                return passed, failed
        except requests.exceptions.ConnectionError:
            print_test("Image upload", False, "Server not reachable")
            self.add_result("upload", "upload", False, "Server not reachable")
            failed += 1
            return passed, failed
        except Exception as e:
            print_test("Image upload", False, str(e))
            self.add_result("upload", "upload", False, str(e))
            failed += 1
            return passed, failed
            
        # Check job status
        try:
            resp = requests.get(f"{api_base}/jobs/status/{job_id}", timeout=timeout)
            if resp.status_code == 200:
                status = resp.json().get("status")
                print_test("Job status retrieval", True, f"Status: {status}")
                self.add_result("upload", "status", True, status)
                passed += 1
            else:
                print_test("Job status retrieval", False, f"Status: {resp.status_code}")
                self.add_result("upload", "status", False)
                failed += 1
        except Exception as e:
            print_test("Job status retrieval", False, str(e))
            self.add_result("upload", "status", False, str(e))
            failed += 1
            
        # Wait a bit and check if job is processing
        print_info("Waiting for job to process (max 10 seconds)...")
        final_status = None
        for _ in range(5):
            time.sleep(2)
            try:
                resp = requests.get(f"{api_base}/jobs/status/{job_id}", timeout=timeout)
                if resp.status_code == 200:
                    final_status = resp.json().get("status")
                    if final_status in ["completed", "completed_partial", "failed"]:
                        break
            except:
                pass
                
        if final_status:
            success = final_status in ["completed", "completed_partial", "processing", "queued"]
            print_test("Job processing", success, f"Final status: {final_status}")
            self.add_result("upload", "processing", success, final_status)
            passed += 1 if success else 0
            failed += 0 if success else 1
        else:
            print_warning("Could not determine final job status")
            
        return passed, failed
    
    def check_gpu_availability(self) -> Tuple[int, int]:
        """Check CUDA/GPU availability."""
        print_header("GPU/CUDA Status")
        
        passed = 0
        failed = 0
        
        try:
            import torch
            cuda_available = torch.cuda.is_available()
            
            if cuda_available:
                device_count = torch.cuda.device_count()
                device_name = torch.cuda.get_device_name(0)
                cuda_version = torch.version.cuda
                print_test("CUDA available", True, f"{device_count} GPU(s) - {device_name}")
                print_info(f"CUDA version: {cuda_version}")
                print_info(f"PyTorch CUDA: {torch.version.cuda}")
                self.add_result("gpu", "cuda", True, device_name)
                passed += 1
                
                # Check GPU memory
                try:
                    total_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                    print_info(f"GPU Memory: {total_memory:.1f} GB")
                except:
                    pass
            else:
                print_warning("CUDA not available - will use CPU (slower)")
                print_info("For GPU support, install CUDA-enabled PyTorch")
                self.add_result("gpu", "cuda", False, "Not available")
                # Not counting as failure, just warning
        except ImportError:
            print_warning("PyTorch not installed - cannot check GPU")
            self.add_result("gpu", "cuda", False, "PyTorch not installed")
        except Exception as e:
            print_warning(f"GPU check failed: {e}")
            self.add_result("gpu", "cuda", False, str(e))
            
        return passed, failed
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a summary report."""
        total_passed = sum(1 for r in self.results if r["passed"])
        total_failed = sum(1 for r in self.results if not r["passed"])
        
        categories = {}
        for r in self.results:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = {"passed": 0, "failed": 0}
            if r["passed"]:
                categories[cat]["passed"] += 1
            else:
                categories[cat]["failed"] += 1
                
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.results),
                "passed": total_passed,
                "failed": total_failed,
                "success_rate": f"{(total_passed / len(self.results) * 100):.1f}%" if self.results else "N/A"
            },
            "categories": categories,
            "results": self.results
        }
    
    def run_all_tests(self, full: bool = False, backend_only: bool = False, 
                      frontend_only: bool = False) -> int:
        """Run all system tests."""
        print("\n" + colorize("=" * 60, Colors.BOLD))
        print(colorize("    FORMA3D SYSTEM HEALTH CHECK", Colors.BOLD + Colors.CYAN))
        print(colorize("=" * 60, Colors.BOLD))
        print(f"\n  Backend URL:  {self.backend_url}")
        print(f"  Frontend URL: {self.frontend_url}")
        print(f"  Timestamp:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        total_passed = 0
        total_failed = 0
        
        if not frontend_only:
            # Python dependencies
            p, f = self.check_python_dependencies()
            total_passed += p
            total_failed += f
            
            # File system
            p, f = self.check_file_system()
            total_passed += p
            total_failed += f
            
            # GPU status
            p, f = self.check_gpu_availability()
            total_passed += p
            total_failed += f
            
            # Backend server
            p, f = self.check_backend_server()
            total_passed += p
            total_failed += f
            
            # API endpoints
            if p > 0:  # Only if backend is reachable
                p, f = self.check_api_endpoints()
                total_passed += p
                total_failed += f
                
                # Full upload test
                if full:
                    p, f = self.check_upload_flow()
                    total_passed += p
                    total_failed += f
            
            # Docker
            p, f = self.check_docker()
            total_passed += p
            total_failed += f
            
        if not backend_only:
            # Frontend server
            p, f = self.check_frontend_server()
            total_passed += p
            total_failed += f
        
        # Print summary
        print_header("SUMMARY")
        print(f"\n  Total Tests:  {total_passed + total_failed}")
        print(f"  {colorize('Passed:', Colors.GREEN)} {total_passed}")
        print(f"  {colorize('Failed:', Colors.RED)} {total_failed}")
        
        if total_failed == 0:
            print(f"\n  {colorize('✓ All tests passed!', Colors.GREEN + Colors.BOLD)}")
        else:
            print(f"\n  {colorize(f'✗ {total_failed} test(s) failed', Colors.RED + Colors.BOLD)}")
            
        # Generate and optionally save report
        report = self.generate_report()
        report_path = os.path.join(self.base_dir, "system_test_report.json")
        try:
            with open(report_path, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\n  Report saved to: {report_path}")
        except Exception as e:
            print_warning(f"Could not save report: {e}")
            
        print("\n" + "=" * 60 + "\n")
        
        return 0 if total_failed == 0 else 1


def main():
    parser = argparse.ArgumentParser(
        description="Forma3D System Health Check",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_system.py                    # Basic tests
  python test_system.py --full             # Full tests including upload
  python test_system.py --backend-only     # Only test backend
  python test_system.py --verbose          # Show detailed output
        """
    )
    parser.add_argument("--full", action="store_true", help="Run full tests including upload flow")
    parser.add_argument("--backend-only", action="store_true", help="Only test backend components")
    parser.add_argument("--frontend-only", action="store_true", help="Only test frontend components")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--backend-url", default="http://localhost:8000", help="Backend URL")
    parser.add_argument("--frontend-url", default="http://localhost:3000", help="Frontend URL")
    
    args = parser.parse_args()
    
    tester = SystemTester(
        backend_url=args.backend_url,
        frontend_url=args.frontend_url,
        verbose=args.verbose
    )
    
    exit_code = tester.run_all_tests(
        full=args.full,
        backend_only=args.backend_only,
        frontend_only=args.frontend_only
    )
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
