import { useState } from "react";

// This is a plain client-side React component. There is no server here — Vite
// serves static files, and all of this runs in the browser. The counter proves
// React state is working: no page reload, no network request.
export default function App() {
  const [count, setCount] = useState(0);

  return (
    <main className="card">
      <h1>
        👋 hello from <code>vite react</code>
      </h1>
      <div>Vite + React · frontend only</div>

      <p className="meta">
        This page is rendered entirely in your browser. There's no backend —
        Vite just serves static files. The counter below is React state, so it
        updates instantly with no request to a server.
      </p>

      <button onClick={() => setCount((c) => c + 1)}>
        clicked {count} {count === 1 ? "time" : "times"}
      </button>

      <p className="meta small">
        Edit <code>src/App.jsx</code> and save — the page updates instantly
        without losing the count. That's Vite's Hot Module Replacement.
      </p>
    </main>
  );
}
