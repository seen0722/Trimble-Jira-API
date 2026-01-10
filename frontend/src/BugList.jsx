import React, { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import { ArrowLeft, ArrowUpDown, ArrowUp, ArrowDown, Search, Download } from 'lucide-react';

// ... existing code ...



  // Calculate Status Counts for Summary
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

const STATUS_ORDER = {
  'New': 1,
  'Open': 2,
  'In Progress': 3,
  'Ready for Test': 4,
  'In Test': 5,
  'Resolved': 6,
  'Closed': 7,
  'Done': 8
};

export default function BugList({ isGate = false }) {
  const [bugs, setBugs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortConfig, setSortConfig] = useState({ key: 'priority', direction: 'ascending' });
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const endpoint = isGate ? `${API_BASE}/gate/bugs` : `${API_BASE}/bugs`;
    axios.get(endpoint)
      .then(res => {
        setBugs(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [isGate]);

  const filteredBugs = useMemo(() => {
    if (!searchQuery) return bugs;
    const lowerQuery = searchQuery.toLowerCase();
    return bugs.filter(bug => 
      bug.key.toLowerCase().includes(lowerQuery) ||
      bug.summary.toLowerCase().includes(lowerQuery) ||
      (bug.assignee && bug.assignee.toLowerCase().includes(lowerQuery)) ||
      (bug.reporter && bug.reporter.toLowerCase().includes(lowerQuery)) ||
      (bug.labels && bug.labels.toLowerCase().includes(lowerQuery))
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
        } else if (sortConfig.key === 'status') {
           aValue = STATUS_ORDER[aValue] || 99;
           bValue = STATUS_ORDER[bValue] || 99;
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

  // Calculate Status Counts for Summary
  const statusCounts = useMemo(() => {
    const counts = {};
    bugs.forEach(bug => {
      counts[bug.status] = (counts[bug.status] || 0) + 1;
    });
    return counts;
  }, [bugs]);

  // Export to Markdown
  const handleExport = () => {
    try {
        console.log("Export button clicked");
        const dateStr = new Date().toISOString().split('T')[0];
        let content = `# Gate Backlog Report - ${dateStr}\n\n`;
        content += `**Filter**: Label = \`OS_FCS\` (Includes all statuses)\n`;
        content += `**Total Issues**: ${bugs.length}\n\n`;

        // Summary Dashboard
        content += `## Status Overview\n`;
        content += `| Status | Count |\n`;
        content += `|---|---|\n`;
        
        // Sort logic same as python script: Logical order first, then others
        const orderedStatuses = Object.keys(STATUS_ORDER);
        orderedStatuses.forEach(status => {
        if (statusCounts[status]) {
            content += `| **${status}** | ${statusCounts[status]} |\n`;
        }
        });
        // Any remaining
        Object.keys(statusCounts).forEach(status => {
        if (!STATUS_ORDER[status]) {
            content += `| **${status}** | ${statusCounts[status]} |\n`;
        }
        });

        content += `\n---\n\n## Detailed Issue List\n\n`;
        content += `| Key | Priority | Status | Summary | Assignee | Reporter | Remark |\n`;
        content += `|---|---|---|---|---|---|---|\n`;

        // Sort bugs by Status (primary) and Priority (secondary) for the report
        const bugsToExport = [...bugs].sort((a, b) => {
            const statusA = STATUS_ORDER[a.status] || 99;
            const statusB = STATUS_ORDER[b.status] || 99;
            if (statusA !== statusB) return statusA - statusB;

            const prioA = PRIORITY_ORDER[a.priority] || 99;
            const prioB = PRIORITY_ORDER[b.priority] || 99;
            return prioA - prioB;
        });

        bugsToExport.forEach(bug => {
        // Escape pipes
        const summary = (bug.summary || "").replace(/\|/g, "\\|");
        // Escape newlines in summary to prevent table breakage
        const safeSummary = summary.replace(/\n/g, " ");
        
        const assignee = bug.assignee || "Unassigned";
        const reporter = bug.reporter || "-";
        
        // key link
        const keyLink = bug.link ? `[${bug.key}](${bug.link})` : bug.key;

        // Remark column is empty as requested
        content += `| ${keyLink} | ${bug.priority} | ${bug.status} | ${safeSummary} | ${assignee} | ${reporter} |   |\n`;
        });

        // Create Download
        const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `gate_report_${dateStr}.md`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        setTimeout(() => URL.revokeObjectURL(url), 100);
        
        console.log("Export completed");
    } catch (e) {
        console.error("Export failed:", e);
        alert("Export failed: " + e.message);
    }
  };

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
             <Link to={isGate ? "/gate" : "/"} style={{display:'flex', alignItems:'center', textDecoration:'none', color:'inherit', marginRight:'16px'}}>
                <ArrowLeft size={24} />
             </Link>
             {isGate ? "Gate Backlog Detail" : "Dev Backlog Detail"}
          </h1>
          <p className="subtitle">Detailed list of {filteredBugs.length} issues {searchQuery && `(filtered from ${bugs.length})`}</p>
        </div>
        
        <div className="header-actions" style={{display: 'flex', flexWrap: 'wrap', alignItems: 'center', flexShrink: 0}}>
           <div className="search-wrapper" style={{position: 'relative', width: '300px', marginRight: '16px'}}>
               <Search size={18} style={{position:'absolute', left:'12px', top:'50%', transform:'translateY(-50%)', color:'#9ca3af', zIndex: 1}} />
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
                   outline: 'none',
                   backgroundColor: '#ffffff',
                   color: '#111827',
                   boxSizing: 'border-box'
                 }}
               />
           </div>
           
           <button 
             onClick={handleExport}
             style={{
               display: 'flex', alignItems: 'center', gap: '8px',
               padding: '10px 16px',
               borderRadius: '8px',
               border: 'none',
               background: '#2563eb',
               color: 'white',
               cursor: 'pointer',
               fontWeight: '500',
               fontSize: '14px',
               boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
               whiteSpace: 'nowrap',
               flexShrink: 0
             }}
           >
             <Download size={18} />
             Export Report
           </button>
        </div>
      </header>

      {/* Status Summary Dashboard */}
      <div style={{
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', 
        gap: '12px', 
        marginBottom: '24px',
        padding: '0 4px'
      }}>
        {Object.entries(STATUS_ORDER).map(([status, order]) => {
           const count = statusCounts[status] || 0;
           if (count === 0) return null; // Optional: Hide zero counts or keep them
           
           let color = '#6b7280';
           if (status === 'New') color = '#3b82f6';
           if (status === 'Open') color = '#f59e0b';
           if (status === 'In Progress') color = '#10b981';
           if (status === 'Ready for Test') color = '#8b5cf6';
           
           return (
             <div key={status} style={{
               background: 'white', 
               padding: '12px', 
               borderRadius: '12px', 
               border: '1px solid #e5e7eb',
               boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
               display: 'flex',
               flexDirection: 'column',
               alignItems: 'center'
             }}>
                <span style={{fontSize: '12px', color: '#6b7280', textTransform: 'uppercase', marginBottom: '4px', textAlign: 'center'}}>{status}</span>
                <span style={{fontSize: '20px', fontWeight: 'bold', color: color}}>{count}</span>
             </div>
           )
        })}
      </div>

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
