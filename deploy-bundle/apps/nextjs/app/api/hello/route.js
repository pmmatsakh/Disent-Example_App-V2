// A Route Handler — this is the BACKEND half. It runs only on the server and
// responds to requests at /api/hello. This is what makes the row "frontend/
// backend": one Next.js app serves both the rendered page and this API.
export function GET() {
  return Response.json({
    app: "nextjs",
    status: "ok",
    message: "hello from the Next.js backend (API route)",
    time: new Date().toISOString(),
  });
}
