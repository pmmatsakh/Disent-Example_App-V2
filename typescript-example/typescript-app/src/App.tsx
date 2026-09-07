import { useState } from "react";

// A tiny typed helper — proves TypeScript is really compiling, not just being
// stripped: `count` is typed `number`, and this function only accepts a number.
function label(count: number): string {
  return `clicked ${count} ${count === 1 ? "time" : "times"}`;
}

export default function App() {
  const [count, setCount] = useState<number>(0);

  return (
    <main className="card">
      <h1>
        👋 hello from <code>typescript</code>
      </h1>
      <div>Vite + React + TypeScript · frontend only</div>

      <p className="meta">
        Written in <code>.tsx</code> with full type-checking. Vite compiles the
        TypeScript to JavaScript in the browser; the counter is typed React state.
      </p>

      <button onClick={() => setCount((c) => c + 1)}>{label(count)}</button>

      <p className="meta small">
        Run <code>npm run build</code> to type-check with <code>tsc</code> and
        produce a production bundle.
      </p>
    </main>
  );
}
