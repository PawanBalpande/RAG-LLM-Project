import { useState } from "react";

const API_BASE = "http://127.0.0.1:8000/api";

export default function App() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState("");
  const [file, setFile] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [status, setStatus] = useState("");

  const askQuestion = async (event) => {
    event.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, top_k: 4 }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Request failed");
      }

      const data = await response.json();
      setAnswer(data.answer || "");
    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const uploadAndReindex = async (event) => {
    event.preventDefault();
    if (!file) return;
    setProcessing(true);
    setError("");
    setStatus("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch(`${API_BASE}/upload-pdf`, {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Upload failed");
      setStatus(
        `Indexed ${data.filename}: ${data.chunks_indexed} chunks added.`
      );
      setFile(null);
    } catch (err) {
      setError(err.message || "Upload/Reindex failed");
    } finally {
      setProcessing(false);
    }
  };

  const resetVectorStore = async () => {
    setResetting(true);
    setError("");
    setStatus("");
    try {
      const response = await fetch(`${API_BASE}/reset`, { method: "POST" });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Reset failed");
      setAnswer("");
      setStatus(
        `Vector store reset. Collection "${data.collection_name}" now has ${data.collection_count} documents.`
      );
    } catch (err) {
      setError(err.message || "Reset failed");
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="page">
      <div className="card">
        <h1>RAG Assistant</h1>
        <p>Ask questions from your PDF vector store.</p>

        <section>
          <h2>Manage PDFs</h2>
          <form onSubmit={uploadAndReindex}>
            <input
              type="file"
              accept="application/pdf"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
            <button type="submit" disabled={processing || !file}>
              {processing ? "Processing..." : "Upload PDF"}
            </button>
          </form>
          <button type="button" onClick={resetVectorStore} disabled={resetting || processing}>
            {resetting ? "Resetting..." : "Reset Vector Store"}
          </button>
        </section>

        <form onSubmit={askQuestion}>
          <textarea
            placeholder="Ask a question, e.g. What is RAG?"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            rows={4}
          />
          <button type="submit" disabled={loading}>
            {loading ? "Thinking..." : "Ask"}
          </button>
        </form>

        {error && <div className="error">{error}</div>}
        {status && <div className="status">{status}</div>}

        {answer && (
          <section>
            <h2>Answer</h2>
            <div className="answer">{answer}</div>
          </section>
        )}

      </div>
    </div>
  );
}
