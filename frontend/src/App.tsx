import { useState, useEffect } from "react";
import axios from "axios";
import config from "./config";
import "./App.css";

// Create axios instance
const apiClient = axios.create({
  baseURL: config.apiUrl,
  headers: {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
  },
});

function App() {
  const [healthStatus, setHealthStatus] = useState<string>("checking...");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check health on component mount
    apiClient
      .get("/health")
      .then((response) => {
        setHealthStatus(response.data.status || "unknown");
        setError(null);
      })
      .catch((err) => {
        setError(err.message || "Failed to connect to backend");
        setHealthStatus("error");
      });
  }, []);

  return (
    <div className="app">
      <div className="container">
        <h1>GCP RAG Chatbot</h1>
        <p className="subtitle">Step 1: Health Check</p>

        <div className="health-check">
          <h2>Backend Health Status</h2>
          <div className={`status ${healthStatus}`}>{healthStatus}</div>
          {error && <div className="error">Error: {error}</div>}
          <p className="info">API URL: {config.apiUrl}</p>
        </div>
      </div>
    </div>
  );
}

export default App;
