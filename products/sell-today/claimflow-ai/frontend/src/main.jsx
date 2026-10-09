import './i18n';
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';
import './sw-register.js';
import './utils/lumi-motion.js';
import './styles/rtl.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
