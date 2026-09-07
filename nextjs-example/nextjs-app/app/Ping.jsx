"use client";

// "use client" makes this a Client Component — it runs in the browser, so it
// can hold state and respond to clicks. It fetches the backend API route and
// shows the JSON it returns, closing the frontend → backend loop.
import { useState } from "react";

export default function Ping() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  async function ping() {
    setLoading(true);
    try {
      const res = await fetch("/api/hello");
      const data = await res.json();
      setResult(JSON.stringify(data, null, 2));
    } catch (err) {
      setResult("error: " + err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <button onClick={ping} disabled={loading}>
        {loading ? "calling…" : "call the backend →"}
      </button>
      {result && <pre className="result">{result}</pre>}
    </div>
  );
}
