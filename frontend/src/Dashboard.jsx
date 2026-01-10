import React, { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area
} from 'recharts';
import { 
  Activity, Bug, CheckCircle2, RotateCw, AlertTriangle, TrendingDown, Layers, Calendar, FileText
} from 'lucide-react';
import { Link } from 'react-router-dom';
import './Dashboard.css';

const API_BASE = '/api';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
const STATUS_COLOR_MAP = {
  'New': '#3b82f6',       // Blue
  'Open': '#f59e0b',      // Orange
  'In Progress': '#10b981', // Green
  'Ready for Test': '#8b5cf6', // Purple
  'In Test': '#6366f1',   // Indigo
  'Closed': '#9ca3af'     // Gray
};

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="custom-tooltip">
        <p className="label">{label}</p>
        {payload.map((entry, index) => (
          <p key={index} style={{ color: entry.color }}>
            {entry.name}: <strong>{entry.value}</strong>
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function Dashboard() {
  const [history, setHistory] = useState([]);
  const [breakdown, setBreakdown] = useState({ priority: [], status: [] });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [histRes, breakRes] = await Promise.all([
        axios.get(`${API_BASE}/history`),
        axios.get(`${API_BASE}/breakdown`)
      ]);
      setHistory(histRes.data);
      setBreakdown(breakRes.data);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await axios.post(`${API_BASE}/snapshot`);
      await fetchData();
    } catch (err) {
      console.error(err);
      alert('Failed to refresh data');
    }
    setRefreshing(false);
  };

  // Progress modal state
  const [reportProgress, setReportProgress] = useState({ current: 0, total: 0, status: '', issueKey: null });
  const [reportContent, setReportContent] = useState(null);
  const [reportFilename, setReportFilename] = useState(null);

  const handleGenerateReport = () => {
    setGeneratingReport(true);
    setReportProgress({ current: 0, total: 0, status: 'Connecting...', issueKey: null });
    setReportContent(null);
    setReportFilename(null);

    const eventSource = new EventSource(`${API_BASE}/weekly-report/stream`);

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'progress') {
        setReportProgress({
          current: data.current,
          total: data.total,
          status: data.status,
          issueKey: data.issue_key
        });
      } else if (data.type === 'complete') {
        eventSource.close();
        setReportContent(data.content);
        setReportFilename(data.filename);
        setReportProgress({ current: data.issue_count || 0, total: data.issue_count || 0, status: 'Complete! Downloading...', issueKey: null });
        
        // Download from backend endpoint (proper Content-Disposition)
        window.location.href = `${API_BASE}/weekly-report/download`;
        
        setTimeout(() => setGeneratingReport(false), 1500);
      } else if (data.type === 'error') {
        eventSource.close();
        alert(`Error: ${data.message}`);
        setGeneratingReport(false);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      alert('Connection lost. Please try again.');
      setGeneratingReport(false);
    };
  };



  const currentStats = history.length > 0 ? history[history.length - 1] : {};
  const prevStats = history.length > 1 ? history[history.length - 2] : {};
  
  // Calculations for trend
  // Calculations for trend
  const openDiff = (currentStats.open || 0) - (prevStats.open || 0);

  // Hybrid Mode Logic for Charts (Strict Weekly)
  const chartData = useMemo(() => {
    if (!Array.isArray(history) || history.length < 2) return history;
    
    try {
        const data = [...history];
        const last = data[data.length - 1];
        const prev = data[data.length - 2];
        
        if (!last || !prev || !last.date || !prev.date) return data;

        const d1 = new Date(prev.date);
        const d2 = new Date(last.date);
        
        // Calculate difference in days
        const diffTime = Math.abs(d2 - d1);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)); 
        
        // If the latest point is less than 7 days from the previous one, use strict weekly
        if (diffDays < 7) {
            return data.slice(0, -1);
        }
        return data;
    } catch (e) {
        console.error("Error filtering chart data:", e);
        return history;
    }
  }, [history]);

  if (loading) return (
    <div className="loading-screen" style={{height:'100vh', display:'flex', alignItems:'center', justifyContent:'center'}}>
      <RotateCw className="spinning" size={32} />
      <span style={{marginLeft: 10,  fontFamily: 'Inter'}}>Loading metrics...</span>
    </div>
  );

  // Progress Modal Component
  const ProgressModal = () => {
    if (!generatingReport) return null;
    const percentage = reportProgress.total > 0 
      ? Math.round((reportProgress.current / reportProgress.total) * 100) 
      : 0;
    
    return (
      <div style={{
        position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
        background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center',
        zIndex: 1000
      }}>
        <div style={{
          background: 'white', borderRadius: 16, padding: 32, width: 420,
          boxShadow: '0 20px 40px rgba(0,0,0,0.2)'
        }}>
          <div style={{display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20}}>
            <FileText size={24} color="#2563eb" />
            <h3 style={{margin: 0, fontSize: 18}}>Generating Weekly Report</h3>
          </div>
          
          <p style={{color: '#6b7280', fontSize: 14, margin: '0 0 16px'}}>
            {reportProgress.status}
          </p>
          
          {reportProgress.issueKey && (
            <p style={{color: '#2563eb', fontSize: 13, fontFamily: 'monospace', margin: '0 0 16px'}}>
              📋 {reportProgress.issueKey}
            </p>
          )}
          
          <div style={{
            background: '#e5e7eb', borderRadius: 8, height: 12, overflow: 'hidden', marginBottom: 12
          }}>
            <div style={{
              background: 'linear-gradient(90deg, #2563eb, #3b82f6)',
              height: '100%', width: `${percentage}%`,
              transition: 'width 0.3s ease',
              borderRadius: 8
            }} />
          </div>
          
          <div style={{display: 'flex', justifyContent: 'space-between', fontSize: 13, color: '#6b7280'}}>
            <span>{reportProgress.current} / {reportProgress.total} issues</span>
            <span>{percentage}%</span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="dashboard-container">
      <ProgressModal />
      <header className="dashboard-header">
        <div className="header-title-group">
          <h1><Activity color="#2563eb" /> Bug Stability Control</h1>
          <p className="subtitle">Real-time Quality Assurance Metrics</p>
        </div>
        <div style={{display:'flex', gap:'12px'}}>
            <Link to="/gate" style={{
              display:'flex', alignItems:'center', gap:'8px', padding:'8px 16px', 
              background:'#fce7f3', color:'#db2777', textDecoration:'none', borderRadius:'8px', fontSize:'14px', fontWeight:'500'
            }}>
                <Activity size={16} /> 
                Gate View
            </Link>
            <button 
              className="refresh-btn" 
              onClick={handleGenerateReport} 
              disabled={generatingReport}
              style={{background: '#dbeafe', color: '#2563eb'}}
            >
              <FileText className={generatingReport ? 'spinning' : ''} size={16} />
              {generatingReport ? 'Generating...' : 'Weekly Report'}
            </button>
            <button className="refresh-btn" onClick={handleRefresh} disabled={refreshing}>
              <RotateCw className={`refresh-icon ${refreshing ? 'spinning' : ''}`} size={16} />
              {refreshing ? 'Syncing...' : 'Refresh Data'}
            </button>
        </div>
      </header>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card" style={{cursor:'pointer'}} onClick={() => window.location.href='/bugs'}>
          <div className="kpi-header">
            <span className="kpi-title" style={{textDecoration:'underline'}}>Backlog Size</span>
            <div className="kpi-icon-wrapper"><Layers size={20} /></div>
          </div>
          <div className="kpi-value">{currentStats.open || 0}</div>
          <div className="kpi-trend">
             {openDiff > 0 ? <TrendingDown size={14} className="trend-bad" /> : <CheckCircle2 size={14} className="trend-good" />}
             <span className={openDiff > 0 ? "trend-bad" : "trend-good"}>
               {openDiff > 0 ? `+${openDiff}` : openDiff} this week
             </span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Critical Issues</span>
            <div className="kpi-icon-wrapper" style={{color:'#ef4444', background:'#fee2e2'}}><AlertTriangle size={20} /></div>
          </div>
          <div className="kpi-value" style={{color: currentStats.critical > 0 ? '#ef4444' : '#10b981'}}>
            {currentStats.critical || 0}
          </div>
          <div className="kpi-trend">
             <span className="trend-neutral">Target: 0</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Weekly Velocity</span>
            <div className="kpi-icon-wrapper"><Calendar size={20} /></div>
          </div>
          <div className="kpi-value">
            <span style={{color: '#f59e0b', fontSize:'1.8rem'}}>+{currentStats.new_bugs || 0}</span>
            <span style={{color: '#9ca3af', margin:'0 8px'}}>/</span>
            <span style={{color: '#10b981', fontSize:'1.8rem'}}>-{currentStats.fixed_bugs || 0}</span>
          </div>
          <div className="kpi-trend">
             <span className="trend-neutral">New / Fixed</span>
          </div>
        </div>
      </div>

      <div className="charts-grid">
        {/* Chart 1: Open Trends */}
        <div className="chart-card wide">
          <div className="chart-header">
            <h3>Open Issue Trend</h3>
            <p className="chart-desc">Historical tracking of total open bug count over time.</p>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorOpen" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.1}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
              <XAxis dataKey="date" tick={{fontSize: 12, fill: '#6b7280'}} axisLine={false} tickLine={false} />
              <YAxis tick={{fontSize: 12, fill: '#6b7280'}} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Legend iconType="circle" />
              <Area type="monotone" dataKey="open" stroke="#2563eb" fillOpacity={1} fill="url(#colorOpen)" name="Total Open Bugs" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Chart 2: Velocity */}
        <div className="chart-card">
           <div className="chart-header">
            <h3>Velocity (New vs Fixed)</h3>
            <p className="chart-desc">Inflow vs outflow of bugs per week.</p>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
              <XAxis dataKey="date" tick={{fontSize: 12, fill: '#6b7280'}} axisLine={false} tickLine={false} />
              <YAxis tick={{fontSize: 12, fill: '#6b7280'}} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Legend iconType="circle" />
              <Bar dataKey="new_bugs" fill="#f59e0b" name="New" radius={[4, 4, 0, 0]} />
              <Bar dataKey="fixed_bugs" fill="#10b981" name="Fixed" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Chart 3: Critical vs High */}
        <div className="chart-card">
           <div className="chart-header">
            <h3>Priority Breakdown Trend</h3>
            <p className="chart-desc">Tracking high-risk items separately.</p>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
              <XAxis dataKey="date" tick={{fontSize: 12, fill: '#6b7280'}} axisLine={false} tickLine={false} />
              <YAxis tick={{fontSize: 12, fill: '#6b7280'}} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Legend iconType="circle" />
              <Line type="monotone" dataKey="high" stroke="#3b82f6" name="High" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="critical" stroke="#ef4444" name="Critical" strokeWidth={2} dot={{stroke: '#ef4444', strokeWidth: 2, r: 4}} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Chart 4: Pie Charts */}
        <div className="chart-card wide">
           <div className="chart-header">
            <h3>Current State Breakdown</h3>
            <p className="chart-desc">Distribution by Priority and Workflow Status.</p>
          </div>
          <div className="pie-wrapper">
             <div className="pie-section">
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie data={breakdown.priority} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5}>
                        {breakdown.priority.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                    <Legend verticalAlign="bottom" height={36} iconType="circle" />
                  </PieChart>
                </ResponsiveContainer>
                <div className="pie-label">By Priority</div>
             </div>
             
             <div className="pie-section">
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie data={breakdown.status} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5}>
                         {breakdown.status.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={STATUS_COLOR_MAP[entry.name] || '#9ca3af'} />
                        ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                    <Legend verticalAlign="bottom" height={36} iconType="circle" />
                  </PieChart>
                </ResponsiveContainer>
                <div className="pie-label">By Status</div>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}
