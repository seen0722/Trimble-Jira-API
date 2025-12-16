import React, { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import { ArrowLeft, ArrowUpDown, ArrowUp, ArrowDown, Search } from 'lucide-react';
import { Link } from 'react-router-dom';
import './Dashboard.css';

const API_BASE = 'http://127.0.0.1:8000/api';

const PRIORITY_COLORS = {
  'Critical': '#ef4444',
  'Blocker': '#ef4444',
  'High': '#f59e0b',
  'Medium': '#3b82f6',
  'Low': '#6b7280'
};

const PRIORITY_ORDER = {
  'Blocker': 1,
  'Critical': 2,
  'High': 3,
  'Medium': 4,
  'Low': 5,
  'None': 6
};

export default function BugList() {
  const [bugs, setBugs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortConfig, setSortConfig] = useState({ key: 'priority', direction: 'ascending' });
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    axios.get(`${API_BASE}/bugs`)
      .then(res => {
        setBugs(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const filteredBugs = useMemo(() => {
    if (!searchQuery) return bugs;
    const lowerQuery = searchQuery.toLowerCase();
    return bugs.filter(bug => 
      bug.key.toLowerCase().includes(lowerQuery) ||
      bug.summary.toLowerCase().includes(lowerQuery) ||
      (bug.assignee || '').toLowerCase().includes(lowerQuery) ||
      (bug.reporter || '').toLowerCase().includes(lowerQuery) ||
      (bug.labels || '').toLowerCase().includes(lowerQuery)
    );
  }, [bugs, searchQuery]);

  const sortedBugs = useMemo(() => {
    let sortableItems = [...filteredBugs];
    if (sortConfig.key !== null) {
      sortableItems.sort((a, b) => {
        let aValue = a[sortConfig.key];
        let bValue = b[sortConfig.key];

        // Handle nulls
        if (aValue === null) aValue = '';
        if (bValue === null) bValue = '';

        // Custom sort for Priority
        if (sortConfig.key === 'priority') {
           aValue = PRIORITY_ORDER[aValue] || 99;
           bValue = PRIORITY_ORDER[bValue] || 99;
        }

        if (aValue < bValue) {
          return sortConfig.direction === 'ascending' ? -1 : 1;
        }
        if (aValue > bValue) {
          return sortConfig.direction === 'ascending' ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableItems;
  }, [filteredBugs, sortConfig]);

  const requestSort = (key) => {
    let direction = 'ascending';
    if (sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending';
    }
    setSortConfig({ key, direction });
  };

  const SortIcon = ({ columnKey }) => {
    if (sortConfig.key !== columnKey) return <ArrowUpDown size={14} style={{marginLeft: 4, opacity: 0.3}} />;
    if (sortConfig.direction === 'ascending') return <ArrowUp size={14} style={{marginLeft: 4, opacity: 1}} />;
    return <ArrowDown size={14} style={{marginLeft: 4, opacity: 1}} />;
  };

  const Th = ({ label, columnKey, width }) => (
    <th 
      onClick={() => requestSort(columnKey)}
      style={{
        padding: '12px 24px', 
        textAlign: 'left', 
        fontSize: '12px', 
        color: '#6b7280', 
        textTransform: 'uppercase', 
        cursor: 'pointer', 
        userSelect: 'none',
        width: width
      }}
    >
      <div style={{display:'flex', alignItems:'center'}}>
        {label}
        <SortIcon columnKey={columnKey} />
      </div>
    </th>
  );

  if (loading) return (
    <div className="dashboard-container">
      <div className="loading-state">Loading bugs...</div>
    </div>
  );

  return (
    <div className="dashboard-container">
      <header className="dashboard-header" style={{flexWrap: 'wrap', gap: '16px'}}>
        <div className="header-title-group" style={{flex: 1}}>
          <h1>
             <Link to="/" style={{display:'flex', alignItems:'center', textDecoration:'none', color:'inherit', marginRight:'16px'}}>
                <ArrowLeft size={24} />
             </Link>
             Dev Backlog Detail
          </h1>
          <p className="subtitle">Detailed list of {filteredBugs.length} issues {searchQuery && `(filtered from ${bugs.length})`}</p>
        </div>
        
        <div className="search-wrapper" style={{position: 'relative', minWidth: '300px'}}>
            <Search size={18} style={{position:'absolute', left:'12px', top:'50%', transform:'translateY(-50%)', color:'#9ca3af'}} />
            <input 
              type="text" 
              placeholder="Search by Key, Summary, Assignee..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                padding: '10px 10px 10px 40px',
                borderRadius: '8px',
                border: '1px solid #e5e7eb',
                fontSize: '14px',
                width: '100%',
                outline: 'none'
              }}
            />
        </div>
      </header>

      <div className="kpi-card" style={{padding: 0, overflow: 'hidden'}}>
        <table style={{width: '100%', borderCollapse: 'collapse'}}>
          <thead style={{background: '#f9fafb', borderBottom: '1px solid #e5e7eb'}}>
            <tr>
              <Th label="Key" columnKey="key" />
              <Th label="Summary" columnKey="summary" width="40%" />
              <Th label="Priority" columnKey="priority" />
              <Th label="Status" columnKey="status" />
              <Th label="Assignee" columnKey="assignee" />
              <Th label="Reporter" columnKey="reporter" />
              <Th label="Created" columnKey="created" />
              <Th label="Updated" columnKey="updated" />
              <Th label="Labels" columnKey="labels" />
            </tr>
          </thead>
          <tbody>
            {sortedBugs.map((bug, i) => (
              <tr key={bug.key} style={{borderBottom: i < sortedBugs.length - 1 ? '1px solid #f3f4f6' : 'none'}}>
                <td style={{padding: '16px 24px', fontWeight: '500', color: '#2563eb'}}>
                  {bug.link ? (
                    <a href={bug.link} target="_blank" rel="noopener noreferrer" style={{color: '#2563eb', textDecoration: 'none'}}>
                       {bug.key}
                    </a>
                  ) : bug.key}
                </td>
                <td style={{padding: '16px 24px', color: '#374151', textAlign: 'left'}}>{bug.summary}</td>
                <td style={{padding: '16px 24px'}}>
                   <span style={{
                     display: 'inline-flex', alignItems: 'center', gap: '6px',
                     padding: '4px 8px', borderRadius: '12px', fontSize: '12px', fontWeight: '600',
                     background: `${PRIORITY_COLORS[bug.priority] || '#9ca3af'}15`,
                     color: PRIORITY_COLORS[bug.priority] || '#9ca3af'
                   }}>
                     {bug.priority}
                   </span>
                </td>
                <td style={{padding: '16px 24px', fontSize: '14px', color: '#4b5563'}}>
                  {bug.status}
                </td>
                <td style={{padding: '16px 24px', fontSize: '14px', color: '#6b7280'}}>
                  {bug.assignee || 'Unassigned'}
                </td>
                <td style={{padding: '16px 24px', fontSize: '14px', color: '#6b7280'}}>
                  {bug.reporter || '-'}
                </td>
                <td style={{padding: '16px 24px', fontSize: '14px', color: '#6b7280'}}>
                  {bug.created ? new Date(bug.created).toLocaleDateString() : '-'}
                </td>
                <td style={{padding: '16px 24px', fontSize: '14px', color: '#6b7280'}}>
                  {bug.updated ? new Date(bug.updated).toLocaleDateString() : '-'}
                </td>
                <td style={{padding: '16px 24px', fontSize: '14px', color: '#6b7280'}}>
                  {bug.labels ? (
                    <div style={{display:'flex', gap:'4px', flexWrap:'wrap'}}>
                      {bug.labels.split(', ').map((lbl, idx) => (
                        <span key={idx} style={{background:'#e5e7eb', padding:'2px 6px', borderRadius:'4px', fontSize:'11px'}}>
                          {lbl}
                        </span>
                      ))}
                    </div>
                  ) : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
