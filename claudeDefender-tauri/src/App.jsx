import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import iconImage from './assets/icon.gif';
import "./App.css";

function App() {
  const [changes, setChanges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedChange, setSelectedChange] = useState(null);

  useEffect(() => {
    checkForChanges();

    const unlisten = listen("check-now", () => {
      checkForChanges();
    });

    return () => {
      unlisten.then((fn) => fn());
    };
  }, []);

  async function checkForChanges() {
    setLoading(true);
    try {
      const result = await invoke("check_changes");
      setChanges(result);
      if (result.length > 0) {
        setSelectedChange(0);
      }
    } catch (error) {
      console.error("Error checking changes:", error);
    } finally {
      setLoading(false);
    }
  }

  async function handleRevert() {
    if (!confirm("Revert all files to previous version?")) return;

    try {
      await invoke("revert_changes", { changes });
      alert("Changes reverted successfully!");
      await checkForChanges();
    } catch (error) {
      alert(`Error reverting: ${error}`);
    }
  }

  async function handleAccept() {
    try {
      await invoke("accept_changes");
      alert("Changes accepted. Baseline updated.");
      await checkForChanges();
    } catch (error) {
      alert(`Error: ${error}`);
    }
  }

  if (loading) {
    return (
      <div className="loading">
        <h2>Scanning MCP files...</h2>
      </div>
    );
  }

  if (changes.length === 0) {
    return (
      <div className="no-changes">
        <div className="icon">
          <img width="400px" src={iconImage} alt="xx" className="logotitle" />
        </div>
        <h1 style={{ color: "#89db6eff" }}>All Clear!</h1>
        <p>No changes detected in your MCP configuration or server files.</p>
        <button onClick={checkForChanges} className="btn-secondary">
          Check Again
        </button>
      </div>
    );
  }

  const current = changes[selectedChange];

  return (
    <div className="app">
      <div className="header">
        <h1>Changes Detected</h1>
        <p>{changes.length} file(s) changed</p>
      </div>

      <div className="content">
        <div className="sidebar">
          <h3>Changed Files</h3>
          {changes.map((change, idx) => (
            <div
              key={idx}
              className={`file-item ${selectedChange === idx ? "active" : ""}`}
              onClick={() => setSelectedChange(idx)}
            >
              <div className="file-icon">📝</div>
              <div>
                <div className="file-name">{change.name}</div>
                {/* <div className="file-path">{change.path}</div> */}
              </div>
            </div>
          ))}
        </div>

        <div className="main">
          {current && (
            <>
              <div className="file-header">
                <h2>{current.name}</h2>
                <code>{current.path}</code>
              </div>

              <div className="diff-container">
                <h3>Changes:</h3>
                <pre className="diff">{current.diff}</pre>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="actions">
        <button onClick={handleRevert} className="btn-danger">
          Revert All
        </button>
        <button onClick={handleAccept} className="btn-success">
          Accept All
        </button>
        <button onClick={checkForChanges} className="btn-refresh">
          Refresh
        </button>
      </div>
    </div>
  );
}

export default App;
