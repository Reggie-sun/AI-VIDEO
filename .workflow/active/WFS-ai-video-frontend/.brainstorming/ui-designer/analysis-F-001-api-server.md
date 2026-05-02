# F-001 API Server -- UI Designer Analysis

**Feature**: api-server | **Priority**: High | **Framework**: @../guidance-specification.md

## 1. UI Relevance

API Server 是纯后端功能，但对 UI 层有直接影响。UI Designer 需要定义前端如何消费 API、如何处理 API 响应状态、以及错误态和加载态的统一视觉模式。

## 2. API Consumption Patterns

### REST Endpoints -- UI Mapping

The frontend MUST map each API endpoint to a consistent UI interaction pattern:

| API Operation | HTTP Method | UI Trigger | Loading Pattern | Error Channel |
|---------------|-------------|------------|-----------------|---------------|
| Project CRUD | GET/POST/PUT | Wizard save/step change | Skeleton on load | Feature Alert |
| Shot CRUD | GET/POST/PUT/DELETE | Card editor actions | Spinner on save | Field-level + Toast |
| Pipeline Run | POST | "Run Pipeline" button | Monitor view (F-004) | System Alert |
| File serving | GET | Gallery/preview | Skeleton for images | Broken state icon |
| Run History | GET | History list load | Skeleton list | Empty state |

### SSE Connection -- UI Requirements

The frontend MUST establish an `EventSource` connection for pipeline status:

- Connection state MUST be visible: connected (green dot), reconnecting (yellow dot, pulse), disconnected (red dot)
- SSE connection indicator SHOULD be placed in the header, adjacent to wizard steps
- On disconnect, the UI MUST show an `<Alert>` banner: "Connection lost. Attempting to reconnect..."
- On reconnect, the banner MUST auto-dismiss after 2 seconds

## 3. Loading State Architecture

### Three-Tier Loading Pattern

The UI MUST implement consistent loading patterns for all API interactions:

**Tier 1: Skeleton** (initial data fetch)
```
+----------------------------------+
| [============================]   |  <-- Skeleton card
| [==========]  [===============]  |
| [============================]   |
+----------------------------------+
```
- Used for: page load, list fetch, project/shots load
- Component: `<Skeleton>` from shadcn/ui
- Pattern: Match final layout structure with animated placeholder

**Tier 2: Spinner** (mutation in progress)
- Used for: save, delete, create operations
- Component: `<Loader2 className="animate-spin" />` on the action button
- The triggering button MUST show spinner + disabled state during operation
- MUST NOT disable the entire page -- only the triggering action

**Tier 3: Progress** (long-running tasks)
- Used for: pipeline execution (F-004)
- Component: Pipeline node view with per-shot status
- This is F-004's primary UI -- see @analysis-F-004-generation-monitor.md

### Optimistic Updates

For shot reordering (F-003), the UI SHOULD apply optimistic updates:
- Reorder cards immediately in local state
- Show subtle "syncing" indicator on the moved card
- On API failure: revert position + show toast error

## 4. Error Handling Visual Specification

### Error Hierarchy

The frontend MUST render errors at the appropriate level:

**Field-Level Errors** (form validation -- F-002, F-003, F-007):
```
+----------------------------------+
| Prompt *                         |
| [                               ]|
|   This field is required         |  <-- Red text below field
+----------------------------------+
```
- Red border on input: `border-destructive`
- Error message below: `text-sm text-destructive`
- MUST appear on blur for required fields, on submit for all

**Feature-Level Errors** (API business errors):
- `<Alert variant="destructive">` at top of content area
- Dismissible with X button
- MUST include: error code (if available), human-readable message, retry button

**System-Level Errors** (network, 5xx):
- Full-page error boundary
- Large icon (`AlertTriangle`), message, "Retry" button
- MUST preserve user's current navigation state for retry

### API Error Response Mapping

The frontend MUST map API error responses to user-friendly messages:

| API Error Code | UI Message | Visual |
|----------------|------------|--------|
| CONFIG_INVALID | "Some settings need attention. Check the highlighted fields." | Field-level highlights |
| DISK_SPACE_LOW | "Not enough disk space. Free up space and try again." | Feature Alert + cleanup tip |
| COMFY_UNREACHABLE | "Cannot reach ComfyUI. Make sure it's running." | Feature Alert + connection check |
| PIPELINE_FAILED | "Generation failed for one or more shots." | Node view error state (F-004) |

## 5. Toast Notification System

The frontend MUST implement a toast notification system for transient feedback:

- **Success**: Green accent, checkmark icon, auto-dismiss 3s
- **Info**: Blue accent, info icon, auto-dismiss 4s
- **Warning**: Yellow accent, triangle icon, manual dismiss
- **Error**: Red accent, X icon, manual dismiss + retry

Toast position: bottom-right corner, stacked vertically, max 3 visible.

Usage:
- Shot saved/deleted: Success toast
- Pipeline started: Info toast
- Disk space warning: Warning toast
- API failure with auto-retry: Error toast

## 6. API-Driven Component Patterns

### Data Fetching Hook Pattern

Each feature MUST use a consistent data fetching pattern:

```
useApiQuery(endpoint, options) → { data, isLoading, error, refetch }
useApiMutation(endpoint, options) → { mutate, isLoading, error }
```

The UI layer MUST NOT make raw fetch calls -- all API interactions go through these hooks to ensure consistent loading/error handling.

### File URL Pattern

API-served files (videos, images) MUST use a consistent URL pattern:
- `GET /api/files/{run_id}/{shot_id}/{artifact_type}`

The `<VideoPlayer>` and `<FrameThumbnail>` components MUST construct URLs using this pattern, never hardcode paths.

## 7. Key Recommendations

1. The frontend MUST abstract all API interactions behind custom hooks for consistent state management
2. SSE connection state MUST be globally visible, not hidden from users
3. Loading skeletons MUST match the final layout shape to prevent layout shift
4. Error messages MUST be human-readable, never expose technical stack traces to users
5. Toast notifications MUST be the primary pattern for transient success/error feedback
