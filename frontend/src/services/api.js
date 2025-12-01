const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

export const ENDPOINTS = {
  projects: `${API_URL}/api/v1/projects`,
  jobs: `${API_URL}/api/v1/jobs`,
};

function buildHeaders(apiKey, extra = {}) {
  const headers = { ...extra };
  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }
  return headers;
}

async function handleResponse(response, responseType = "json") {
  if (!response.ok) {
    let detail;
    try {
      const data = await response.json();
      detail = data?.detail || data?.error || response.statusText;
    } catch (_) {
      detail = response.statusText;
    }
    const error = new Error(detail || "Request failed");
    error.status = response.status;
    throw error;
  }

  if (responseType === "blob") {
    return response.blob();
  }
  return response.json();
}

async function apiFetch(path, { method = "GET", body, headers = {}, apiKey, responseType = "json" } = {}) {
  const options = { method, headers: buildHeaders(apiKey, headers) };
  if (body && !(body instanceof FormData)) {
    options.body = JSON.stringify(body);
    options.headers["Content-Type"] = "application/json";
  } else if (body instanceof FormData) {
    options.body = body;
  }

  const response = await fetch(path, options);
  return handleResponse(response, responseType);
}

export async function createProject(title, description = "", apiKey) {
  return apiFetch(ENDPOINTS.projects, {
    method: "POST",
    apiKey,
    body: { name: title, description },
  });
}

export async function uploadImages(projectId, files, apiKey) {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  const primaryPath = projectId
    ? `${ENDPOINTS.projects}/${projectId}/upload`
    : `${ENDPOINTS.jobs}/upload`;

  try {
    return await apiFetch(primaryPath, {
      method: "POST",
      apiKey,
      body: formData,
    });
  } catch (error) {
    if (projectId && error.status === 404) {
      return apiFetch(`${ENDPOINTS.jobs}/upload`, {
        method: "POST",
        apiKey,
        body: formData,
      });
    }
    throw error;
  }
}

export async function startProcessing(projectId, apiKey) {
  const path = `${ENDPOINTS.projects}/${projectId}/process`;
  return apiFetch(path, { method: "POST", apiKey });
}

export async function pollJobStatus(jobId, apiKey) {
  const path = `${ENDPOINTS.jobs}/status/${jobId}`;
  return apiFetch(path, { method: "GET", apiKey });
}

export async function downloadMesh(jobId, format = "obj", apiKey) {
  const path = `${ENDPOINTS.jobs}/download/${jobId}?format=${format}`;
  const blob = await apiFetch(path, { method: "GET", apiKey, responseType: "blob" });
  return blob;
}

export async function listJobs(apiKey) {
  const path = `${ENDPOINTS.jobs}/jobs`;
  return apiFetch(path, { method: "GET", apiKey });
}

export async function scaleModel(jobId, payload, apiKey) {
  const path = `${ENDPOINTS.jobs}/jobs/${jobId}/scale`;
  return apiFetch(path, { method: "POST", apiKey, body: payload });
}

export { API_URL };
