import React, { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area
} from 'recharts';
import { 
  Activity, Bug, CheckCircle2, RotateCw, AlertTriangle, TrendingDown, Layers, Calendar, ArrowLeft
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import './Dashboard.css';

const API_BASE = 'http://127.0.0.1:8000/api';

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

export default function GateDashboard() {
  const [history, setHistory] = useState([]);
  const [breakdown, setBreakdown] = useState({ priority: [], status: [] });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [histRes, breakRes] = await Promise.all([
        axios.get(`${API_BASE}/gate/history`),
        axios.get(`${API_BASE}/gate/breakdown`)
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

  // Hybrid Mode Logic:
  // KPIs use 'history' (latest data).
  // Charts use 'chartData' (strict weekly cadence, removing the partial latest day if it causes overlap).
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
        
        // If the latest point is less than 7 days from the previous one, 
        // it's a "Forced Latest" update. We hide it from the trend charts to strictly show weekly intervals.
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
      <span style={{marginLeft: 10,  fontFamily: 'Inter'}}>Loading gate metrics...</span>
    </div>
  );

  const currentStats = history.length > 0 ? history[history.length - 1] : {};
  const prevStats = history.length > 1 ? history[history.length - 2] : {};
  
  // Calculations for trend
  // Calculations for trend
  const openDiff = (currentStats.open || 0) - (prevStats.open || 0);



  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div className="header-title-group">
          <h1>
             <Link to="/" style={{display:'flex', alignItems:'center', textDecoration:'none', color:'inherit', marginRight:'16px'}}>
                <ArrowLeft size={24} />
             </Link>
             <div style={{display:'flex', alignItems:'center', gap: '8px'}}>
                <Activity color="#ec4899" /> 
                Mass Production Gate
             </div>
          </h1>
          <p className="subtitle">Tracking issues for OS_FCS Gate</p>
        </div>
        <button className="refresh-btn" onClick={handleRefresh} disabled={refreshing}>
          <RotateCw className={`refresh-icon ${refreshing ? 'spinning' : ''}`} size={16} />
          {refreshing ? 'Syncing...' : 'Refresh Data'}
        </button>
      </header>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card" style={{cursor:'pointer'}} onClick={() => navigate('/gate-bugs')}>
          <div className="kpi-header">
            <span className="kpi-title" style={{textDecoration:'underline'}}>Gate Backlog Size</span>
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
            <span className="kpi-title">Critical Gate Issues</span>
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
            <h3>Gate Issue Trend</h3>
            <p className="chart-desc">Historical tracking of OS_FCS bug count.</p>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorOpenGate" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ec4899" stopOpacity={0.1}/>
                  <stop offset="95%" stopColor="#ec4899" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
              <XAxis dataKey="date" tick={{fontSize: 12, fill: '#6b7280'}} axisLine={false} tickLine={false} />
              <YAxis tick={{fontSize: 12, fill: '#6b7280'}} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Legend iconType="circle" />
              <Area type="monotone" dataKey="open" stroke="#ec4899" fillOpacity={1} fill="url(#colorOpenGate)" name="Open Bugs" strokeWidth={2} />
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
              <Line type="monotone" dataKey="critical" stroke="#ef4444" name="Critical" strokeWidth={2} dot={{stroke: '#ef4444', strokeWidth: 2, r: 4}} />
              <Line type="monotone" dataKey="high" stroke="#f59e0b" name="High" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="medium" stroke="#3b82f6" name="Medium" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="low" stroke="#6b7280" name="Low" strokeWidth={2} dot={false} />
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
