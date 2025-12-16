# Bug Stability Charts (12-10)

## 1. Open Bug Trend (Backlog)
Shows the total number of unresolved bugs over time. Lower is better.

```mermaid
xychart-beta
    title "Open Bug Count (06-18 to 12-10)"
    x-axis ["06-18", "06-25", "07-02", "07-09", "07-16", "07-23", "07-30", "08-06", "08-13", "08-20", "08-27", "09-03", "09-10", "09-17", "09-24", "10-01", "10-08", "10-15", "10-22", "10-29", "11-05", "11-12", "11-19", "11-26", "12-03", "12-10"]
    y-axis "Count" 57 --> 82
    line [65, 71, 71, 68, 71, 67, 67, 75, 69, 74, 73, 71, 70, 72, 68, 68, 66, 64, 77, 76, 72, 69, 68, 63, 62, 63]
```

## 2. New vs Fixed (Velocity)
Compares incoming bugs (New) vs resolved bugs (Fixed). Fixed > New is ideal.

```mermaid
xychart-beta
    title "Daily Velocity"
    x-axis ["06-18", "06-25", "07-02", "07-09", "07-16", "07-23", "07-30", "08-06", "08-13", "08-20", "08-27", "09-03", "09-10", "09-17", "09-24", "10-01", "10-08", "10-15", "10-22", "10-29", "11-05", "11-12", "11-19", "11-26", "12-03", "12-10"]
    y-axis "Issues" 0 --> 24
    bar [5, 22, 7, 16, 10, 10, 8, 18, 8, 12, 4, 3, 6, 6, 2, 1, 1, 4, 15, 2, 4, 8, 1, 0, 1, 2]
    line [8, 17, 7, 19, 7, 14, 8, 10, 15, 9, 6, 5, 7, 4, 6, 1, 3, 6, 2, 3, 8, 16, 4, 6, 9, 1]
```

## 3. Critical vs High Trend
Splitting top priorities. **Line 1 (Lower)** = Critical, **Line 2 (Higher)** = High.

```mermaid
xychart-beta
    title "Critical (Lower) vs High (Higher)"
    x-axis ["06-18", "06-25", "07-02", "07-09", "07-16", "07-23", "07-30", "08-06", "08-13", "08-20", "08-27", "09-03", "09-10", "09-17", "09-24", "10-01", "10-08", "10-15", "10-22", "10-29", "11-05", "11-12", "11-19", "11-26", "12-03", "12-10"]
    y-axis "Count" 0 --> 42
    line [5, 5, 5, 7, 6, 6, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2]
    line [20, 23, 25, 25, 25, 21, 20, 22, 18, 18, 21, 21, 24, 28, 27, 27, 26, 26, 34, 35, 33, 37, 36, 31, 30, 30]
```

## 4. Convergence Forecast
> 🟢 **Prediction:** At current velocity (-4.1/day), backlog will clear in ~15 days.

```mermaid
xychart-beta
    title "Burndown Forecast"
    x-axis ["12-10", "+1W", "+2W", "+3W"]
    y-axis "Open Bugs" 0 --> 73
    line [63, 34, 4, 0]
```

## 5. Breakdown by Priority
```mermaid
pie
    title "By Priority (12-10)"
    "Critical" : 2
    "High" : 30
    "Low" : 7
    "Medium" : 24
```

| Priority | Count |
|---|---|
| Critical | 2 |
| High | 30 |
| Low | 7 |
| Medium | 24 |

## 6. Breakdown by Status
State of active bugs in the workflow.

```mermaid
pie
    title "By Workflow Status (12-10)"
    "In Test" : 1
    "Open" : 42
    "Ready for Test" : 20
```

| Status | Count |
|---|---|
| In Test | 1 |
| Open | 42 |
| Ready for Test | 20 |

