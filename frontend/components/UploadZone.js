"use client";

import React, { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import {
  Upload,
  Loader2,
  Image,
  AlertCircle,
  CheckCircle,
  Clock3,
} from "lucide-react";
import {
  createProject,
  uploadImages,
  startProcessing,
} from "@/services/api";
import { useAuth } from "@/hooks/useAuth";

export default function UploadZone({ onUploadComplete }) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(null);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [lastJobId, setLastJobId] = useState(null);
  const [projectName, setProjectName] = useState("");
  const { apiKey, setApiKey } = useAuth();

  const onDrop = useCallback(
    async (acceptedFiles) => {
      if (!acceptedFiles.length) return;

      if (!apiKey) {
        setError("API key required. Add your X-API-Key to continue.");
        return;
      }

      setSelectedFiles(acceptedFiles);
      setUploading(true);
      setError(null);
      setUploadProgress(0);

      try {
        let projectId = null;
        if (projectName.trim()) {
          const project = await createProject(projectName.trim(), "", apiKey);
          projectId = project?.id;
        }

        const response = await uploadImages(projectId, acceptedFiles, apiKey);

        // startProcessing is a no-op if backend auto-enqueues during upload
        try {
          if (projectId && response?.project_id) {
            await startProcessing(projectId, apiKey);
          }
        } catch (processErr) {
          console.debug("Process enqueue skipped", processErr);
        }

        setLastJobId(response?.job_id || null);
        setSelectedFiles([]);
        if (onUploadComplete) onUploadComplete();
      } catch (err) {
        console.error("Upload failed", err);
        const detail = err?.response?.data?.detail || err?.message || err?.detail;
        const message = Array.isArray(detail)
          ? detail.map((d) => d.msg || d).join(", ")
          : detail || "Upload failed. Please try again.";
        setError(message);
      } finally {
        setUploading(false);
        setUploadProgress(null);
      }
    },
    [apiKey, onUploadComplete, projectName]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/*": [".jpeg", ".jpg", ".png", ".webp", ".bmp", ".tiff", ".tif"],
    },
    maxFiles: 20,
    multiple: true,
    disabled: uploading,
  });

  return (
    <div className="w-full rounded-3xl border border-white/5 bg-white/[0.02] p-8 backdrop-blur-sm transition hover:bg-white/[0.04]">
      <div className="mb-6 grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <label className="text-xs uppercase tracking-wide text-slate-400">Project name</label>
          <input
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder="Optional: e.g. Ceramic Vase"
            className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-violet-500 focus:outline-none"
            disabled={uploading}
          />
        </div>
        <div className="space-y-2">
          <label className="text-xs uppercase tracking-wide text-slate-400">API Key</label>
          <div className="flex gap-2">
            <input
              value={apiKey || ""}
              onChange={(e) => {
                setError(null);
                setApiKey(e.target.value);
              }}
              placeholder="Enter your X-API-Key"
              className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-violet-500 focus:outline-none"
              disabled={uploading}
            />
          </div>
          <p className="text-xs text-slate-500">
            Stored locally only. Required for create/upload/process/download operations.
          </p>
        </div>
      </div>

      <div className="mb-6 flex items-center justify-between gap-2">
        <div>
          <h3 className="text-xl font-medium text-white">
            Drop your references
          </h3>
          <p className="text-sm text-slate-400">
            Supports JPG, PNG, WEBP. Max 20 files.
          </p>
        </div>
        {lastJobId && (
          <div className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-200">
            Last job: {lastJobId.slice(0, 8)}...
          </div>
        )}
      </div>

      <div
        {...getRootProps()}
        className={`relative flex min-h-[280px] flex-col items-center justify-center gap-4 rounded-2xl border border-dashed transition duration-300 ${
          isDragActive
            ? "border-violet-400 bg-violet-500/10"
            : "border-white/10 bg-white/[0.02] hover:border-violet-500/50 hover:bg-white/[0.05]"
        } ${uploading ? "cursor-wait opacity-70" : "cursor-pointer"}`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-4 text-center">
          {uploading ? (
            <Loader2 className="h-12 w-12 animate-spin text-violet-400" />
          ) : (
            <div className="rounded-full bg-white/5 p-4 ring-1 ring-white/10 transition group-hover:bg-white/10">
              <Upload className="h-8 w-8 text-slate-200" />
            </div>
          )}
          <div className="space-y-1">
            <p className="text-lg font-medium text-white">
              {uploading ? "Uploading..." : "Click to upload or drag and drop"}
            </p>
            <p className="text-sm text-slate-400">
              Auto-starts processing immediately.
            </p>
          </div>
        </div>
      </div>

      {uploadProgress !== null && (
        <div className="mt-6 h-1 w-full overflow-hidden rounded-full bg-white/5">
          <div
            className="h-full rounded-full bg-violet-500 transition-all duration-300"
            style={{ width: `${uploadProgress}%` }}
          />
        </div>
      )}

      {selectedFiles.length > 0 && (
        <div className="mt-6 rounded-xl border border-white/5 bg-black/20 p-4">
          <div className="flex items-center gap-2 text-sm font-medium text-white">
            <Image className="h-4 w-4 text-violet-400" />
            {selectedFiles.length} file{selectedFiles.length > 1 ? "s" : ""}{" "}
            queued
          </div>
          <ul className="mt-3 space-y-2 text-sm text-slate-400">
            {selectedFiles.slice(0, 4).map((file) => (
              <li
                key={file.name}
                className="flex items-center justify-between gap-2"
              >
                <span className="truncate">{file.name}</span>
                <span className="text-xs text-slate-500">
                  {(file.size / 1024 / 1024).toFixed(1)} MB
                </span>
              </li>
            ))}
            {selectedFiles.length > 4 && (
              <li className="text-xs text-slate-500">
                + {selectedFiles.length - 4} more
              </li>
            )}
          </ul>
        </div>
      )}

      {error && (
        <div className="mt-6 inline-flex w-full items-start gap-2 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          <AlertCircle className="mt-0.5 h-4 w-4" />
          <div>{error}</div>
        </div>
      )}
    </div>
  );
}
