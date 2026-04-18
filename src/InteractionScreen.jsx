import React, { useState, useEffect, useRef } from "react";
import { useDispatch, useSelector } from "react-redux";
import { setAllLogs, addMessage, setProcessing, setSuggestions } from "./store";

const InteractionScreen = () => {
  const dispatch = useDispatch();
  const { logs, chatHistory, isProcessing, suggestions } = useSelector(
    (state) => state.interactions
  );

  const [chatInput, setChatInput] = useState("");
  const chatEndRef = useRef(null);

  // 1. SESSION ID: Persistent per browser tab/refresh
  // This ensures the backend knows these messages belong to the same "conversation"
  const [sessionId] = useState(`sess-${Date.now()}`);

  // 2. INITIAL LOAD: Sync Sidebar with PostgreSQL on Mount
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const res = await fetch("http://localhost:8000/get-logs");
        if (res.ok) {
          const data = await res.json();
          dispatch(setAllLogs(data));
        }
      } catch (e) {
        console.error("Failed to load initial history:", e);
      }
    };
    loadInitialData();
  }, [dispatch]);

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  const handleAISubmit = async () => {
    if (!chatInput.trim() || isProcessing) return;

    const userMsg = chatInput;
    setChatInput("");
    dispatch(setProcessing(true));
    
    // Optimistically add user message to UI
    dispatch(addMessage({ role: "user", content: userMsg }));

    try {
      const res = await fetch("http://localhost:8000/log-interaction", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
            user_input: userMsg,
            session_id: sessionId // <--- CRITICAL: Matches backend InteractionRequest model
        }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Server Error");
      }

      const data = await res.json();

      // 1. Update Chat History with AI Reply
      dispatch(addMessage({ role: "ai", content: data.reply }));

      // 2. Update the Structured Logs List (The Left Panel)
      if (data.all_logs) {
        dispatch(setAllLogs(data.all_logs));
      }

      // 3. Extract action items for the UI suggestions panel
      const extracted = data.reply
        .split("\n")
        .filter((l) => l.trim().startsWith("- "))
        .map((l) => l.replace(/^-\s*/, ""));
      dispatch(setSuggestions(extracted));
      
    } catch (e) {
      console.error("Connection Error:", e);
      dispatch(addMessage({ 
        role: "ai", 
        content: `Error: ${e.message}. Verify FastAPI is running on port 8000.` 
      }));
    } finally {
      dispatch(setProcessing(false));
    }
  };

  // --- DATA MAPPING FOR UI ---
  const latestLog = logs[0] || {};
  const docName = latestLog.doctor_name || "";
  const topicName = latestLog.topic || "";
  const summaryText = latestLog.raw_summary || "";
  const sentimentVal = latestLog.sentiment || "Neutral";
  const dateVal = latestLog.created_at 
    ? new Date(latestLog.created_at).toLocaleString() 
    : "No records found";

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', overflow: 'hidden', backgroundColor: '#f9fafb' }}>
      
      {/* NAVBAR */}
      <nav style={{ height: '64px', backgroundColor: 'white', borderBottom: '1px solid #e5e7eb', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 32px', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '32px', height: '32px', backgroundColor: '#2563eb', borderRadius: '6px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold' }}>H</div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#111827' }}>
            HCP CRM <span style={{ color: '#2563eb' }}>AI</span>
          </h1>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ width: '8px', height: '8px', backgroundColor: isProcessing ? '#f59e0b' : '#10b981', borderRadius: '50%' }}></span>
          <span style={{ fontSize: '11px', color: isProcessing ? '#b45309' : '#047857', fontWeight: '700', textTransform: 'uppercase' }}>
            {isProcessing ? "AI is Thinking..." : "Assistant Ready"}
          </span>
        </div>
      </nav>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        
        {/* LEFT PANEL: DATA EXTRACTION PREVIEW */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '40px', backgroundColor: '#f3f4f6' }}>
          <div style={{ maxWidth: '800px', margin: '0 auto', backgroundColor: 'white', borderRadius: '16px', border: '1px solid #e5e7eb', padding: '32px', boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <h2 style={{ fontSize: '1.125rem', fontWeight: 'bold', marginBottom: '24px', color: '#1f2937' }}>Latest Extraction</h2>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <label style={{ fontSize: '11px', fontWeight: 'bold', color: '#9ca3af', textTransform: 'uppercase' }}>HCP Name</label>
                <input readOnly value={docName} style={{ padding: '12px', backgroundColor: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: '14px' }} placeholder="Waiting for interaction..." />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <label style={{ fontSize: '11px', fontWeight: 'bold', color: '#9ca3af', textTransform: 'uppercase' }}>Logged At</label>
                <input readOnly value={dateVal} style={{ padding: '12px', backgroundColor: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: '14px' }} />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <label style={{ fontSize: '11px', fontWeight: 'bold', color: '#9ca3af', textTransform: 'uppercase' }}>Therapeutic Area</label>
                <input readOnly value={topicName} style={{ padding: '12px', backgroundColor: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: '14px' }} placeholder="Identifying..." />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <label style={{ fontSize: '11px', fontWeight: 'bold', color: '#9ca3af', textTransform: 'uppercase' }}>HCP Sentiment</label>
                <div style={{ 
                  padding: '12px', 
                  backgroundColor: sentimentVal.toLowerCase().includes('pos') ? '#ecfdf5' : '#eff6ff', 
                  border: '1px solid #e5e7eb', 
                  borderRadius: '8px', 
                  fontSize: '14px', 
                  color: sentimentVal.toLowerCase().includes('pos') ? '#059669' : '#2563eb', 
                  fontWeight: 'bold' 
                }}>
                  {sentimentVal}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '24px' }}>
              <label style={{ fontSize: '11px', fontWeight: 'bold', color: '#9ca3af', textTransform: 'uppercase' }}>Executive Summary</label>
              <textarea readOnly value={summaryText} style={{ padding: '16px', backgroundColor: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '8px', minHeight: '160px', fontSize: '14px', lineHeight: '1.6', resize: 'none' }} placeholder="AI will summarize your conversation here..." />
            </div>

            {/* AI ACTION ITEMS */}
            <div style={{ borderTop: '1px solid #f3f4f6', paddingTop: '24px' }}>
              <h3 style={{ fontSize: '11px', fontWeight: 'bold', color: '#2563eb', textTransform: 'uppercase', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                Next Best Actions
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {suggestions.length > 0 ? suggestions.map((s, i) => (
                  <div key={i} style={{ padding: '10px 14px', backgroundColor: '#eff6ff', border: '1px solid #dbeafe', borderRadius: '8px', fontSize: '13px', color: '#1e40af' }}>
                    • {s}
                  </div>
                )) : <p style={{ fontSize: '12px', color: '#9ca3af', fontStyle: 'italic' }}>Awaiting interaction to generate steps.</p>}
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT PANEL: CONVERSATIONAL LOGGING */}
        <div style={{ width: '420px', backgroundColor: 'white', borderLeft: '1px solid #e5e7eb', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
          <div style={{ padding: '20px', borderBottom: '1px solid #e5e7eb', backgroundColor: '#f9fafb' }}>
            <div style={{ fontSize: '14px', fontWeight: 'bold' }}>Field Assistant</div>
            <div style={{ fontSize: '10px', color: '#9ca3af' }}>Conversations are synced to CRM in real-time</div>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {chatHistory.map((msg, i) => (
              <div key={i} style={{ 
                alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start', 
                maxWidth: '85%', 
                padding: '10px 14px', 
                borderRadius: '12px', 
                fontSize: '14px', 
                backgroundColor: msg.role === 'user' ? '#2563eb' : '#f3f4f6', 
                color: msg.role === 'user' ? 'white' : '#1f2937',
                boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
              }}>
                {msg.content}
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>

          <div style={{ padding: '20px', borderTop: '1px solid #e5e7eb' }}>
            <div style={{ display: 'flex', gap: '8px', backgroundColor: '#f3f4f6', padding: '8px', borderRadius: '12px' }}>
              <input 
                style={{ flex: 1, backgroundColor: 'transparent', border: 'none', outline: 'none', padding: '8px', fontSize: '14px' }} 
                placeholder="Talk to assistant..." 
                value={chatInput} 
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAISubmit()}
              />
              <button 
                onClick={handleAISubmit} 
                disabled={isProcessing} 
                style={{ 
                  backgroundColor: isProcessing ? '#9ca3af' : '#2563eb', 
                  color: 'white', 
                  padding: '8px 16px', 
                  borderRadius: '8px', 
                  border: 'none', 
                  cursor: isProcessing ? 'not-allowed' : 'pointer',
                  fontWeight: '600',
                  minWidth: '70px'
                }}
              >
                {isProcessing ? "..." : "Send"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InteractionScreen;