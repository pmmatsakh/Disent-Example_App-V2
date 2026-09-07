import { useEffect, useState } from "react";

// This app proves fullstack persistence: messages you add are POSTed to the
// FastAPI backend, which stores them in SQLite. The list is read back from the
// database — reload the page and everything is still there (nothing is kept in
// browser memory). Same origin, so no CORS.
export default function App() {
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [error, setError] = useState(null);

  async function load() {
    setError(null);
    try {
      const res = await fetch("/api/messages");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setMessages(await res.json());
    } catch (e) {
      setError(e.message);
    }
  }

  async function add(e) {
    e.preventDefault();
    const value = text.trim();
    if (!value) return;
    try {
      const res = await fetch("/api/messages", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text: value }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setText("");
      load();
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
        👋 hello from <code>fastapi_react_sqlite</code>
      </h1>
      <div>React · FastAPI · SQLite · one port, persistent</div>

      <p className="meta">
        Add a message below. It's saved to SQLite on the backend — reload the
        page and it's still here.
      </p>

      <form onSubmit={add} className="row">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="type a message…"
          aria-label="new message"
        />
        <button type="submit">add</button>
      </form>

      {error && <div className="reply">error: {error}</div>}

      <ul className="list">
        {messages.length === 0 && <li className="empty">no messages yet</li>}
        {messages.map((m) => (
          <li key={m.id}>
            <span>{m.text}</span>
            <span className="ts">#{m.id} · {m.created}</span>
          </li>
        ))}
      </ul>
    </main>
  );
}
