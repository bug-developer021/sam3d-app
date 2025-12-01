"use client";

import React, { Suspense, useEffect, useMemo, useState } from "react";
import { Canvas, useLoader } from "@react-three/fiber";
import { OrbitControls, Stage, Html, useProgress, useGLTF } from "@react-three/drei";
import { OBJLoader } from "three/examples/jsm/loaders/OBJLoader";
import { Loader2, AlertCircle } from "lucide-react";
import { API_URL } from "../lib/api";

function OBJModel({ url }) {
  const obj = useLoader(OBJLoader, url);
  const cloned = useMemo(() => obj.clone(), [obj]);
  return <primitive object={cloned} />;
}

function GLBModel({ url }) {
  const { scene } = useGLTF(url);
  const cloned = useMemo(() => scene.clone(), [scene]);
  return <primitive object={cloned} />;
}

function Model({ url }) {
  const extension = url.split(".").pop().toLowerCase();

  if (extension === "glb" || extension === "gltf") {
    return <GLBModel url={url} />;
  } else if (extension === "obj") {
    return <OBJModel url={url} />;
  }

  return (
    <Html center>
      <div className="flex items-center gap-2 rounded-lg bg-black/80 p-3 text-red-200 backdrop-blur-md">
        <AlertCircle className="h-5 w-5" />
        <span>Unsupported format: .{extension}</span>
      </div>
    </Html>
  );
}

function Loader() {
  const { progress } = useProgress();
  return (
    <Html center>
      <div className="flex flex-col items-center gap-2 rounded-xl bg-black/60 p-4 text-white backdrop-blur-md">
        <Loader2 className="h-8 w-8 animate-spin text-violet-400" />
        <span className="text-sm font-medium">{progress.toFixed(0)}% loaded</span>
      </div>
    </Html>
  );
}

export default function ModelViewer({ modelUrl, jobId }) {
  const [showScale, setShowScale] = useState(false);
  const [targetSize, setTargetSize] = useState(2.0);
  const [axis, setAxis] = useState("y");
  const [isScaling, setIsScaling] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [feedback, setFeedback] = useState(null);

  if (!modelUrl) return null;

  const handleScale = async () => {
    if (!jobId) return;
    setIsScaling(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/jobs/${jobId}/scale`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_dimension: parseFloat(targetSize), axis }),
      });

      if (res.ok) {
        setRefreshKey((prev) => prev + 1);
        setShowScale(false);
        setFeedback("Scale applied");
      } else {
        setFeedback("Scaling failed");
      }
    } catch (e) {
      console.error(e);
      setFeedback("Scaling error");
    } finally {
      setIsScaling(false);
    }
  };

  useEffect(() => {
    if (!feedback) return;
    const timer = setTimeout(() => setFeedback(null), 2400);
    return () => clearTimeout(timer);
  }, [feedback]);

  // Append timestamp to bust cache
  const currentUrl = refreshKey > 0 ? `${modelUrl}?t=${Date.now()}` : modelUrl;

  return (
    <div className="group relative h-full w-full overflow-hidden rounded-2xl bg-black/20">
      <Canvas shadows camera={{ position: [0, 0, 4], fov: 50 }} dpr={[1, 2]} key={refreshKey}>
        <Suspense fallback={<Loader />}>
          <Stage environment="city" intensity={0.65} adjustCamera={1.2}>
            <Model url={currentUrl} />
          </Stage>
        </Suspense>
        <OrbitControls makeDefault autoRotate autoRotateSpeed={0.5} />
      </Canvas>

      <div className="absolute left-4 top-4 rounded-full border border-white/10 bg-black/40 px-3 py-1 text-xs font-medium text-white backdrop-blur-md">
        {jobId ? `Job ${jobId.slice(0, 8)}...` : "Live preview"}
      </div>

      <div className="absolute top-4 right-4 flex gap-2">
        <button
          onClick={() => setShowScale(!showScale)}
          className="rounded-lg bg-white/10 px-3 py-1.5 text-sm font-medium text-white backdrop-blur-md transition hover:bg-white/20"
        >
          Scale Model
        </button>
      </div>

      {showScale && (
        <div className="absolute right-4 top-16 w-64 rounded-xl border border-white/10 bg-black/80 p-4 shadow-2xl backdrop-blur-md">
          <h3 className="mb-3 text-sm font-medium text-white">Scale Calibration</h3>

          <div className="space-y-3 text-sm">
            <div>
              <label className="mb-1 block text-xs text-slate-400">Target Dimension</label>
              <div className="flex gap-2">
                <input
                  type="number"
                  value={targetSize}
                  onChange={(e) => setTargetSize(e.target.value)}
                  className="w-full rounded border border-white/10 bg-white/5 px-2 py-1 text-white focus:border-violet-500 focus:outline-none"
                />
                <span className="py-1 text-sm text-slate-500">units</span>
              </div>
            </div>

            <div>
              <label className="mb-1 block text-xs text-slate-400">Axis</label>
              <select
                value={axis}
                onChange={(e) => setAxis(e.target.value)}
                className="w-full rounded border border-white/10 bg-white/5 px-2 py-1 text-white focus:border-violet-500 focus:outline-none"
              >
                <option value="y">Height (Y)</option>
                <option value="x">Width (X)</option>
                <option value="z">Depth (Z)</option>
                <option value="max">Longest Side</option>
              </select>
            </div>

            <button
              onClick={handleScale}
              disabled={isScaling}
              className="mt-2 w-full rounded-lg bg-violet-600 py-1.5 text-sm font-medium text-white shadow-lg transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isScaling ? "Scaling..." : "Apply Scale"}
            </button>
          </div>
        </div>
      )}

      <div className="pointer-events-none absolute bottom-4 right-4 rounded-lg bg-black/50 px-3 py-1.5 text-xs text-slate-300 opacity-0 backdrop-blur-md group-hover:opacity-100 transition">
        Left click: rotate | Right click: pan | Scroll: zoom
      </div>

      {feedback && (
        <div className="absolute bottom-4 left-4 rounded-lg border border-white/10 bg-black/60 px-3 py-1.5 text-xs text-white shadow-lg backdrop-blur-md">
          {feedback}
        </div>
      )}
    </div>
  );
}
