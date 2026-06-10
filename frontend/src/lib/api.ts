const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type ApiHealth = {
  status: string;
};

export async function getApiHealth() {
  const [liveResponse, readyResponse] = await Promise.all([
    fetch(`${API_BASE_URL}/health/live`),
    fetch(`${API_BASE_URL}/health/ready`),
  ]);

  if (!liveResponse.ok) {
    throw new Error(`Live check failed with ${liveResponse.status}`);
  }

  const live = (await liveResponse.json()) as ApiHealth;

  if (!readyResponse.ok) {
    return {
      live: live.status,
      ready: "not ready",
      detail: `Ready check failed with ${readyResponse.status}`,
    };
  }

  const ready = (await readyResponse.json()) as ApiHealth;

  return {
    live: live.status,
    ready: ready.status,
  };
}

