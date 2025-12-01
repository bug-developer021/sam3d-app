"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { pollJobStatus } from "@/services/api";
import { useAuth } from "./useAuth";

export function useJobPolling(jobId, intervalMs = 5000) {
  const { apiKey } = useAuth();
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const timerRef = useRef(null);

  const stop = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  useEffect(() => {
    if (!jobId || !apiKey) return undefined;

    const fetchStatus = async () => {
      try {
        const data = await pollJobStatus(jobId, apiKey);
        setStatus(data);
        if (data.status === "completed" || data.status === "failed") {
          stop();
        }
      } catch (err) {
        setError(err);
      }
    };

    fetchStatus();
    timerRef.current = setInterval(fetchStatus, intervalMs);

    return () => stop();
  }, [jobId, apiKey, intervalMs]);

  return useMemo(() => ({ status, error, stop }), [status, error]);
}

