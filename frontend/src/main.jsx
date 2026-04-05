import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, info) {
    console.error("React Error Boundary caught:", error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 40, fontFamily: "Inter, sans-serif" }}>
          <h1 style={{ color: "#ef4444" }}>Something went wrong</h1>
          <pre style={{ background: "#fef2f2", padding: 16, borderRadius: 8, overflow: "auto", fontSize: 14 }}>
            {this.state.error?.toString()}
          </pre>
        </div>
      );
    }
    return this.props.children;
  }
}

try {
  ReactDOM.createRoot(document.getElementById("root")).render(
    <React.StrictMode>
      <ErrorBoundary>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </ErrorBoundary>
    </React.StrictMode>
  );
} catch (err) {
  document.getElementById("root").innerHTML =
    `<div style="padding:40px;font-family:sans-serif">
      <h1 style="color:#ef4444">Fatal Error</h1>
      <pre style="background:#fef2f2;padding:16px;border-radius:8px">${err}</pre>
    </div>`;
}
