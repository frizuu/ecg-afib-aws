const API_URL =
  import.meta.env.VITE_API_URL ||
  "/api";

export { API_URL };

async function handleResponse(
  res
) {
  if (!res.ok) {
    let message = `HTTP Error: ${res.status}`;

    try {
      const payload = await res.json();
      message =
        payload?.detail ||
        payload?.message ||
        message;
    } catch {
      // Keep the generic HTTP message when the API returns no JSON body.
    }

    throw new Error(
      message
    );
  }

  return await res.json();
}

export function normalizePrediction(
  prediction,
  patientName = "Unknown"
) {
  return {
    patient: patientName,
    status:
      prediction?.label ||
      "Unknown",
    bpm:
      prediction?.bpm ??
      "--",
    risk:
      prediction?.probability != null
        ? (
            prediction.probability *
            100
          ).toFixed(1)
        : 0,
    timestamp:
      prediction?.created_at ||
      "-",
  };
}

export async function getLatest() {
  const res = await fetch(
    `${API_URL}/latest`
  );

  return handleResponse(res);
}

export async function getHistory() {
  const res = await fetch(
    `${API_URL}/history?limit=100`
  );

  return handleResponse(res);
}

export async function startStream(
  afib = false
) {
  const res = await fetch(
    `${API_URL}/stream/start?afib=${afib}`,
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

export async function getStreamStatus() {
  const res = await fetch(
    `${API_URL}/stream/status`
  );

  return handleResponse(res);
}

export async function getStreamLatest(
  seconds = 5
) {
  const res = await fetch(
    `${API_URL}/stream/latest?seconds=${seconds}`
  );

  return handleResponse(res);
}

export async function predictStream() {
  const res = await fetch(
    `${API_URL}/predict-stream?seconds=5&threshold=0.5`,
    {
      method: "POST",
    }
  );

  return handleResponse(res);
}
