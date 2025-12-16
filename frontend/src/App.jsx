import React from 'react';
import Dashboard from './Dashboard';
import BugList from './BugList';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/bugs" element={<BugList />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
