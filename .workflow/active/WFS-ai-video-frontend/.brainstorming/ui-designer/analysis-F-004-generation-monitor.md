# F-004 Generation Monitor -- UI Designer Analysis

**Feature**: generation-monitor | **Priority**: High | **Framework**: @../guidance-specification.md

## 1. Pipeline Node View Design

Per @../guidance-specification.md D-011, the generation monitor MUST render progress as a pipeline node view with shot-level status indicators.

### Node View Layout

```
+------------------------------------------------------------------+
|  Pipeline: "My Project"                          [SSE: Connected] |
|                                                                   |
|  [1 shot_001] ──→ [2 shot_002] ──→ [3 shot_003] ──→ [Concat]   |
|   COMPLETED         RUNNING           QUEUED                      |
|   1.8s / 2s         0.5s / 2s                                      |
|                                                                   |
|  +------------------------------------------------------------+  |
|  | Shot Detail (expanded shot)                                 |  |
|  | Status: Running  |  Elapsed: 0.5s  |  Attempt: 1/2        |  |
|  | Prompt: hero enters a quiet studio...                        |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+
```

### Node Card Design

Each shot is rendered as a node card in a horizontal pipeline:

**Node Card Dimensions**: 140px wide x 100px tall

**Node Card States**:

| State | Background | Border | Icon | Animation |
|-------|-----------|--------|------|-----------|
| Queued | `bg-muted` | `border-muted-foreground/30` | `Clock` | None |
| Running | `bg-accent/10` | `border-accent` | `Loader2 animate-spin` | Pulse border |
| Completed | `bg-success/10` | `border-success` | `CheckCircle2` | Flash on complete |
| Failed | `bg-destructive/10` | `border-destructive` | `XCircle` | Shake on failure |

### Connector Design

- Lines between nodes: 2px solid, color matches source node status
- Arrow at end: filled triangle
- Active flow: animated dash pattern on the connector to running node
- Completed flow: solid colored line (success green)
- Not-yet-reached: gray dashed line

## 2. Real-Time Status Updates

### SSE-Driven UI Updates

The monitor MUST update in real-time based on SSE events:

**Status Change Animation Sequence**:
1. Node border flashes (400ms accent highlight)
2. Previous state transitions out (fade icon)
3. New state transitions in (scale + fade icon)
4. Connector to next node starts animated dash (if next is now running)
5. Progress values update with number counter animation

### Elapsed Time Display

- Running shot: MUST show elapsed time with live counter (updates every second)
- Completed shot: MUST show final duration
- Format: "0.5s" for sub-minute, "1m 23s" for longer

### Progress Estimation

MVP reports shot-level status only (per D-016). However, the UI SHOULD estimate progress:
- Show a subtle progress bar inside running nodes (based on elapsed vs. expected clip_seconds * poll_interval)
- This is approximate -- MUST be styled as "estimated" with muted colors
- MUST NOT show precise percentage

## 3. Shot Detail Panel

When a user clicks a node card, a detail panel MUST expand below the pipeline:

### Detail Panel Content

```
+----------------------------------------------------+
| shot_002 -- RUNNING                    [Close X]   |
|----------------------------------------------------|
| Status:     [Running badge]                         |
| Elapsed:    12.5s                                   |
| Attempt:    1 / 2                                   |
| Prompt:     "hero turns toward the camera..."       |
| Characters: [hero]                                  |
| Init Image:  [thumbnail]                            |
|                                                    |
| [View Logs]  [Cancel Shot]  [Skip Shot]            |
+----------------------------------------------------+
```

- Panel MUST slide down with 300ms animation
- Panel MUST auto-close if the user clicks another node (replaces content)
- "View Logs" MUST open a scrollable log viewer (read-only)
- "Cancel Shot" MUST require confirmation
- "Skip Shot" MUST require confirmation and warn about Frame Relay impact

## 4. Pipeline Control Bar

### Top-Level Actions

The monitor MUST provide pipeline-level controls:

- **Start Pipeline**: Primary button, triggers `POST /api/runs`
- **Pause Pipeline**: Secondary button (post-MVP, MAY be disabled in MVP)
- **Cancel Pipeline**: Destructive button, requires confirmation
- **Rerun Failed**: Appears when any shot fails, reruns only failed shots

### Pipeline Status Summary

A summary bar MUST be visible at all times:

```
Total: 3 shots  |  Completed: 1  |  Running: 1  |  Queued: 1  |  Failed: 0
[============================------]  33% complete
```

- Progress bar: segmented to match number of shots
- Each segment colored by shot status
- Label below: "Estimated time remaining: ~45s"

## 5. Error State Design

### Shot Failure

When a shot fails:

1. Node card shakes (200ms horizontal shake animation)
2. Node transitions to failed state (red border, X icon)
3. Detail panel auto-opens with error information
4. Pipeline pauses (remaining shots stay queued)
5. Action buttons appear: "Retry Shot", "Skip & Continue", "Cancel Pipeline"

### Error Information

The detail panel MUST show:
- Error type (timeout, ComfyUI error, etc.)
- Human-readable error message
- Attempt count vs. max_attempts
- "Retry" button if attempts remaining

### Pipeline Failure Recovery

After a failure, the UI MUST clearly present options:
- "Retry Failed Shot" -- reruns with same params
- "Skip & Continue" -- skips this shot, continues with next (warns about Frame Relay)
- "Cancel Pipeline" -- stops everything

## 6. Completion State

### Pipeline Complete

When all shots complete:

1. All nodes show completed state
2. All connectors show solid green
3. Summary bar: "Pipeline complete! 3/3 shots generated."
4. Primary CTA changes to: "View Results" (navigates to F-005 gallery)
5. Confetti or subtle celebration animation (optional, SHOULD be subtle)

### Partial Completion

If some shots failed but pipeline completed:
- Summary: "Pipeline complete with 2/3 shots generated. 1 failed."
- CTA: "View Results" + "Retry Failed"
- Failed node remains red with retry option

## 7. SSE Connection State

Per @analysis-F-001-api-server.md Section 2, the SSE connection state MUST be visible:

- Connected: `Wifi` icon, green, in monitor header
- Reconnecting: `WifiOff` icon, yellow, pulse animation
- Disconnected: `WifiOff` icon, red, with "Reconnect" button

On disconnect during active pipeline:
- MUST show warning banner: "Connection lost. Pipeline may still be running."
- MUST offer "Reconnect" button
- MUST NOT auto-cancel or show failure state

## 8. Key Recommendations

1. The horizontal pipeline node view MUST be scrollable if shots exceed viewport width
2. The detail panel MUST NOT block the pipeline view -- use bottom sheet or below-pipeline placement
3. Error recovery options MUST be visually prominent and clear -- this is the most stressful moment for users
4. The connection state indicator MUST be persistent and visible -- users need to know if updates are live
5. Time estimates SHOULD be conservative and clearly marked as estimates to manage expectations
