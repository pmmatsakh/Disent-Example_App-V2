import { useState } from "react";

// Every bit of styling here is a Tailwind utility class (bg-*, text-*, p-*...).
// If the page renders as a styled dark card, Tailwind is working end-to-end:
// the plugin scanned these classes and generated the matching CSS.
export default function App() {
  const [count, setCount] = useState(0);

  return (
    <div className="min-h-screen grid place-items-center bg-[#0f1117] text-[#e6e8ee] font-sans">
      <main className="text-center px-10 py-8 border border-[#262b38] rounded-xl bg-[#161a23] max-w-lg">
        <h1 className="text-2xl font-semibold mb-1">
          👋 hello from{" "}
          <code className="bg-[#0f1117] px-1.5 py-0.5 rounded text-[#7dd3fc]">
            tailwind
          </code>
        </h1>
        <div className="text-[#8a93a6]">Vite + React + Tailwind CSS · frontend only</div>

        <p className="text-[#8a93a6] text-sm mt-4">
          These styles come entirely from Tailwind utility classes — no
          hand-written CSS. The counter below is React state.
        </p>

        <button
          onClick={() => setCount((c) => c + 1)}
          className="mt-2 px-4 py-2 rounded-lg border border-[#2b6cb0] bg-[#1a2433] text-[#7dd3fc] hover:bg-[#22304a] cursor-pointer"
        >
          clicked {count} {count === 1 ? "time" : "times"}
        </button>
      </main>
    </div>
  );
}
