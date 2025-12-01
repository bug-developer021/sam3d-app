# Forma3D Roadmap

This roadmap outlines the development plan for **Forma3D**, a photo-to-3D asset pipeline for designers and architects, leveraging Meta's SAM 3D Objects.

## Phase 1: Proof of Concept (PoC) & Core Pipeline
**Goal:** Validate the technology and produce the first 3D mesh from user photos.

- [ ] **Environment Setup**
    - [ ] Set up a GPU-enabled development environment (NVIDIA CUDA support required).
    - [ ] Install dependencies for [SAM 3D Objects](https://github.com/facebookresearch/sam-3d-objects).
    - [ ] Install dependencies for Segment Anything Model (SAM) for masking.

- [ ] **Core Script Development**
    - [ ] Create a Python script `pipeline.py` that accepts an image path.
    - [ ] **Step 1: Segmentation**: Implement auto-masking using SAM to isolate the main object.
    - [ ] **Step 2: Reconstruction**: Pass the image + mask to SAM 3D Objects to generate the 3D representation (Gaussian Splats).
    - [ ] **Step 3: Conversion**: Implement a conversion step from Gaussian Splats (`.ply`) to a mesh format (`.obj` / `.glb`) using algorithms like Poisson Surface Reconstruction or Marching Cubes, as standard design tools need meshes, not splats.

- [ ] **CLI Tool**
    - [ ] Wrap the pipeline in a CLI: `python main.py --input image.jpg --output model.obj`.
    - [ ] Verify output quality in Blender/Rhino.

## Phase 2: Backend Architecture & API
**Goal:** Create a scalable backend service to handle multiple user requests.

- [ ] **API Development (FastAPI)**
    - [ ] Design `POST /upload` endpoint to accept images.
    - [ ] Design `GET /status/{job_id}` to check processing status.
    - [ ] Design `GET /download/{job_id}` to retrieve the final model.

- [ ] **Task Queue System**
    - [ ] Integrate **Redis** and **Celery** (or BullMQ) to handle long-running 3D generation tasks asynchronously.
    - [ ] Ensure GPU resources are managed (one job per GPU or batched if possible).

- [ ] **Storage Layer**
    - [ ] Set up object storage (S3 / MinIO) for:
        - [ ] Raw input images.
        - [ ] Intermediate masks/splats.
        - [ ] Final exported meshes.

## Phase 3: Frontend & User Interface
**Goal:** Build a user-friendly web interface for designers.

- [ ] **Web Application (Next.js / React)**
    - [ ] **Upload Zone**: Drag-and-drop interface for single or multiple images.
    - [ ] **Gallery**: View past generations.

- [ ] **3D Viewer Integration**
    - [ ] Integrate **Three.js** or **React Three Fiber**.
    - [ ] Implement a viewer to preview the `.glb` / `.obj` result directly in the browser before downloading.

- [ ] **Export Options**
    - [ ] UI controls to select export format (OBJ, FBX, STL, GLTF).

## Phase 4: Advanced Features & Optimization
**Goal:** Improve quality and support multi-view inputs as promised in the vision.

- [ ] **Multi-View Fusion**
    - [ ] Research and implement alignment of multiple SAM 3D outputs from different angles.
    - [ ] Implement a fusion algorithm to merge these into a single, complete mesh (filling gaps from the single-view approach).

- [ ] **Mesh Optimization**
    - [ ] Implement **Quad Remeshing** (e.g., using Instant Meshes or similar libraries) for cleaner topology.
    - [ ] Add **Texture Baking** to transfer colors from the Gaussian Splats/Photos onto the final mesh UVs.

- [ ] **Scale Calibration**
    - [ ] Add UI for users to define a known dimension (e.g., "this height is 2 meters") to scale the model accurately.

## Phase 5: Production & Scaling
**Goal:** Launch the SaaS product.

- [ ] **Deployment**
    - [ ] Containerize the application (Docker).
    - [ ] Deploy to a GPU cloud provider (AWS EC2 g4dn/g5, Lambda Labs, or RunPod).

- [ ] **User Management**
    - [ ] Implement Authentication (Auth0 / Supabase).
    - [ ] Set up usage limits and subscription tiers.

- [ ] **Documentation**
    - [ ] Create user guides for "Best Practices for Photography" to ensure high-quality results.
