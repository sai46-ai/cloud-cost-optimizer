import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import * as THREE from 'three'

import { ErrorBoundary } from './components/ErrorBoundary.tsx'

// Suppress THREE.Clock deprecation warnings from React Three Fiber/Drei internal logic globally
const originalWarn = console.warn;
console.warn = (...args: any[]) => {
  if (args[0] && typeof args[0] === 'string' && args[0].includes('THREE.Clock: This module has been deprecated')) {
    return;
  }
  originalWarn.apply(console, args);
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
)
