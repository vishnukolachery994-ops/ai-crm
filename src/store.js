import { configureStore, createSlice } from '@reduxjs/toolkit';

/**
 * interactionSlice
 * Manages the state of HCP logs, chat history, and AI-generated content.
 */
const interactionSlice = createSlice({
  name: 'interactions',
  initialState: { 
    logs: [],             // History of all saved interactions (synced from DB)
    chatHistory: [],      // Messages for the Conversational Interface
    suggestions: [],      // AI-generated follow-up tasks
    isProcessing: false   // Loading state for LangGraph calls
  },
  reducers: {
    /**
     * SYNC REDUCER: Updates the entire logs list.
     * Use this when the backend returns 'all_logs' from main.py.
     */
    setAllLogs: (state, action) => {
      // action.payload is the array of logs from PostgreSQL
      state.logs = action.payload;
    },

    /**
     * Adds a single log to the top of the history.
     */
    addLog: (state, action) => {
      if (action.payload) {
        state.logs.unshift(action.payload);
      } else {
        console.error("Invalid log payload:", action.payload);
      }
    },

    /**
     * Updates the chat history (messages between User and AI).
     */
    addMessage: (state, action) => {
      // action.payload: { role: 'user' | 'ai', content: string }
      state.chatHistory.push(action.payload);
    },

    /**
     * Stores AI-generated follow-up tasks.
     */
    setSuggestions: (state, action) => {
      state.suggestions = action.payload;
    },

    /**
     * Toggles the loading spinner.
     */
    setProcessing: (state, action) => {
      state.isProcessing = action.payload;
    },

    /**
     * Resets session-specific data.
     */
    clearSession: (state) => {
      state.chatHistory = [];
      state.suggestions = [];
    }
  },
});

// Export all actions, including the new setAllLogs
export const { 
  setAllLogs, 
  addLog, 
  addMessage, 
  setSuggestions, 
  setProcessing, 
  clearSession 
} = interactionSlice.actions;

// Configure and export the Redux store
export const store = configureStore({ 
  reducer: { 
    interactions: interactionSlice.reducer 
  } 
});

export default store;