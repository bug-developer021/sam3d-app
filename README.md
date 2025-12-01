# **Forma3D**

## Photo to 3D Asset Pipeline for Designers and Architects

Transform real objects into clean 3D models ready for Rhino, Blender, Fusion 360, AutoCAD and more.

---

## **Overview**

Forma3D is a pipeline that converts a small set of photos into a clean 3D mesh suitable for design and visualization workflows.
It uses recent advances in vision and reconstruction, including **Meta’s SAM 3D Objects**, segmentation based on **Segment Anything**, and multi-view geometric processing.

This tool is built for **architects, interior designers, product designers, CGI artists and creative studios** who need fast, visually accurate 3D models without complex scanning hardware.

The focus is on **speed, convenience and visual fidelity**, not engineering level dimensional accuracy.

---

## **Installation & Quickstart**

### Backend
1. Install Python 3.10+ and create a virtual environment:
   ```bash
   python -m venv .venv
   .venv\\Scripts\\activate  # Windows
   source .venv/bin/activate  # macOS/Linux
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. (Optional) Skip heavy checkpoint initialization for quick smoke tests:
   ```bash
   set FORMA3D_SKIP_MODEL_INIT=true  # PowerShell: $env:FORMA3D_SKIP_MODEL_INIT="true"
   ```
4. Download model checkpoints when you are ready for real inference:
   ```bash
   # SAM checkpoint (~2.4GB)
   python scripts/download_checkpoints.py

   # SAM 3D Objects checkpoints (requires HF_TOKEN in your env)
   python scripts/download_sam3d_checkpoints.py
   ```
5. Run the API:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### Frontend
1. Install PNPM if needed: `npm install -g pnpm`
2. From `frontend/`:
   ```bash
   pnpm install
   pnpm dev  # or pnpm build && pnpm start for production
   ```

### Tests (checkpoint-light)
- The pipeline defaults to stub mode when checkpoints are missing. You can run the lightweight checks without downloads:
  ```bash
  python test_multiview.py
  python test_optimization.py
  ```
- To exercise the API flow end-to-end, run the backend in one terminal and then:
  ```bash
  python test_api.py
  ```

---

## **What This Pipeline Does**

Given between 3 and 10 user photos taken from different angles, the pipeline produces:

* A visually accurate **3D mesh** of the object
* Clean **quad or triangle topology**
* Optional textures
* Export formats that work in all major design tools
* A scalable backend that can run on GPU servers

The output is ideal for concept design, moodboards, scene kits, visualization, interior renderings, and quick prototyping.

---

## **Core Features**

### **Single or Multi-View Input**

You can upload:

* One photo for a quick single-view reconstruction
* Multiple photos for higher completeness and lower hallucination
* Optional user provided mask or auto segmentation

### **SAM 3D Reconstruction**

Uses SAM 3D Objects to extract shape, appearance and layout priors from each photo. The model is applied per view to give stronger reconstruction than standard photogrammetry in cluttered environments.

### **Segmentation and Masking**

Automatic object masking through SAM or manual input.
Supports extracting only the target object even if the environment is complex.

### **Geometry Fusion**

All per-view reconstructions are aligned and merged into a unified 3D representation.
We use classical geometric registration and surface reconstruction algorithms.

### **Mesh Generation and Cleanup**

The fused geometry is converted into a clean mesh with:

* Poisson surface reconstruction
* Decimation and smoothing
* Optional quad remeshing
* UV optional baking

### **Designer-Friendly Export Formats**

You can export to:

* OBJ
* FBX
* STL
* PLY
* glTF
* STEP or IGES (optional NURBS conversion through Rhino or Fusion)

These formats load directly into:

* Rhino
* Blender
* Fusion 360
* SketchUp
* Unreal Engine
* Unity
* AutoCAD
* SolidWorks (ScanTo3D)

---

## **Intended Use Cases**

### **Architecture and Interiors**

Rapid digitalization of furniture, fixtures, decor and room elements for visualization and concept work.

### **Design and CGI**

Quick 3D assets for moodboards, set design, advertising scenes and creative prototyping.

### **Product Design**

Visual form exploration and early stage concept shape capture.

---

## **What This Is Not**

Forma3D is not intended for:

* Manufacturing grade modeling
* Construction level measurements
* Engineering tolerances
* Reverse engineering of mechanical parts

If exact dimensional accuracy is needed, users should apply a known measurement to scale the model manually.

---

## **API Docs, Logging & Limits**

* Interactive docs: `http://localhost:8000/docs` (Swagger) and `http://localhost:8000/redoc`
* OpenAPI schema: `http://localhost:8000/openapi.json` (useful for SDK generation)
* Structured logging: JSON logs to stdout with `X-Request-ID` headers. Control via `LOG_LEVEL`.
* Rate limits: Upload endpoints default to `30 requests / 60s` per user/IP (override with `RATE_LIMIT_UPLOAD_*` env vars).

---

## **HTTPS/TLS**

Run the API behind a TLS-terminating proxy (recommended):
```nginx
server {
    listen 443 ssl;
    server_name forma3d.yourdomain.com;
    ssl_certificate     /etc/letsencrypt/live/forma3d/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/forma3d/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Request-ID $request_id;
    }
}
```

Or terminate TLS directly in uvicorn for small deployments:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8443 --ssl-keyfile /path/to/key.pem --ssl-certfile /path/to/cert.pem
```

---

## **How It Works**

### 1. **Image Upload**

User uploads several images showing the object from different views such as front, back, side, top.

### 2. **Segmentation**

The object is segmented either automatically via SAM or via manual mask selection.

### 3. **SAM 3D Reconstruction**

Each selected view is processed by SAM 3D Objects to predict the object’s geometry and appearance.

### 4. **Camera Pose Estimation**

Structure from Motion (SfM) is performed to estimate intrinsic and extrinsic camera parameters.

### 5. **Multi-View Fusion**

All single-view predictions are registered into one coordinate system and merged.

### 6. **Mesh Construction**

A surface reconstruction algorithm turns the fused geometry into a mesh.

### 7. **Cleanup**

Mesh is simplified, cleaned, smoothed and optionally quad remeshed.

### 8. **Export**

Final mesh is exported to user specified formats.



## **Roadmap**

* Web interface for drag and drop reconstruction
* Automatic scale calibration
* Interior room reconstruction support
* Real time preview mesh viewer
* GPU inference batching and caching
* API for SaaS products and automation pipelines

---

## **License**

This project uses SAM 3D Objects from Meta Research.
Please review and comply with the SAM License included in the upstream repository.

---

## **Contributing**

Pull requests are welcome.
If you want to contribute new features, integrations or reconstruction modules, please open an issue or start a discussion.

---

If you want, I can also prepare:

* A **logo banner** for the top of the README
* A **diagram** you can embed
* Installation instructions specific to your GPU environment
* A shorter SaaS oriented README for clients

Just tell me what you need.
