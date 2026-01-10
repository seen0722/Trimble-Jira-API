import React from 'react';
import Dashboard from './Dashboard';
import BugList from './BugList';
import GateDashboard from './GateDashboard';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/bugs" element={<BugList />} />
        <Route path="/gate" element={<GateDashboard />} />
        <Route path="/gate-bugs" element={<BugList isGate={true} />} />
      </Routes>
    </Router>
  );
}

export default App;
