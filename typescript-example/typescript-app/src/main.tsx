import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.tsx";
import "./index.css";

// The non-null assertion (!) is a TypeScript feature: we promise the compiler
// that #root exists, so getElementById's `HTMLElement | null` becomes HTMLElement.
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
