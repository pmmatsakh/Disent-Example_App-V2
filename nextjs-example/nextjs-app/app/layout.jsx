import "./globals.css";

// The root layout is required in the App Router. Every page renders inside it.
export const metadata = {
  title: "nextjs — hello world",
  description: "Next.js frontend/backend hello-world example",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
