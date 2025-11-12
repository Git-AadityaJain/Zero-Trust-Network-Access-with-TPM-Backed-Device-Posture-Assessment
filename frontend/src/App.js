// frontend/src/App.js
import React, { useEffect, useState } from 'react';

function App() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(response => response.json())
      .then(data => setHealth(data.status));
  }, []);

  return (
    <div>
      <h1>ZTNA Admin Dashboard</h1>
      <p>Backend health: {health ? health : "Loading..."}</p>
    </div>
  );
}

export default App;
