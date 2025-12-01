"use client";

import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  Download,
  Box,
  Clock3,
  AlertCircle,
  Eye,
  X,
  Loader2,
  Filter,
} from "lucide-react";
import ModelViewer from "./ModelViewer";
import { API_URL } from "../lib/api";

const STATUS_PROGRESS = {
  queued: 18,
  processing: 65,
  completed: 100,
  completed_partial: 82,
  failed: 100,
};

const STATUS_ORDER = {
  processing: 0,
  queued: 1,
  completed: 2,
  completed_partial: 2,
  failed: 4,
};

export default function Gallery({ refreshTrigger }) {
  const [jobs, setJobs] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedModel, setSelectedModel] = useState(null);
  const [selectedJobId, setSelectedJobId] = useState(null);
  const [filter, setFilter] = useState("all");
  const [lastUpdated, setLastUpdated] = useState(null);
  const [manualRefresh, setManualRefresh] = useState(false);

  const fetchJobs = async (isManual = false) => {
    if (isManual) setManualRefresh(true);
    try {
      const response = await axios.get(`${API_URL}/api/v1/jobs/jobs`);
      setJobs(response.data || {});
      setLastUpdated(new Date());
    } catch (error) {
      console.error("Failed to fetch jobs", error);
    } finally {
      setLoading(false);
      setManualRefresh(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshTrigger]);

  const filteredJobs = useMemo(() => {
    const entries = Object.entries(jobs);
    return entries
      .filter(([, job]) => {
        if (filter === "all") return true;
        if (filter === "ready") {
          return (
            job.status === "completed" || job.status === "completed_partial"
          );
        }
        return job.status === filter;
      })
      .sort(([, a], [, b]) => {
        const orderA = STATUS_ORDER[a.status] ?? 99;
        const orderB = STATUS_ORDER[b.status] ?? 99;
        return orderA - orderB;
      });
  }, [jobs, filter]);

  const counts = useMemo(() => {
    const base = {
      all: Object.keys(jobs).length,
      ready: 0,
      processing: 0,
      queued: 0,
      failed: 0,
    };
    Object.values(jobs).forEach((job) => {
      if (job.status === "completed" || job.status === "completed_partial") {
        base.ready += 1;
      }
      if (job.status === "processing") base.processing += 1;
      if (job.status === "queued") base.queued += 1;
      if (job.status === "failed") base.failed += 1;
    });
    return base;
  }, [jobs]);

  const emptyState = !loading && filteredJobs.length === 0;

  return (
    <>
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap items-center gap-2">
            {["all", "processing", "queued", "ready", "failed"].map((key) => (
              <button
                key={key}
                onClick={() => setFilter(key)}
                className={`rounded-full border px-4 py-1.5 text-xs font-medium transition ${
                  filter === key
                    ? "border-violet-500/50 bg-violet-500/10 text-violet-200"
                    : "border-white/5 bg-white/[0.02] text-slate-400 hover:border-white/10 hover:text-slate-200"
                }`}
              >
                {key.charAt(0).toUpperCase() + key.slice(1)}{" "}
                <span className="ml-1 opacity-50">({counts[key] ?? 0})</span>
              </button>
            ))}
          </div>
          <button
            onClick={() => fetchJobs(true)}
            className="inline-flex items-center gap-2 rounded-full border border-white/5 bg-white/[0.02] px-4 py-1.5 text-xs font-medium text-slate-300 transition hover:bg-white/[0.05] hover:text-white"
          >
            {manualRefresh ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin text-violet-400" />
            ) : (
              <Clock3 className="h-3.5 w-3.5 text-violet-400" />
            )}
            Refresh
          </button>
        </div>

        {loading && Object.keys(jobs).length === 0 && (
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            {[1, 2, 3].map((key) => (
              <div
                key={key}
                className="h-64 rounded-3xl border border-white/5 bg-white/[0.02]"
              >
                <div className="h-full animate-pulse rounded-3xl bg-white/[0.02]" />
              </div>
            ))}
          </div>
        )}

        {!loading && (
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            {filteredJobs.map(([jobId, job]) => (
              <JobCard
                key={jobId}
                jobId={jobId}
                job={job}
                onView={(url) => {
                  setSelectedModel(url);
                  setSelectedJobId(jobId);
                }}
              />
            ))}
          </div>
        )}

        {emptyState && (
          <div className="flex flex-col items-center justify-center rounded-3xl border border-dashed border-white/10 bg-white/[0.02] py-20 text-center">
            <div className="rounded-full bg-white/5 p-4">
              <Box className="h-6 w-6 text-slate-500" />
            </div>
            <p className="mt-4 text-sm text-slate-400">No generations yet.</p>
            <p className="text-xs text-slate-500">Upload photos to start building.</p>
          </div>
        )}
      </div>

      {selectedModel && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-md p-4">
          <div className="relative w-full max-w-6xl overflow-hidden rounded-3xl border border-white/10 bg-ink shadow-2xl">
            <div className="absolute right-6 top-6 z-10">
              <button
                onClick={() => {
                  setSelectedModel(null);
                  setSelectedJobId(null);
                }}
                className="rounded-full bg-black/50 p-2 text-white backdrop-blur-sm transition hover:bg-black/70"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="h-[80vh] w-full">
              <ModelViewer modelUrl={selectedModel} jobId={selectedJobId} />
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function JobCard({ jobId, job, onView }) {
  const ready =
    job.status === "completed" || job.status === "completed_partial";
  const defaultFormat = job.result ? job.result.split(".").pop() : "obj";
  const [format, setFormat] = useState(defaultFormat || "obj");

  useEffect(() => {
    setFormat(defaultFormat || "obj");
  }, [defaultFormat]);

  const downloadUrl = `${API_URL}/api/v1/jobs/download/${jobId}?format=${format}`;
  const viewUrl = `${downloadUrl}#model.${format}`;
  const progressWidth = `${STATUS_PROGRESS[job.status] || 12}%`;

  return (
    <div className="group relative flex h-full flex-col justify-between rounded-3xl border border-white/5 bg-white/[0.02] p-6 transition hover:border-white/10 hover:bg-white/[0.04]">
      <div>
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-slate-500" title={jobId}>
                #{jobId.slice(0, 8)}
              </span>
              {job.result && (
                <span className="rounded px-1.5 py-0.5 text-[10px] font-medium uppercase text-slate-400 bg-white/5">
                  {job.result.split(".").pop()}
                </span>
              )}
            </div>
            <StatusBadge status={job.status} />
          </div>
        </div>

        <div className="mt-6 space-y-2">
          <div className="flex justify-between text-xs text-slate-500">
            <span>Progress</span>
            <span>{Math.round(parseFloat(progressWidth))}%</span>
          </div>
          <div className="h-1 w-full overflow-hidden rounded-full bg-white/5">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                job.status === "failed"
                  ? "bg-red-500"
                  : job.status === "processing"
                  ? "bg-violet-500"
                  : ready
                  ? "bg-emerald-500"
                  : "bg-amber-500"
              }`}
              style={{ width: progressWidth }}
            />
          </div>
        </div>

        {job.error && (
          <div className="mt-4 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-xs text-red-200">
            {job.error}
          </div>
        )}
      </div>

      <div className="mt-6 flex items-center justify-between gap-3 border-t border-white/5 pt-4">
        <select
          className="bg-transparent text-xs font-medium text-slate-400 focus:outline-none"
          value={format}
          onChange={(e) => setFormat(e.target.value)}
        >
          <option value="obj">OBJ</option>
          <option value="stl">STL</option>
          <option value="gltf">GLTF</option>
          <option value="glb">GLB</option>
        </select>

        <div className="flex gap-2">
          <button
            onClick={() => onView(viewUrl)}
            disabled={!ready}
            className="rounded-lg p-2 text-slate-400 transition hover:bg-white/5 hover:text-white disabled:opacity-30"
            title="View 3D Model"
          >
            <Eye className="h-4 w-4" />
          </button>
          <button
            onClick={() => window.location.assign(downloadUrl)}
            disabled={!ready}
            className="rounded-lg p-2 text-violet-400 transition hover:bg-violet-500/10 hover:text-violet-300 disabled:opacity-30"
            title="Download"
          >
            <Download className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  const styles = {
    queued: "text-amber-400",
    processing: "text-violet-400",
    completed: "text-emerald-400",
    completed_partial: "text-emerald-400",
    failed: "text-red-400",
  };

  const labels = {
    queued: "Queued",
    processing: "Processing",
    completed: "Ready",
    completed_partial: "Ready (Partial)",
    failed: "Failed",
  };

  return (
    <div className={`text-sm font-medium ${styles[status] || "text-slate-400"}`}>
      {labels[status] || status}
    </div>
  );
}
