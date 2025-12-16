import sqlite3
from datetime import datetime
import os

DB_NAME = "dashboard.db"

def view_dashboard():
    if not os.path.exists(DB_NAME):
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print("\n=== Bug Stability & Convergence Dashboard ===")
    print("Generated: ", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)

    # Fetch Snapshots
    cursor.execute("SELECT snapshot_id, timestamp FROM snapshots ORDER BY timestamp ASC")
    snapshots = cursor.fetchall()
    
    if not snapshots:
        print("No data available.")
        return

    print(f"{'Date':<12} | {'Open':<6} | {'New':<6} | {'Fixed':<6} | {'Net':<6} | {'Crit':<6} | {'Status'}")
    print("-" * 65)

    last_open_count = 0

    for snap in snapshots:
        sid, ts_str = snap
        date_str = ts_str.split(' ')[0]
        
        # Metric 1: Open Bug Count (Backlog) on this day
        # "Open" means status NOT in ('Closed', 'Done', 'Resolved') - simplifying
        cursor.execute(f"SELECT COUNT(*) FROM issues WHERE snapshot_id=? AND status NOT IN ('Closed', 'Done', 'Resolved')", (sid,))
        open_count = cursor.fetchone()[0]

        # Metric 5: Critical Bug Count
        cursor.execute(f"SELECT COUNT(*) FROM issues WHERE snapshot_id=? AND status NOT IN ('Closed', 'Done', 'Resolved') AND priority IN ('Critical', 'Blocker', 'High')", (sid,))
        critical_count = cursor.fetchone()[0]

        # Metric 2: New vs Fixed (Weekly Aggregate)
        # "New": Created between [Snapshot Date - 7 days, Snapshot Date]
        # "Fixed": Resolved between [Snapshot Date - 7 days, Snapshot Date]
        
        # Calculate start of the week for this snapshot
        cursor.execute(f"SELECT date(?, '-6 days')", (date_str,))
        week_start = cursor.fetchone()[0]
        
        cursor.execute(f"SELECT COUNT(*) FROM issues WHERE snapshot_id=? AND date(substr(created_date,1,10)) BETWEEN ? AND ?", (sid, week_start, date_str))
        new_count = cursor.fetchone()[0]

        # Note: Fixed count should check resolution date range
        cursor.execute(f"SELECT COUNT(*) FROM issues WHERE snapshot_id=? AND date(substr(resolution_date,1,10)) BETWEEN ? AND ?", (sid, week_start, date_str))
        fixed_count = cursor.fetchone()[0]
        
        net_change = new_count - fixed_count
        
        # Stability Signal
        signal = "🟢"
        if critical_count > 0: signal = "🔴"
        elif net_change > 0: signal = "🟡" # Growing backlog
        
        print(f"{date_str:<12} | {open_count:<6} | {new_count:<6} | {fixed_count:<6} | {net_change:<6} | {critical_count:<6} | {signal}")
        
        last_open_count = open_count

    print("-" * 65)
    print("\n[Interpretations]")
    print("1. Open: Total active bugs.")
    print("2. Net: New - Fixed. Positive means backlog is growing.")
    print("3. Crit: Critical/Blocker/High bugs. Must be 0 for release.")
    print("4. Signal: 🔴=Critical Bugs, 🟡=Growing Backlog, 🟢=Stable/Shrinking")

    conn.close()

if __name__ == "__main__":
    view_dashboard()
