import { useEffect, useState } from "react";

// This React app proves the fullstack round-trip: on load it fetches
// /api/hello from the FastAPI backend (same origin, so no CORS) and renders the
// reply. If you see the backend's message and Python version below, the
// frontend and backend are talking end-to-end.
export default function App() {
  const [reply, setReply] = useState(null);
  const [error, setError] = useState(null);

  async function load() {
    setError(null);
    setReply(null);
    try {
      const res = await fetch("/api/hello");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setReply(await res.json());
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <main className="card">
      <h1>
        👋 hello from <code>fastapi_react</code>
      </h1>
      <div>React frontend · FastAPI backend · one port, no CORS</div>

      <p className="meta">
        The box below is fetched live from <code>/api/hello</code> on the
        FastAPI backend that also serves this page.
      </p>

      {reply && (
        <div className="reply">
          backend says: “{reply.message}”
          <br />
          python {reply.python} · served by {reply.served_by}
        </div>
      )}
      {error && <div className="reply">could not reach backend: {error}</div>}
      {!reply && !error && <div className="reply">loading…</div>}

      <button onClick={load}>fetch again</button>
    </main>
  );
}
