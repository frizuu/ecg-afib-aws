const API_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";

async function handleResponse(
  res
) {
  if (!res.ok) {
    throw new Error(
      `HTTP Error: ${res.status}`
    );
  }

  return await res.json();
}

export async function getLatest() {
  const res = await fetch(
    `${API_URL}/latest`
  );

  return handleResponse(res);
}

export async function getHistory() {
  const res = await fetch(
    `${API_URL}/history`
  );

  return handleResponse(res);
}

export async function startStream() {
  const res = await fetch(
    `${API_URL}/stream/start`,
    {
      method: "POST",
    }
  );

  return handleResponse(res);
}

export async function stopStream() {
  const res = await fetch(
    `${API_URL}/stream/stop`,
    {
      method: "POST",
    }
  );

  return handleResponse(res);
}

export async function predictStream() {
  const res = await fetch(
    `${API_URL}/predict-stream`,
    {
      method: "POST",
    }
  );

  return handleResponse(res);
}