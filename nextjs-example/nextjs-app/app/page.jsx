import Ping from "./Ping";

// This is a React Server Component — Next.js renders it on the server (the
// FRONTEND half). The button it includes calls a backend API route.
export default function Home() {
  return (
    <main className="card">
      <h1>
        👋 hello from <code>nextjs</code>
      </h1>
      <div>Next.js · frontend + backend in one app</div>
      <p className="meta">
        This page is rendered by Next.js on the server (the <strong>frontend</strong>).
        The button below calls an API route at <code>/api/hello</code> (the{" "}
        <strong>backend</strong>) and shows exactly what it returns.
      </p>
      <Ping />
    </main>
  );
}
