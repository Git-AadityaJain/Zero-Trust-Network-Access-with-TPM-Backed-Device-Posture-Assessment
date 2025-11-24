import React from 'react';
import { AuthProvider } from './context/AuthContext';
import AppRoutes from './Routes';
import './index.css';

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}

export default App;