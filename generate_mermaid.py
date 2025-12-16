import sqlite3
import os
from datetime import datetime

DB_NAME = "dashboard.db"
OUTPUT_FILE = "dashboard_charts.md"

def generate_charts():
    if not os.path.exists(DB_NAME):
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Fetch Snapshots sorted by date
    cursor.execute("SELECT snapshot_id, timestamp FROM snapshots ORDER BY timestamp ASC")
    snapshots = cursor.fetchall()

    if not snapshots:
        print("No data available.")
        return

    def to_mermaid_list(data):
        if not data: return "[]"
        # If strings, wrap in double quotes. If numbers, straight conversion.
        if isinstance(data[0], str):
            return "[" + ", ".join([f'"{d}"' for d in data]) + "]"
        return str(data)

    dates = []
    open_counts = []
    new_counts = []
    fixed_counts = []
    critical_only_counts = []
    high_only_counts = []

    for snap in snapshots:
        sid, ts_str = snap
        # Format date as 'Week XX' or 'YYYY-MM-DD'
        # Let's use ISO Week number for clarity if needed, or just the date
        date_obj = datetime.strptime(ts_str.split(' ')[0], "%Y-%m-%d")
        week_num = date_obj.isocalendar()[1]
        date_label = f"W{week_num}" # e.g., W42
        # Adding year to handle cross-year: W42, W43... W1, W2
        if len(dates) == 0 or dates[-1].split('-')[0] != str(week_num):
             # Simplified: Just MM-DD is usually safer for readers than Abstract Week Numbers
             date_label = date_obj.strftime("%m-%d")

        dates.append(date_label)

        # 1. Open Bugs
        cursor.execute(f"SELECT COUNT(*) FROM issues WHERE snapshot_id=? AND status NOT IN ('Closed', 'Done', 'Resolved') AND type='Bug'", (sid,))
        open_counts.append(cursor.fetchone()[0])
        
        # 5. Critical Only
        cursor.execute(f"SELECT COUNT(*) FROM issues WHERE snapshot_id=? AND status NOT IN ('Closed', 'Done', 'Resolved') AND priority IN ('Critical', 'Blocker') AND type='Bug'", (sid,))
        critical_only_counts.append(cursor.fetchone()[0])
        
        # 6. High Only
        cursor.execute(f"SELECT COUNT(*) FROM issues WHERE snapshot_id=? AND status NOT IN ('Closed', 'Done', 'Resolved') AND priority = 'High' AND type='Bug'", (sid,))
        high_only_counts.append(cursor.fetchone()[0])

        # 2. New vs Fixed (Weekly)
        date_full = ts_str.split(' ')[0]
        cursor.execute(f"SELECT date(?, '-6 days')", (date_full,))
        week_start = cursor.fetchone()[0]

        cursor.execute(f"SELECT COUNT(*) FROM issues WHERE snapshot_id=? AND date(substr(created_date,1,10)) BETWEEN ? AND ? AND type='Bug'", (sid, week_start, date_full))
        new_counts.append(cursor.fetchone()[0])

        cursor.execute(f"SELECT COUNT(*) FROM issues WHERE snapshot_id=? AND date(substr(resolution_date,1,10)) BETWEEN ? AND ? AND type='Bug'", (sid, week_start, date_full))
        fixed_counts.append(cursor.fetchone()[0])


    # Generate Markdown content
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(f"# Bug Stability Charts ({dates[-1]})\n\n")

        # Chart 1: Open Bug Trend
        f.write("## 1. Open Bug Trend (Backlog)\n")
        f.write("Shows the total number of unresolved bugs over time. Lower is better.\n\n")
        f.write("```mermaid\n")
        f.write("xychart-beta\n")
        f.write(f'    title "Open Bug Count ({dates[0]} to {dates[-1]})"\n')
        f.write(f'    x-axis {to_mermaid_list(dates)}\n')
        f.write(f'    y-axis "Count" {min(open_counts)-5} --> {max(open_counts)+5}\n')
        f.write(f'    line {to_mermaid_list(open_counts)}\n')
        f.write("```\n\n")

        # Chart 2: New vs Fixed
        f.write("## 2. New vs Fixed (Velocity)\n")
        f.write("Compares incoming bugs (New) vs resolved bugs (Fixed). Fixed > New is ideal.\n\n")
        f.write("```mermaid\n")
        f.write("xychart-beta\n")
        f.write(f'    title "Daily Velocity"\n')
        f.write(f'    x-axis {to_mermaid_list(dates)}\n')
        f.write(f'    y-axis "Issues" 0 --> {max(max(new_counts), max(fixed_counts)) + 2}\n')
        f.write(f'    bar {to_mermaid_list(new_counts)}\n')
        f.write(f'    line {to_mermaid_list(fixed_counts)}\n')
        f.write("```\n\n")
        
        # Chart 3: Critical & High
        f.write("## 3. Critical vs High Trend\n")
        f.write("Splitting top priorities. **Line 1 (Lower)** = Critical, **Line 2 (Higher)** = High.\n\n")
        f.write("```mermaid\n")
        f.write("xychart-beta\n")
        f.write(f'    title "Critical (Lower) vs High (Higher)"\n')
        f.write(f'    x-axis {to_mermaid_list(dates)}\n')
        # Dynamic Y max
        y_max = max(max(critical_only_counts), max(high_only_counts)) + 5
        f.write(f'    y-axis "Count" 0 --> {y_max}\n')
        f.write(f'    line {to_mermaid_list(critical_only_counts)}\n')
        f.write(f'    line {to_mermaid_list(high_only_counts)}\n')
        f.write("```\n\n")

        # Chart 4: Convergence Prediction (Linear Forecast)
        # Simple projection based on last 7 days velocity
        avg_velocity = 0
        if len(fixed_counts) >= 7:
            recent_net = [new_counts[i] - fixed_counts[i] for i in range(-7, 0)]
            avg_net_change = sum(recent_net) / 7
        else:
            avg_net_change = (sum(new_counts) - sum(fixed_counts)) / len(new_counts) if new_counts else 0

        current_open = open_counts[-1]
        forecast_dates = [dates[-1]]
        forecast_counts = [current_open]
        
        # Project 4 weeks into future
        # Note: avg_net_change must be NEGATIVE to converge.
        prediction_note = ""
        if avg_net_change >= 0:
            prediction_note = f"> ⚠️ **Warning:** Backlog is growing (Net: +{avg_net_change:.1f}/day). No convergence in sight."
        else:
            days_to_zero = abs(current_open / avg_net_change)
            prediction_note = f"> 🟢 **Prediction:** At current velocity ({avg_net_change:.1f}/day), backlog will clear in ~{int(days_to_zero)} days."

            # Generate forecast points
            for i in range(1, 4):
                 # Weekly steps
                 future_val = current_open + (avg_net_change * 7 * i)
                 if future_val < 0: future_val = 0
                 forecast_counts.append(int(future_val))
                 forecast_dates.append(f"+{i}W")

        f.write("## 4. Convergence Forecast\n")
        f.write(f"{prediction_note}\n\n")
        
        if avg_net_change < 0:
            f.write("```mermaid\n")
            f.write("xychart-beta\n")
            f.write(f'    title "Burndown Forecast"\n')
            f.write(f'    x-axis {to_mermaid_list(forecast_dates)}\n')
            f.write(f'    y-axis "Open Bugs" 0 --> {max(forecast_counts)+10}\n')
            f.write(f'    line {to_mermaid_list(forecast_counts)}\n')
        f.write("```\n\n")

        # Chart 5: Priority Breakdown
        cursor.execute("SELECT priority, COUNT(*) FROM issues WHERE snapshot_id=? AND status NOT IN ('Closed', 'Done', 'Resolved') AND type='Bug' GROUP BY priority", (snapshots[-1][0],))
        priority_data = cursor.fetchall()
        
        f.write("## 5. Breakdown by Priority\n")
        f.write("```mermaid\n")
        f.write("pie\n")
        f.write(f'    title "By Priority ({dates[-1]})"\n')
        for p, count in priority_data:
            f.write(f'    "{p}" : {count}\n')
        f.write("```\n\n")
        
        f.write("| Priority | Count |\n|---|---|\n")
        for p, count in priority_data:
             f.write(f"| {p} | {count} |\n")
        f.write("\n")

        # Chart 6: Status Breakdown
        cursor.execute("SELECT status, COUNT(*) FROM issues WHERE snapshot_id=? AND status NOT IN ('Closed', 'Done', 'Resolved') AND type='Bug' GROUP BY status", (snapshots[-1][0],))
        status_data = cursor.fetchall()

        f.write("## 6. Breakdown by Status\n")
        f.write("State of active bugs in the workflow.\n\n")
        f.write("```mermaid\n")
        f.write("pie\n")
        f.write(f'    title "By Workflow Status ({dates[-1]})"\n')
        for s, count in status_data:
            f.write(f'    "{s}" : {count}\n')
        f.write("```\n\n")

        f.write("| Status | Count |\n|---|---|\n")
        for s, count in status_data:
             f.write(f"| {s} | {count} |\n")
        f.write("\n")

    conn.close()
    print(f"Charts generated in {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_charts()
