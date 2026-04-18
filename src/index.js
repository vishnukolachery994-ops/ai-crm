import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux';
import { store } from './store';
import InteractionScreen from './InteractionScreen';

/**
 * GLOBAL STYLE RESET
 * This ensures the browser doesn't add default margins or padding
 * that would break the 100vw/100vh split-screen layout.
 */
const injectGlobalStyles = () => {
  const style = document.createElement('style');
  style.innerHTML = `
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    html, body, #root {
      height: 100%;
      width: 100%;
      overflow: hidden; /* Prevents double scrollbars on the main page */
      background-color: #f9fafb;
    }
  `;
  document.head.appendChild(style);
};

injectGlobalStyles();

const root = ReactDOM.createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <Provider store={store}>
      {/* This wrapper forces the application to occupy the entire viewport.
        It acts as a container for the flex-layout inside InteractionScreen.
      */}
      <div style={{ 
        width: '100vw', 
        height: '100vh', 
        display: 'flex', 
        flexDirection: 'column' 
      }}>
        <InteractionScreen />
      </div>
    </Provider>
  </React.StrictMode>
);