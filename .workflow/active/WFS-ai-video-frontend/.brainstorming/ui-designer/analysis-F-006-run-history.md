# F-006 Run History -- UI Designer Analysis

**Feature**: run-history | **Priority**: Medium | **Framework**: @../guidance-specification.md

## 1. Layout Design

### History List View

The run history MUST present past executions as a chronological list, most recent first.

```
+------------------------------------------------------------------+
|  Run History                        [Filter: All | Completed]    |
+------------------------------------------------------------------+
|                                                                   |
|  +------------------------------------------------------------+  |
|  | Run #5  |  2026-05-02 14:32  |  3/3 Completed  |  [View]  |  |
|  +------------------------------------------------------------+  |
|  | Run #4  |  2026-05-02 11:15  |  2/3 Partial    |  [View]  |  |
|  +------------------------------------------------------------+  |
|  | Run #3  |  2026-05-01 09:00  |  0/3 Failed     |  [View]  |  |
|  +------------------------------------------------------------+  |
|  | Run #2  |  2026-04-30 16:45  |  3/3 Completed  |  [View]  |  |
|  +------------------------------------------------------------+  |
|                                                                   |
|  [Load More...]                                                   |
+------------------------------------------------------------------+
```

### Access Point

The run history MUST be accessible from:
- The wizard header (history icon button)
- The generation monitor (after pipeline completion)
- Direct URL: `/history`

## 2. Run Card Design

### Card Structure

Each run maps to a manifest.json record. The card MUST display:

```
+------------------------------------------------------------+
| Run #5                                   [Status Badge]    |
| Started: 2026-05-02 14:32:05                               |
| Duration: 4m 23s                                            |
|                                                             |
| Shots: [1.Done] [2.Done] [3.Done]                          |
|                                                             |
| Project: "My Project"  |  Template: wan22_i2v              |
|                                                             |
| [View Results]  [View Details]  [Rerun]                    |
+------------------------------------------------------------+
```

**Card Elements**:
- **Run ID**: `#5` (auto-incremented, human-readable)
- **Status Badge**: `<StatusBadge>` with aggregate status (completed/partial/failed)
- **Timestamp**: Start time, formatted as relative ("2 hours ago") + absolute on hover
- **Duration**: Total pipeline execution time
- **Shot Status Row**: Mini node indicators (colored dots) showing per-shot status
- **Project Info**: Project name and workflow template name
- **Actions**: View Results (F-005), View Details (expanded manifest), Rerun (F-007)

### Card Visual Specifications

- Background: `var(--card)` with `border border-border`
- Border-radius: `rounded-xl` (0.75rem)
- Hover: `shadow-md` + slight lift
- Status left border: `border-l-4` colored by aggregate status
  - All completed: `border-l-success`
  - Partial: `border-l-warning`
  - All failed: `border-l-destructive`

## 3. Aggregate Status Logic

The run card MUST compute aggregate status from individual shot statuses:

| Shot Statuses | Aggregate | Badge Color | Label |
|--------------|-----------|-------------|-------|
| All completed | Completed | `--status-completed` | "3/3 Completed" |
| Some completed, some failed | Partial | `--status-warning` | "2/3 Partial" |
| All failed | Failed | `--status-failed` | "0/3 Failed" |
| Any running | Running | `--status-running` | "In Progress" |
| All queued | Queued | `--status-queued` | "Queued" |

## 4. Run Detail View

### Detail Panel

When "View Details" is clicked, a detail panel MUST expand or navigate to a detail page:

```
+------------------------------------------------------------+
| Run #5 -- Details                            [Close]       |
|------------------------------------------------------------|
|                                                            |
| Manifest                                                   |
|   Project:     My Project                                  |
|   Template:    wan22_i2v_api.json                          |
|   Binding:     wan22_i2v_binding.yaml                      |
|   Started:     2026-05-02 14:32:05                         |
|   Completed:   2026-05-02 14:36:28                         |
|   Duration:    4m 23s                                      |
|                                                            |
| Shot Results                                               |
|   shot_001  Completed  1.8s  [clip.mp4] [last_frame.png]  |
|   shot_002  Completed  2.1s  [clip.mp4] [last_frame.png]  |
|   shot_003  Completed  1.9s  [clip.mp4] [last_frame.png]  |
|                                                            |
| Output                                                     |
|   Final: final.mp4  (12.4 MB)                              |
|   Directory: /runs/run_20260502_143205/                    |
|                                                            |
| [View Gallery]  [Open Directory]  [Rerun with Same Params] |
+------------------------------------------------------------+
```

### Manifest Data Display

The detail view MUST show data from manifest.json:
- Project configuration summary (not the full YAML -- key fields only)
- Per-shot execution record: status, duration, output artifacts
- Output directory path (clickable to copy)
- Final output file link

### Artifact Links

Each artifact link MUST be:
- Clickable to open in browser (images play inline, videos open player)
- Right-click to download
- Show file size if available

## 5. Filtering & Sorting

### Filter Options

The history view MUST support basic filtering:

- **Status Filter**: All | Completed | Partial | Failed (tab or dropdown)
- **Date Filter**: Today | Last 7 Days | Last 30 Days | All (radio group)

### Sort Options

- Default: Most recent first (descending by start time)
- Alternative: Sort by duration (longest first)

MVP MUST implement status filter. Date filter and sort MAY be post-MVP.

### Search

MVP does NOT require text search. Post-MVP MAY add search by project name or shot prompt.

## 6. Rerun Interaction

### "Rerun" Button

The "Rerun" button on a run card MUST:
1. Open a confirmation dialog: "Rerun pipeline with the same parameters?"
2. On confirm: create a new run using the same project.yaml and shots.yaml
3. Navigate to F-004 generation monitor for the new run
4. Show toast: "New run started"

### "Rerun with Same Params" (Detail View)

From the detail view, the "Rerun with Same Params" button MUST:
1. Copy the run's configuration
2. Navigate to F-007 param-tuner pre-filled with the run's parameters
3. Allow the user to modify before starting

## 7. Empty & Loading States

### No Runs

```
+--------------------------------------------------+
|              [Clock icon]                          |
|   No run history yet.                             |
|   Your pipeline runs will appear here.            |
|   [Create First Project]                          |
+--------------------------------------------------+
```

### Loading

- Skeleton list cards matching the run card structure
- Staggered fade-in on load

### Pagination

- Default: 20 runs per page
- "Load More" button at bottom (not infinite scroll -- predictable for non-technical users)
- MUST show total count: "Showing 5 of 12 runs"

## 8. Key Recommendations

1. Run cards MUST show aggregate status at a glance -- the mini shot status dots are the key visual element
2. Relative timestamps ("2 hours ago") MUST be the primary display, with absolute timestamps on hover
3. The "Rerun" action MUST be prominently available but protected by confirmation dialog
4. The detail view MUST NOT overwhelm with raw manifest.json data -- only show curated, human-readable fields
5. Filtering MUST be simple and visual (tabs/chips, not complex form controls)
