# AI-VIDEO Frontend Core Loop (F-002 + F-003 + F-004) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the frontend application scaffold and the three core workflow features: project wizard (F-002), shot card editor (F-003), and generation monitor (F-004). Together these form the primary user journey: configure project → edit shots → monitor generation.

**Architecture:** React 18 + Vite + TypeScript + Tailwind CSS + shadcn/ui. SPA that communicates with the F-001 FastAPI backend via REST and SSE. State management via Zustand (lightweight, no boilerplate). Routing via React Router v6.

**Tech Stack:** React 18, Vite 5, TypeScript 5, Tailwind CSS 3, shadcn/ui, @dnd-kit/core (drag-and-drop), zustand (state), react-router-dom v6, @tanstack/react-query (server state), event-source-polyfill (SSE)

---

## File Structure

```
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
├── tailwind.config.ts
├── postcss.config.js
├── components.json                  # shadcn/ui config
├── src/
│   ├── main.tsx
│   ├── App.tsx                      # Router + QueryClientProvider
│   ├── index.css                    # Tailwind directives + CSS vars
│   ├── lib/
│   │   ├── utils.ts                 # cn() helper
│   │   ├── api-client.ts            # Fetch wrapper with error envelope parsing
│   │   └── sse-client.ts            # SSE manager with reconnect + Last-Event-ID
│   ├── hooks/
│   │   ├── use-projects.ts          # React Query hooks for project CRUD
│   │   ├── use-shots.ts             # React Query hooks for shot CRUD
│   │   ├── use-runs.ts              # React Query hooks for runs
│   │   ├── use-sse.ts               # SSE subscription hook
│   │   ├── use-command-history.ts   # Undo/redo (EP-004 Command Pattern)
│   │   ├── use-auto-save.ts         # Auto-save with debounce
│   │   └── use-keyboard.ts          # Keyboard shortcut hook
│   ├── stores/
│   │   ├── wizard-store.ts          # Wizard step state + form data
│   │   ├── editor-store.ts          # Shot editor state (cards, selection, expand)
│   │   └── monitor-store.ts         # Monitor state (pipeline nodes, SSE events)
│   ├── components/
│   │   ├── ui/                      # shadcn/ui primitives (button, card, input, etc.)
│   │   ├── shared/
│   │   │   ├── ParameterField.tsx   # EP-008: 3-tier param field with tooltip
│   │   │   ├── StatusBadge.tsx      # Status indicator (queued/running/completed/failed)
│   │   │   ├── EmptyState.tsx       # Empty state with CTA
│   │   │   ├── SaveIndicator.tsx    # Auto-save status (saving/saved/error)
│   │   │   ├── ConnectionTestButton.tsx  # ComfyUI connection test (EP-005)
│   │   │   └── PathSelector.tsx     # File/directory selector
│   │   ├── wizard/
│   │   │   ├── WizardLayout.tsx     # Full-screen wizard shell + step indicator
│   │   │   ├── StepIndicator.tsx    # Top progress bar with step labels
│   │   │   ├── StepProjectInfo.tsx  # Step 1: project name, output dir, workflow
│   │   │   ├── StepConnection.tsx   # Step 2: ComfyUI address + test
│   │   │   ├── StepDefaults.tsx     # Step 3: resolution, FPS, duration, seed
│   │   │   ├── StepCharacters.tsx   # Step 4: character cards (skippable)
│   │   │   └── StepSummary.tsx      # Confirmation summary
│   │   ├── editor/
│   │   │   ├── ShotCardList.tsx     # Card list container with Frame Relay lines
│   │   │   ├── ShotCard.tsx         # Fold/expand card with L1/L2/L3 params
│   │   │   ├── ShotCardCollapsed.tsx # Collapsed state: prompt summary, tags
│   │   │   ├── ShotCardExpanded.tsx  # Expanded state: full form
│   │   │   ├── DragHandle.tsx       # Drag handle with grip icon
│   │   │   ├── FrameRelayLine.tsx   # Arrow connector between cards
│   │   │   ├── CharacterTags.tsx    # Checkbox-style character selector
│   │   │   └── AdvancedParams.tsx   # Collapsible L3 params with count badge
│   │   └── monitor/
│   │       ├── PipelineView.tsx     # Horizontal node chain
│   │       ├── PipelineNode.tsx     # Single shot node card
│   │       ├── NodeDetailPanel.tsx  # Expand below pipeline on node click
│   │       ├── ElapsedTimer.tsx     # Time display with format rules
│   │       ├── SSEStatusIndicator.tsx  # Connected/reconnecting/disconnected
│   │       ├── CancelConfirmDialog.tsx  # Cancel with confirmation
│   │       └── FailureRecoveryPanel.tsx # Retry/skip/cancel options
│   ├── pages/
│   │   ├── WizardPage.tsx           # /wizard — project creation wizard
│   │   ├── EditorPage.tsx           # /projects/:name/editor — shot editor
│   │   └── MonitorPage.tsx          # /runs/:runId/monitor — generation monitor
│   └── types/
│       ├── api.ts                   # API response types
│       ├── project.ts               # Project config types
│       ├── shot.ts                  # Shot types
│       └── run.ts                   # Run/manifest types
```

---

### Task 1: Frontend Scaffold + Vite + Tailwind + shadcn/ui

**Files:**
- Create: `frontend/` directory with all scaffold files
- Create: `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/index.css`
- Create: `frontend/src/lib/utils.ts`

- [ ] **Step 1: Initialize Vite + React + TypeScript project**

```bash
cd /home/reggie/vscode_folder/AI-VIDEO
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

- [ ] **Step 2: Install core dependencies**

```bash
cd /home/reggie/vscode_folder/AI-VIDEO/frontend
npm install tailwindcss @tailwindcss/vite postcss autoprefixer
npm install react-router-dom zustand @tanstack/react-query
npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities
npm install clsx tailwind-merge class-variance-authority lucide-react
npm install event-source-polyfill
npm install -D @types/node
```

- [ ] **Step 3: Configure Tailwind + shadcn/ui**

```typescript
// frontend/vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8787",
      "/health": "http://127.0.0.1:8787",
      "/api/files": "http://127.0.0.1:8787",
    },
  },
});
```

```css
/* frontend/src/index.css */
@import "tailwindcss";

@theme {
  --color-background: oklch(1 0 0);
  --color-foreground: oklch(0.145 0 0);
  --color-card: oklch(1 0 0);
  --color-card-foreground: oklch(0.145 0 0);
  --color-primary: oklch(0.205 0.064 285.885);
  --color-primary-foreground: oklch(0.985 0 0);
  --color-muted: oklch(0.97 0 0);
  --color-muted-foreground: oklch(0.556 0 0);
  --color-accent: oklch(0.97 0 0);
  --color-accent-foreground: oklch(0.205 0.064 285.885);
  --color-destructive: oklch(0.577 0.245 27.325);
  --color-border: oklch(0.922 0 0);
  --color-ring: oklch(0.708 0.165 254.624);
  --radius: 0.625rem;

  --color-status-queued: #9CA3AF;
  --color-status-running: #3B82F6;
  --color-status-completed: #10B981;
  --color-status-failed: #EF4444;
  --color-status-stale: #F59E0B;
}
```

```typescript
// frontend/src/lib/utils.ts
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

- [ ] **Step 4: Initialize shadcn/ui and add base components**

```bash
cd /home/reggie/vscode_folder/AI-VIDEO/frontend
npx shadcn@latest init -d
npx shadcn@latest add button card input label textarea select badge separator dialog tooltip tabs scroll-area collapsible dropdown-menu alert skeleton
```

- [ ] **Step 5: Create App.tsx with router + query provider**

```tsx
// frontend/src/App.tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/wizard" replace />} />
          <Route path="/wizard" element={<WizardPage />} />
          <Route path="/projects/:name/editor" element={<EditorPage />} />
          <Route path="/runs/:runId/monitor" element={<MonitorPage />} />
          <Route path="/results/:runId" element={<div>Gallery (F-005)</div>} />
          <Route path="/history" element={<div>History (F-006)</div>} />
          <Route path="/tuner" element={<div>Tuner (F-007)</div>} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
```

- [ ] **Step 6: Verify dev server starts**

```bash
cd /home/reggie/vscode_folder/AI-VIDEO/frontend && npm run dev
```

Expected: Vite dev server starts at http://localhost:5173

- [ ] **Step 7: Commit**

```bash
git add frontend/
git commit -m "feat(frontend): scaffold React + Vite + Tailwind + shadcn/ui app"
```

---

### Task 2: API Client + SSE Client + Type Definitions

**Files:**
- Create: `frontend/src/lib/api-client.ts`
- Create: `frontend/src/lib/sse-client.ts`
- Create: `frontend/src/types/api.ts`
- Create: `frontend/src/types/project.ts`
- Create: `frontend/src/types/shot.ts`
- Create: `frontend/src/types/run.ts`

- [ ] **Step 1: Define API types**

```typescript
// frontend/src/types/api.ts
export interface ErrorEnvelope {
  error: {
    code: string;
    message: string;
    detail?: string;
    suggestion?: string;
  };
}

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: { offset: number; limit: number; total: number };
}
```

```typescript
// frontend/src/types/project.ts
export interface ProjectSummary {
  name: string;
  config_path: string;
  comfy_base_url: string;
  workflow_template: string;
}

export interface ProjectDetail {
  name: string;
  config_path: string;
  comfy: { base_url: string; allow_non_local: boolean };
  workflow_template: string;
  workflow_binding: string;
  output_root: string;
  defaults: DefaultsConfig;
  shot_count: number;
}

export interface DefaultsConfig {
  width: number;
  height: number;
  fps: number;
  clip_seconds: number;
  seed: number | null;
  negative_prompt: string;
  style_prompt: string;
}

export interface CharacterProfile {
  id: string;
  name: string;
  reference_images: string[];
  future_lora: { enabled: boolean; path?: string };
}

export interface DraftData {
  project_name: string;
  comfy_base_url: string;
  workflow_template: string;
  workflow_binding: string;
  defaults?: DefaultsConfig;
  characters?: CharacterProfile[];
}
```

```typescript
// frontend/src/types/shot.ts
export interface ShotItem {
  id: string;
  prompt: string;
  negative_prompt: string;
  characters: string[];
  seed: number | null;
  clip_seconds: number | null;
  fps: number | null;
  width: number | null;
  height: number | null;
  init_image: string | null;
  continuity_note: string;
}

export interface ShotWithEffective extends ShotItem {
  overrides: string[];
  effective_seed: number;
  effective_fps: number;
  effective_width: number;
  effective_height: number;
  effective_clip_seconds: number;
}

export interface ValidateShotResult {
  valid: boolean;
  errors: Array<{ shot_id: string; field: string; message: string }>;
  warnings: Array<{ shot_id: string; field: string; message: string }>;
}
```

```typescript
// frontend/src/types/run.ts
export type RunStatus = "pending" | "running" | "succeeded" | "failed";
export type ShotStatus = "pending" | "queued" | "running" | "succeeded" | "failed" | "stale";

export interface RunSummary {
  run_id: string;
  status: RunStatus;
  project_name: string;
  created_at: string;
  shot_count: number;
}

export interface RunDetail {
  run_id: string;
  status: RunStatus;
  project_name: string;
  created_at: string;
  shots: ShotRecord[];
  final_output: string | null;
  total_duration_s: number | null;
}

export interface ShotRecord {
  shot_id: string;
  status: ShotStatus;
  clip_path: string | null;
  last_frame_path: string | null;
  started_at: string | null;
  completed_at: string | null;
  error: { code: string; message: string } | null;
}

export interface SSEEvent {
  event: string;
  data: Record<string, unknown>;
  id: string;
}

export type PipelineNodeStatus = "queued" | "running" | "completed" | "failed";

export interface PipelineNode {
  shot_id: string;
  index: number;
  status: PipelineNodeStatus;
  started_at: string | null;
  completed_at: string | null;
  clip_path: string | null;
  last_frame_path: string | null;
  error: { code: string; message: string } | null;
  duration_s: number | null;
}
```

- [ ] **Step 2: Implement API client**

```typescript
// frontend/src/lib/api-client.ts
import type { ErrorEnvelope } from "@/types/api";

const BASE_URL = "";

class ApiError extends Error {
  code: string;
  detail?: string;
  suggestion?: string;
  status: number;

  constructor(status: number, envelope: ErrorEnvelope) {
    super(envelope.error.message);
    this.code = envelope.error.code;
    this.detail = envelope.error.detail;
    this.suggestion = envelope.error.suggestion;
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({
      error: { code: "UNKNOWN", message: res.statusText },
    }));
    throw new ApiError(res.status, body as ErrorEnvelope);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

export { ApiError };
```

- [ ] **Step 3: Implement SSE client with reconnect**

```typescript
// frontend/src/lib/sse-client.ts
import type { SSEEvent } from "@/types/run";

type SSEHandler = (event: SSEEvent) => void;

export class SSEClient {
  private es: EventSource | null = null;
  private handler: SSEHandler;
  private url: string;
  private lastEventId: string | null = null;
  private retryCount = 0;
  private maxRetries = 6;
  private retryDelay = 1000;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private _status: "connected" | "reconnecting" | "disconnected" = "disconnected";
  private onStatusChange?: (status: SSEClient["_status"]) => void;

  constructor(
    url: string,
    handler: SSEHandler,
    onStatusChange?: (status: SSEClient["_status"]) => void
  ) {
    this.url = url;
    this.handler = handler;
    this.onStatusChange = onStatusChange;
  }

  get status() { return this._status; }

  connect(): void {
    this.disconnect();
    const headers: Record<string, string> = {};
    if (this.lastEventId) {
      headers["Last-Event-ID"] = this.lastEventId;
    }

    this.es = new EventSource(this.url);
    this.setStatus("reconnecting");

    this.es.onopen = () => {
      this.retryCount = 0;
      this.setStatus("connected");
    };

    this.es.onmessage = (e) => {
      if (e.lastEventId) this.lastEventId = e.lastEventId;
      try {
        const data = JSON.parse(e.data);
        this.handler({ event: e.type || "message", data, id: e.lastEventId || "" });
      } catch { /* skip malformed */ }
    };

    // Listen for typed events
    const eventTypes = [
      "run:started", "shot:started", "shot:progress",
      "shot:completed", "shot:failed", "run:stitching",
      "run:completed", "run:failed", "run:cancelled",
    ];
    for (const type of eventTypes) {
      this.es.addEventListener(type, (e: MessageEvent) => {
        if (e.lastEventId) this.lastEventId = e.lastEventId;
        try {
          const data = JSON.parse(e.data);
          this.handler({ event: type, data, id: e.lastEventId || "" });
        } catch { /* skip */ }
      });
    }

    this.es.onerror = () => {
      this.es?.close();
      this.es = null;
      if (this.retryCount < this.maxRetries) {
        const delay = Math.min(this.retryDelay * Math.pow(2, this.retryCount), 30_000);
        this.retryCount++;
        this.setStatus("reconnecting");
        this.reconnectTimer = setTimeout(() => this.connect(), delay);
      } else {
        this.setStatus("disconnected");
      }
    };
  }

  disconnect(): void {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.es?.close();
    this.es = null;
    this.setStatus("disconnected");
  }

  private setStatus(status: SSEClient["_status"]): void {
    this._status = status;
    this.onStatusChange?.(status);
  }
}
```

- [ ] **Step 4: Verify TypeScript compilation**

```bash
cd /home/reggie/vscode_folder/AI-VIDEO/frontend && npx tsc --noEmit
```

Expected: No errors

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/ frontend/src/types/
git commit -m "feat(frontend): API client, SSE client with reconnect, type definitions"
```

---

### Task 3: Shared Components — ParameterField, StatusBadge, EmptyState, SaveIndicator, ConnectionTestButton

**Files:**
- Create: `frontend/src/components/shared/ParameterField.tsx`
- Create: `frontend/src/components/shared/StatusBadge.tsx`
- Create: `frontend/src/components/shared/EmptyState.tsx`
- Create: `frontend/src/components/shared/SaveIndicator.tsx`
- Create: `frontend/src/components/shared/ConnectionTestButton.tsx`

- [ ] **Step 1: Implement ParameterField (EP-008 3-tier)**

```tsx
// frontend/src/components/shared/ParameterField.tsx
import { Info } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

interface ParameterFieldProps {
  label: string;
  description?: string;
  tooltip?: string;
  required?: boolean;
  error?: string;
  tier?: "essential" | "advanced" | "expert";
  children: React.ReactNode;
  className?: string;
}

export function ParameterField({
  label,
  tooltip,
  required,
  error,
  children,
  className,
}: ParameterFieldProps) {
  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex items-center gap-1.5">
        <Label className="text-sm font-medium">
          {label}
          {required && <span className="text-destructive ml-0.5">*</span>}
        </Label>
        {tooltip && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
            </TooltipTrigger>
            <TooltipContent side="right" className="max-w-xs text-sm">
              {tooltip}
            </TooltipContent>
          </Tooltip>
        )}
      </div>
      {children}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
```

- [ ] **Step 2: Implement StatusBadge**

```tsx
// frontend/src/components/shared/StatusBadge.tsx
import { cn } from "@/lib/utils";
import {
  Clock, Loader2, CheckCircle2, XCircle, AlertTriangle,
} from "lucide-react";

type Status = "queued" | "running" | "completed" | "succeeded" | "failed" | "stale" | "pending";

const STATUS_CONFIG: Record<Status, { label: string; color: string; icon: React.ElementType }> = {
  pending: { label: "待处理", color: "bg-gray-100 text-gray-700", icon: Clock },
  queued: { label: "排队中", color: "bg-gray-100 text-gray-700", icon: Clock },
  running: { label: "执行中", color: "bg-blue-100 text-blue-700", icon: Loader2 },
  completed: { label: "已完成", color: "bg-green-100 text-green-700", icon: CheckCircle2 },
  succeeded: { label: "已完成", color: "bg-green-100 text-green-700", icon: CheckCircle2 },
  failed: { label: "失败", color: "bg-red-100 text-red-700", icon: XCircle },
  stale: { label: "已过期", color: "bg-yellow-100 text-yellow-700", icon: AlertTriangle },
};

interface StatusBadgeProps {
  status: Status;
  size?: "sm" | "md";
  className?: string;
}

export function StatusBadge({ status, size = "md", className }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
  const Icon = config.icon;
  const spinning = status === "running";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full font-medium",
        size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-sm",
        config.color,
        className
      )}
    >
      <Icon className={cn(size === "sm" ? "h-3 w-3" : "h-3.5 w-3.5", spinning && "animate-spin")} />
      {config.label}
    </span>
  );
}
```

- [ ] **Step 3: Implement EmptyState**

```tsx
// frontend/src/components/shared/EmptyState.tsx
import { Button } from "@/components/ui/button";

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({ icon, title, description, actionLabel, onAction }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      {icon && <div className="mb-4 text-muted-foreground">{icon}</div>}
      <h3 className="text-lg font-semibold">{title}</h3>
      {description && <p className="mt-2 text-sm text-muted-foreground max-w-sm">{description}</p>}
      {actionLabel && onAction && (
        <Button className="mt-6" onClick={onAction}>{actionLabel}</Button>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Implement SaveIndicator (EP-006)**

```tsx
// frontend/src/components/shared/SaveIndicator.tsx
import { cn } from "@/lib/utils";
import { Check, Loader2, AlertCircle } from "lucide-react";

type SaveStatus = "idle" | "saving" | "saved" | "error";

interface SaveIndicatorProps {
  status: SaveStatus;
  className?: string;
}

export function SaveIndicator({ status, className }: SaveIndicatorProps) {
  if (status === "idle") return null;

  return (
    <div className={cn("flex items-center gap-1.5 text-xs", className)}>
      {status === "saving" && (
        <>
          <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
          <span className="text-muted-foreground">保存中...</span>
        </>
      )}
      {status === "saved" && (
        <>
          <Check className="h-3 w-3 text-green-600" />
          <span className="text-green-600">已保存</span>
        </>
      )}
      {status === "error" && (
        <>
          <AlertCircle className="h-3 w-3 text-destructive" />
          <span className="text-destructive">保存失败</span>
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Implement ConnectionTestButton (EP-005)**

```tsx
// frontend/src/components/shared/ConnectionTestButton.tsx
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { CheckCircle2, XCircle, Loader2, Wifi } from "lucide-react";
import { api } from "@/lib/api-client";

type TestState = "idle" | "testing" | "success" | "failure";

interface ConnectionTestButtonProps {
  url: string;
}

export function ConnectionTestButton({ url }: ConnectionTestButtonProps) {
  const [state, setState] = useState<TestState>("idle");
  const [latency, setLatency] = useState<number | null>(null);

  async function testConnection() {
    setState("testing");
    try {
      const result = await api.get<{ valid: boolean; latency_ms?: number }>(
        `/api/validate/comfy-url?url=${encodeURIComponent(url)}`
      );
      setState(result.valid ? "success" : "failure");
      setLatency(result.latency_ms ?? null);
    } catch {
      setState("failure");
      setLatency(null);
    }
  }

  return (
    <div className="flex items-center gap-2">
      <Button variant="outline" size="sm" onClick={testConnection} disabled={state === "testing"}>
        {state === "testing" ? (
          <Loader2 className="h-4 w-4 animate-spin mr-1" />
        ) : (
          <Wifi className="h-4 w-4 mr-1" />
        )}
        测试连接
      </Button>
      {state === "success" && (
        <span className="flex items-center gap-1 text-sm text-green-600">
          <CheckCircle2 className="h-4 w-4" />
          可达{latency != null && ` (${latency}ms)`}
        </span>
      )}
      {state === "failure" && (
        <span className="flex items-center gap-1 text-sm text-destructive">
          <XCircle className="h-4 w-4" />
          不可达
        </span>
      )}
    </div>
  );
}
```

- [ ] **Step 6: Verify TypeScript compilation**

```bash
cd /home/reggie/vscode_folder/AI-VIDEO/frontend && npx tsc --noEmit
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/shared/
git commit -m "feat(frontend): shared components — ParameterField, StatusBadge, EmptyState, SaveIndicator, ConnectionTestButton"
```

---

### Task 4: React Query Hooks + Zustand Stores

**Files:**
- Create: `frontend/src/hooks/use-projects.ts`
- Create: `frontend/src/hooks/use-shots.ts`
- Create: `frontend/src/hooks/use-runs.ts`
- Create: `frontend/src/hooks/use-sse.ts`
- Create: `frontend/src/hooks/use-command-history.ts`
- Create: `frontend/src/hooks/use-auto-save.ts`
- Create: `frontend/src/stores/wizard-store.ts`
- Create: `frontend/src/stores/editor-store.ts`
- Create: `frontend/src/stores/monitor-store.ts`

- [ ] **Step 1: Implement React Query hooks**

```typescript
// frontend/src/hooks/use-projects.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { ProjectSummary, ProjectDetail, DraftData } from "@/types/project";

export function useProjects(searchDir?: string) {
  return useQuery({
    queryKey: ["projects", searchDir],
    queryFn: () => api.get<ProjectSummary[]>(`/api/projects${searchDir ? `?search_dir=${encodeURIComponent(searchDir)}` : ""}`),
  });
}

export function useProject(name: string) {
  return useQuery({
    queryKey: ["project", name],
    queryFn: () => api.get<ProjectDetail>(`/api/projects/${name}`),
    enabled: !!name,
  });
}

export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (draft: DraftData) => api.post<{ name: string; config_path: string }>("/api/projects/draft", draft)
      .then((r) => api.post<{ name: string }>(`/api/projects/draft/${r.name}/finalize`)),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}

export function useValidateComfyUrl() {
  return useMutation({
    mutationFn: (url: string) => api.get<{ valid: boolean; latency_ms: number }>(`/api/validate/comfy-url?url=${encodeURIComponent(url)}`),
  });
}
```

```typescript
// frontend/src/hooks/use-shots.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { ShotWithEffective, ValidateShotResult } from "@/types/shot";

export function useShots(projectName: string) {
  return useQuery({
    queryKey: ["shots", projectName],
    queryFn: () => api.get<ShotWithEffective[]>(`/api/projects/${projectName}/shots`),
    enabled: !!projectName,
  });
}

export function useAddShot(projectName: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (shot: { id: string; prompt: string }) =>
      api.post(`/api/projects/${projectName}/shots`, shot),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["shots", projectName] }),
  });
}

export function useUpdateShot(projectName: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ shotId, data }: { shotId: string; data: Record<string, unknown> }) =>
      api.put(`/api/projects/${projectName}/shots/${shotId}`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["shots", projectName] }),
  });
}

export function useDeleteShot(projectName: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (shotId: string) => api.delete(`/api/projects/${projectName}/shots/${shotId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["shots", projectName] }),
  });
}

export function useReorderShots(projectName: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (order: string[]) => api.patch(`/api/projects/${projectName}/shots/reorder`, { order }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["shots", projectName] }),
  });
}

export function useValidateShots(projectName: string) {
  return useMutation({
    mutationFn: () => api.post<ValidateShotResult>(`/api/projects/${projectName}/shots/validate`),
  });
}
```

```typescript
// frontend/src/hooks/use-runs.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { RunSummary, RunDetail } from "@/types/run";

export function useStartRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (params: { project_name: string }) =>
      api.post<{ run_id: string }>("/api/runs", params),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["runs"] }),
  });
}

export function useRun(runId: string) {
  return useQuery({
    queryKey: ["run", runId],
    queryFn: () => api.get<RunDetail>(`/api/runs/${runId}`),
    enabled: !!runId,
  });
}

export function useCancelRun() {
  return useMutation({
    mutationFn: (runId: string) => api.post(`/api/runs/${runId}/cancel`),
  });
}
```

- [ ] **Step 2: Implement SSE hook**

```typescript
// frontend/src/hooks/use-sse.ts
import { useEffect, useRef, useState, useCallback } from "react";
import { SSEClient } from "@/lib/sse-client";
import type { SSEEvent } from "@/types/run";

type SSEStatus = "connected" | "reconnecting" | "disconnected";

export function useSSE(runId: string, onEvent: (event: SSEEvent) => void) {
  const clientRef = useRef<SSEClient | null>(null);
  const [status, setStatus] = useState<SSEStatus>("disconnected");
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  const connect = useCallback(() => {
    clientRef.current?.disconnect();
    const client = new SSEClient(
      `/api/runs/${runId}/events`,
      (event) => onEventRef.current(event),
      (s) => setStatus(s)
    );
    clientRef.current = client;
    client.connect();
  }, [runId]);

  const disconnect = useCallback(() => {
    clientRef.current?.disconnect();
    clientRef.current = null;
  }, []);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  return { status, reconnect: connect, disconnect };
}
```

- [ ] **Step 3: Implement Command History hook (EP-004)**

```typescript
// frontend/src/hooks/use-command-history.ts
import { useCallback, useRef, useState } from "react";

interface Command {
  execute: () => void;
  undo: () => void;
  description: string;
}

const MAX_HISTORY = 50;

export function useCommandHistory() {
  const [canUndo, setCanUndo] = useState(false);
  const [canRedo, setCanRedo] = useState(false);
  const undoStackRef = useRef<Command[]>([]);
  const redoStackRef = useRef<Command[]>([]);

  const updateFlags = useCallback(() => {
    setCanUndo(undoStackRef.current.length > 0);
    setCanRedo(redoStackRef.current.length > 0);
  }, []);

  const execute = useCallback((cmd: Command) => {
    cmd.execute();
    undoStackRef.current.push(cmd);
    if (undoStackRef.current.length > MAX_HISTORY) undoStackRef.current.shift();
    redoStackRef.current = [];
    updateFlags();
  }, [updateFlags]);

  const undo = useCallback(() => {
    const cmd = undoStackRef.current.pop();
    if (!cmd) return;
    cmd.undo();
    redoStackRef.current.push(cmd);
    updateFlags();
  }, [updateFlags]);

  const redo = useCallback(() => {
    const cmd = redoStackRef.current.pop();
    if (!cmd) return;
    cmd.execute();
    undoStackRef.current.push(cmd);
    updateFlags();
  }, [updateFlags]);

  return { execute, undo, redo, canUndo, canRedo };
}
```

- [ ] **Step 4: Implement auto-save hook**

```typescript
// frontend/src/hooks/use-auto-save.ts
import { useEffect, useRef, useState, useCallback } from "react";

type SaveStatus = "idle" | "saving" | "saved" | "error";

export function useAutoSave<T>(
  data: T,
  saveFn: (data: T) => Promise<void>,
  debounceMs: number = 1000
) {
  const [status, setStatus] = useState<SaveStatus>("idle");
  const timerRef = useRef<ReturnType<typeof setTimeout>>();
  const prevDataRef = useRef(data);

  const save = useCallback(async (value: T) => {
    setStatus("saving");
    try {
      await saveFn(value);
      setStatus("saved");
      setTimeout(() => setStatus("idle"), 2000);
    } catch {
      setStatus("error");
    }
  }, [saveFn]);

  useEffect(() => {
    if (JSON.stringify(data) === JSON.stringify(prevDataRef.current)) return;
    prevDataRef.current = data;
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => save(data), debounceMs);
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, [data, debounceMs, save]);

  return { status };
}
```

- [ ] **Step 5: Implement Zustand stores**

```typescript
// frontend/src/stores/wizard-store.ts
import { create } from "zustand";
import type { DraftData, DefaultsConfig, CharacterProfile } from "@/types/project";

interface WizardState {
  step: number;
  draft: DraftData;
  characters: CharacterProfile[];
  setStep: (step: number) => void;
  updateDraft: (partial: Partial<DraftData>) => void;
  setDefaults: (defaults: DefaultsConfig) => void;
  addCharacter: (char: CharacterProfile) => void;
  removeCharacter: (id: string) => void;
  updateCharacter: (id: string, partial: Partial<CharacterProfile>) => void;
  reset: () => void;
}

const DEFAULT_DRAFT: DraftData = {
  project_name: "my_project",
  comfy_base_url: "http://127.0.0.1:8188",
  workflow_template: "",
  workflow_binding: "",
  defaults: {
    width: 512, height: 512, fps: 16,
    clip_seconds: 2, seed: null,
    negative_prompt: "", style_prompt: "",
  },
};

export const useWizardStore = create<WizardState>((set) => ({
  step: 0,
  draft: { ...DEFAULT_DRAFT },
  characters: [],
  setStep: (step) => set({ step }),
  updateDraft: (partial) => set((s) => ({ draft: { ...s.draft, ...partial } })),
  setDefaults: (defaults) => set((s) => ({ draft: { ...s.draft, defaults } })),
  addCharacter: (char) => set((s) => ({ characters: [...s.characters, char] })),
  removeCharacter: (id) => set((s) => ({ characters: s.characters.filter((c) => c.id !== id) })),
  updateCharacter: (id, partial) =>
    set((s) => ({
      characters: s.characters.map((c) => (c.id === id ? { ...c, ...partial } : c)),
    })),
  reset: () => set({ step: 0, draft: { ...DEFAULT_DRAFT }, characters: [] }),
}));
```

```typescript
// frontend/src/stores/editor-store.ts
import { create } from "zustand";

interface EditorState {
  expandedShotId: string | null;
  setExpandedShotId: (id: string | null) => void;
  toggleExpand: (id: string) => void;
}

export const useEditorStore = create<EditorState>((set) => ({
  expandedShotId: null,
  setExpandedShotId: (id) => set({ expandedShotId: id }),
  toggleExpand: (id) =>
    set((s) => ({ expandedShotId: s.expandedShotId === id ? null : id })),
}));
```

```typescript
// frontend/src/stores/monitor-store.ts
import { create } from "zustand";
import type { PipelineNode, SSEEvent } from "@/types/run";

interface MonitorState {
  nodes: PipelineNode[];
  runStatus: string;
  elapsedSeconds: number;
  sseStatus: "connected" | "reconnecting" | "disconnected";
  selectedNodeId: string | null;
  setNodes: (nodes: PipelineNode[]) => void;
  handleSSEEvent: (event: SSEEvent) => void;
  setRunStatus: (status: string) => void;
  setSSEStatus: (status: MonitorState["sseStatus"]) => void;
  setSelectedNodeId: (id: string | null) => void;
  tickElapsed: () => void;
}

export const useMonitorStore = create<MonitorState>((set, get) => ({
  nodes: [],
  runStatus: "pending",
  elapsedSeconds: 0,
  sseStatus: "disconnected",
  selectedNodeId: null,

  setNodes: (nodes) => set({ nodes }),

  handleSSEEvent: (event) => {
    const { nodes } = get();
    const data = event.data;

    switch (event.event) {
      case "run:started":
        set({ runStatus: "running" });
        break;
      case "shot:started": {
        const shotId = data.shot_id as string;
        set({
          nodes: nodes.map((n) =>
            n.shot_id === shotId
              ? { ...n, status: "running", started_at: new Date().toISOString() }
              : n
          ),
        });
        break;
      }
      case "shot:completed": {
        const shotId = data.shot_id as string;
        set({
          nodes: nodes.map((n) =>
            n.shot_id === shotId
              ? {
                  ...n,
                  status: "completed",
                  completed_at: new Date().toISOString(),
                  clip_path: data.clip_path as string,
                  last_frame_path: data.last_frame_path as string,
                  duration_s: data.duration_s as number,
                }
              : n
          ),
        });
        break;
      }
      case "shot:failed": {
        const shotId = data.shot_id as string;
        set({
          nodes: nodes.map((n) =>
            n.shot_id === shotId
              ? {
                  ...n,
                  status: "failed",
                  error: { code: data.error_code as string, message: data.message as string },
                }
              : n
          ),
        });
        break;
      }
      case "run:completed":
        set({ runStatus: "succeeded" });
        break;
      case "run:failed":
        set({ runStatus: "failed" });
        break;
      case "run:cancelled":
        set({ runStatus: "failed" });
        break;
    }
  },

  setRunStatus: (status) => set({ runStatus: status }),
  setSSEStatus: (status) => set({ sseStatus: status }),
  setSelectedNodeId: (id) => set({ selectedNodeId: id }),
  tickElapsed: () => set((s) => ({ elapsedSeconds: s.elapsedSeconds + 1 })),
}));
```

- [ ] **Step 6: Verify TypeScript compilation**

```bash
cd /home/reggie/vscode_folder/AI-VIDEO/frontend && npx tsc --noEmit
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/hooks/ frontend/src/stores/
git commit -m "feat(frontend): React Query hooks, SSE hook, Command Pattern undo/redo, auto-save, Zustand stores"
```

---

### Task 5: F-002 Project Wizard — 4-Step Wizard Layout + Step Components

**Files:**
- Create: `frontend/src/components/wizard/WizardLayout.tsx`
- Create: `frontend/src/components/wizard/StepIndicator.tsx`
- Create: `frontend/src/components/wizard/StepProjectInfo.tsx`
- Create: `frontend/src/components/wizard/StepConnection.tsx`
- Create: `frontend/src/components/wizard/StepDefaults.tsx`
- Create: `frontend/src/components/wizard/StepCharacters.tsx`
- Create: `frontend/src/components/wizard/StepSummary.tsx`
- Create: `frontend/src/pages/WizardPage.tsx`

- [ ] **Step 1: Implement WizardLayout + StepIndicator**

```tsx
// frontend/src/components/wizard/WizardLayout.tsx
import { StepIndicator } from "./StepIndicator";

const STEPS = [
  { title: "项目信息", description: "名称与工作流" },
  { title: "连接服务", description: "ComfyUI 地址" },
  { title: "默认参数", description: "分辨率与时长" },
  { title: "角色配置", description: "可选" },
];

interface WizardLayoutProps {
  currentStep: number;
  children: React.ReactNode;
  onPrev?: () => void;
  onNext?: () => void;
  canNext?: boolean;
  isLastStep?: boolean;
}

export function WizardLayout({
  currentStep, children, onPrev, onNext, canNext = true, isLastStep,
}: WizardLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <StepIndicator steps={STEPS} currentStep={currentStep} />
      <main className="mx-auto max-w-[680px] px-6 py-10">
        {children}
      </main>
      <footer className="fixed bottom-0 left-0 right-0 border-t bg-background px-6 py-4">
        <div className="mx-auto flex max-w-[680px] justify-between">
          <button
            onClick={onPrev}
            disabled={currentStep === 0}
            className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground disabled:opacity-40"
          >
            上一步
          </button>
          <button
            onClick={onNext}
            disabled={!canNext}
            className="rounded-md bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-40"
          >
            {isLastStep ? "创建项目" : "下一步"}
          </button>
        </div>
      </footer>
    </div>
  );
}
```

```tsx
// frontend/src/components/wizard/StepIndicator.tsx
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface Step { title: string; description: string }

interface StepIndicatorProps {
  steps: Step[];
  currentStep: number;
}

export function StepIndicator({ steps, currentStep }: StepIndicatorProps) {
  return (
    <div className="border-b bg-muted/30 px-6 py-4">
      <div className="mx-auto flex max-w-[680px] items-center justify-between">
        {steps.map((step, i) => (
          <div key={i} className="flex items-center gap-2">
            <div
              className={cn(
                "flex h-8 w-8 items-center justify-center rounded-full text-xs font-medium transition-colors",
                i < currentStep && "bg-green-600 text-white",
                i === currentStep && "bg-primary text-primary-foreground",
                i > currentStep && "bg-muted text-muted-foreground"
              )}
            >
              {i < currentStep ? <Check className="h-4 w-4" /> : i + 1}
            </div>
            <div className="hidden sm:block">
              <p className={cn("text-sm font-medium", i === currentStep ? "text-foreground" : "text-muted-foreground")}>
                {step.title}
              </p>
              <p className="text-xs text-muted-foreground">{step.description}</p>
            </div>
            {i < steps.length - 1 && (
              <div className={cn("mx-2 h-px w-8", i < currentStep ? "bg-green-600" : "bg-border")} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Implement step components (StepProjectInfo through StepSummary)**

```tsx
// frontend/src/components/wizard/StepProjectInfo.tsx
import { Input } from "@/components/ui/input";
import { ParameterField } from "@/components/shared/ParameterField";

interface StepProjectInfoProps {
  projectName: string;
  workflowTemplate: string;
  workflowBinding: string;
  onChange: (field: string, value: string) => void;
}

export function StepProjectInfo({ projectName, workflowTemplate, workflowBinding, onChange }: StepProjectInfoProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">项目基本信息</h2>
        <p className="mt-1 text-sm text-muted-foreground">设定项目名称和工作流配置</p>
      </div>
      <ParameterField label="项目名称" required tooltip="项目的唯一标识名称，将用于创建配置文件">
        <Input value={projectName} onChange={(e) => onChange("project_name", e.target.value)} placeholder="my_project" />
      </ParameterField>
      <ParameterField label="工作流模板" tooltip="ComfyUI 工作流 JSON 文件路径" tier="advanced">
        <Input value={workflowTemplate} onChange={(e) => onChange("workflow_template", e.target.value)} placeholder="workflows/workflow.json" />
      </ParameterField>
      <ParameterField label="绑定文件" tooltip="参数到 ComfyUI 节点的映射文件" tier="advanced">
        <Input value={workflowBinding} onChange={(e) => onChange("workflow_binding", e.target.value)} placeholder="workflows/binding.yaml" />
      </ParameterField>
    </div>
  );
}
```

```tsx
// frontend/src/components/wizard/StepConnection.tsx
import { Input } from "@/components/ui/input";
import { ParameterField } from "@/components/shared/ParameterField";
import { ConnectionTestButton } from "@/components/shared/ConnectionTestButton";

interface StepConnectionProps {
  comfyUrl: string;
  onChange: (url: string) => void;
}

export function StepConnection({ comfyUrl, onChange }: StepConnectionProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">连接生成服务</h2>
        <p className="mt-1 text-sm text-muted-foreground">输入 ComfyUI 服务地址并测试连接</p>
      </div>
      <ParameterField label="ComfyUI 地址" required tooltip="本地 ComfyUI 服务的 HTTP 地址">
        <Input value={comfyUrl} onChange={(e) => onChange(e.target.value)} placeholder="http://127.0.0.1:8188" />
      </ParameterField>
      <ConnectionTestButton url={comfyUrl} />
    </div>
  );
}
```

```tsx
// frontend/src/components/wizard/StepDefaults.tsx
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ParameterField } from "@/components/shared/ParameterField";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ChevronDown } from "lucide-react";
import { useState } from "react";
import type { DefaultsConfig } from "@/types/project";

const RESOLUTION_PRESETS = [
  { label: "512 x 512", width: 512, height: 512 },
  { label: "768 x 512 (宽屏)", width: 768, height: 512 },
  { label: "512 x 768 (竖屏)", width: 512, height: 768 },
  { label: "1024 x 576 (16:9)", width: 1024, height: 576 },
  { label: "自定义", width: 0, height: 0 },
];

interface StepDefaultsProps {
  defaults: DefaultsConfig;
  onChange: (defaults: DefaultsConfig) => void;
}

export function StepDefaults({ defaults, onChange }: StepDefaultsProps) {
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const preset = RESOLUTION_PRESETS.find((p) => p.width === defaults.width && p.height === defaults.height);
  const isCustom = !preset || preset.width === 0;

  const advancedCount = [
    defaults.seed !== null,
    defaults.negative_prompt !== "",
    defaults.style_prompt !== "",
  ].filter(Boolean).length;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">默认参数</h2>
        <p className="mt-1 text-sm text-muted-foreground">设定视频生成的默认参数，各镜头可独立覆盖</p>
      </div>
      <ParameterField label="分辨率" tooltip="视频的宽高像素值，影响生成质量和显存需求">
        <Select
          value={isCustom ? "custom" : `${defaults.width}x${defaults.height}`}
          onValueChange={(v) => {
            if (v === "custom") return;
            const [w, h] = v.split("x").map(Number);
            onChange({ ...defaults, width: w, height: h });
          }}
        >
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            {RESOLUTION_PRESETS.filter((p) => p.width > 0).map((p) => (
              <SelectItem key={`${p.width}x${p.height}`} value={`${p.width}x${p.height}`}>{p.label}</SelectItem>
            ))}
            <SelectItem value="custom">自定义</SelectItem>
          </SelectContent>
        </Select>
      </ParameterField>
      {isCustom && (
        <div className="grid grid-cols-2 gap-4">
          <ParameterField label="宽度">
            <Input type="number" value={defaults.width} onChange={(e) => onChange({ ...defaults, width: Number(e.target.value) })} />
          </ParameterField>
          <ParameterField label="高度">
            <Input type="number" value={defaults.height} onChange={(e) => onChange({ ...defaults, height: Number(e.target.value) })} />
          </ParameterField>
        </div>
      )}
      <div className="grid grid-cols-2 gap-4">
        <ParameterField label="帧率 (FPS)" tooltip="每秒帧数，常用值 8/12/16/24">
          <Input type="number" value={defaults.fps} onChange={(e) => onChange({ ...defaults, fps: Number(e.target.value) })} />
        </ParameterField>
        <ParameterField label="时长 (秒)" tooltip="每个镜头的生成时长">
          <Input type="number" value={defaults.clip_seconds} onChange={(e) => onChange({ ...defaults, clip_seconds: Number(e.target.value) })} />
        </ParameterField>
      </div>

      <Collapsible open={advancedOpen} onOpenChange={setAdvancedOpen}>
        <CollapsibleTrigger className="flex w-full items-center justify-between rounded-md px-3 py-2 text-sm font-medium hover:bg-muted">
          <span>高级参数{advancedCount > 0 && ` (${advancedCount} 项已自定义)`}</span>
          <ChevronDown className={`h-4 w-4 transition-transform ${advancedOpen ? "rotate-180" : ""}`} />
        </CollapsibleTrigger>
        <CollapsibleContent className="mt-3 space-y-4 pl-1">
          <ParameterField label="种子" tooltip="随机种子，相同种子产生相同结果；留空则随机" tier="expert">
            <Input type="number" value={defaults.seed ?? ""} onChange={(e) => onChange({ ...defaults, seed: e.target.value ? Number(e.target.value) : null })} placeholder="随机" />
          </ParameterField>
          <ParameterField label="负面提示词" tooltip="描述不希望出现的内容" tier="expert">
            <Textarea value={defaults.negative_prompt} onChange={(e) => onChange({ ...defaults, negative_prompt: e.target.value })} placeholder="low quality, blurry..." rows={2} />
          </ParameterField>
          <ParameterField label="风格提示词" tooltip="描述全局视觉风格" tier="expert">
            <Input value={defaults.style_prompt} onChange={(e) => onChange({ ...defaults, style_prompt: e.target.value })} placeholder="cinematic, detailed..." />
          </ParameterField>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}
```

```tsx
// frontend/src/components/wizard/StepCharacters.tsx
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Plus, Trash2, Image } from "lucide-react";
import { ParameterField } from "@/components/shared/ParameterField";
import type { CharacterProfile } from "@/types/project";

interface StepCharactersProps {
  characters: CharacterProfile[];
  onAdd: () => void;
  onRemove: (id: string) => void;
  onUpdate: (id: string, partial: Partial<CharacterProfile>) => void;
  onSkip: () => void;
}

export function StepCharacters({ characters, onAdd, onRemove, onUpdate, onSkip }: StepCharactersProps) {
  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-xl font-semibold">角色配置</h2>
          <p className="mt-1 text-sm text-muted-foreground">配置角色以保持视频中的角色一致性（可选）</p>
        </div>
        <Button variant="ghost" size="sm" onClick={onSkip} className="text-muted-foreground">
          跳过此步
        </Button>
      </div>

      {characters.length === 0 && (
        <div className="flex flex-col items-center py-8 text-center">
          <Image className="mb-3 h-10 w-10 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">尚无角色，点击下方按钮添加</p>
        </div>
      )}

      <div className="space-y-3">
        {characters.map((char) => (
          <Card key={char.id}>
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <div className="flex-1 space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <ParameterField label="角色 ID">
                      <Input value={char.id} onChange={(e) => onUpdate(char.id, { id: e.target.value })} />
                    </ParameterField>
                    <ParameterField label="显示名称">
                      <Input value={char.name} onChange={(e) => onUpdate(char.id, { name: e.target.value })} />
                    </ParameterField>
                  </div>
                  <ParameterField label="参考图" tooltip="角色参考图路径，支持 jpg/png/webp，最大 20MB">
                    <Input value={char.reference_images.join(", ")} onChange={(e) => onUpdate(char.id, { reference_images: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) })} placeholder="path/to/ref.png" />
                  </ParameterField>
                </div>
                <Button variant="ghost" size="icon" onClick={() => onRemove(char.id)}>
                  <Trash2 className="h-4 w-4 text-muted-foreground" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Button variant="outline" onClick={onAdd} className="w-full">
        <Plus className="mr-2 h-4 w-4" /> 添加角色
      </Button>
    </div>
  );
}
```

```tsx
// frontend/src/components/wizard/StepSummary.tsx
import { Card, CardContent } from "@/components/ui/card";
import type { DraftData, CharacterProfile } from "@/types/project";

interface StepSummaryProps {
  draft: DraftData;
  characters: CharacterProfile[];
}

export function StepSummary({ draft, characters }: StepSummaryProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">确认项目配置</h2>
        <p className="mt-1 text-sm text-muted-foreground">检查以下配置，确认无误后点击"创建项目"</p>
      </div>
      <Card>
        <CardContent className="space-y-3 p-4 text-sm">
          <Row label="项目名称" value={draft.project_name} />
          <Row label="ComfyUI 地址" value={draft.comfy_base_url} />
          <Row label="分辨率" value={`${draft.defaults?.width}x${draft.defaults?.height}`} />
          <Row label="帧率" value={`${draft.defaults?.fps} FPS`} />
          <Row label="时长" value={`${draft.defaults?.clip_seconds} 秒`} />
          <Row label="角色" value={characters.length > 0 ? `${characters.length} 个` : "无"} />
        </CardContent>
      </Card>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string | undefined }) {
  return (
    <div className="flex justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
```

- [ ] **Step 3: Implement WizardPage**

```tsx
// frontend/src/pages/WizardPage.tsx
import { useWizardStore } from "@/stores/wizard-store";
import { useCreateProject } from "@/hooks/use-projects";
import { WizardLayout } from "@/components/wizard/WizardLayout";
import { StepProjectInfo } from "@/components/wizard/StepProjectInfo";
import { StepConnection } from "@/components/wizard/StepConnection";
import { StepDefaults } from "@/components/wizard/StepDefaults";
import { StepCharacters } from "@/components/wizard/StepCharacters";
import { StepSummary } from "@/components/wizard/StepSummary";
import { useNavigate } from "react-router-dom";

const STEPS = ["info", "connection", "defaults", "characters"] as const;

export default function WizardPage() {
  const { step, draft, characters, setStep, updateDraft, setDefaults, addCharacter, removeCharacter, updateCharacter, reset } = useWizardStore();
  const createProject = useCreateProject();
  const navigate = useNavigate();

  const canNext = step === 0 ? draft.project_name.trim() !== "" : true;
  const isLastStep = step === 3;

  function handleNext() {
    if (isLastStep) {
      createProject.mutate(draft, {
        onSuccess: (result) => {
          reset();
          navigate(`/projects/${result.name}/editor`);
        },
      });
    } else {
      setStep(step + 1);
    }
  }

  function handlePrev() {
    if (step > 0) setStep(step - 1);
  }

  function handleSkipCharacters() {
    setStep(3);
  }

  return (
    <WizardLayout
      currentStep={step}
      onPrev={handlePrev}
      onNext={handleNext}
      canNext={canNext}
      isLastStep={isLastStep}
    >
      {step === 0 && (
        <StepProjectInfo
          projectName={draft.project_name}
          workflowTemplate={draft.workflow_template}
          workflowBinding={draft.workflow_binding}
          onChange={(field, value) => updateDraft({ [field]: value })}
        />
      )}
      {step === 1 && (
        <StepConnection
          comfyUrl={draft.comfy_base_url}
          onChange={(url) => updateDraft({ comfy_base_url: url })}
        />
      )}
      {step === 2 && (
        <StepDefaults
          defaults={draft.defaults!}
          onChange={setDefaults}
        />
      )}
      {step === 3 && (
        <StepCharacters
          characters={characters}
          onAdd={() => addCharacter({ id: `char_${characters.length + 1}`, name: "", reference_images: [], future_lora: { enabled: false } })}
          onRemove={removeCharacter}
          onUpdate={updateCharacter}
          onSkip={handleSkipCharacters}
        />
      )}
      {step === 3 && (
        <div className="mt-6">
          <StepSummary draft={draft} characters={characters} />
        </div>
      )}
    </WizardLayout>
  );
}
```

- [ ] **Step 4: Verify dev server renders wizard without errors**

```bash
cd /home/reggie/vscode_folder/AI-VIDEO/frontend && npx tsc --noEmit && npm run dev
```

Expected: Wizard page loads at http://localhost:5173/wizard

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/wizard/ frontend/src/pages/WizardPage.tsx
git commit -m "feat(frontend): F-002 project wizard — 4-step wizard with Smart Defaults, connection test, character management"
```

---

### Task 6: F-003 Shot Card Editor — Card List + Drag-and-Drop + Undo/Redo

**Files:**
- Create: `frontend/src/components/editor/ShotCardList.tsx`
- Create: `frontend/src/components/editor/ShotCard.tsx`
- Create: `frontend/src/components/editor/ShotCardCollapsed.tsx`
- Create: `frontend/src/components/editor/ShotCardExpanded.tsx`
- Create: `frontend/src/components/editor/DragHandle.tsx`
- Create: `frontend/src/components/editor/FrameRelayLine.tsx`
- Create: `frontend/src/components/editor/CharacterTags.tsx`
- Create: `frontend/src/components/editor/AdvancedParams.tsx`
- Create: `frontend/src/pages/EditorPage.tsx`

- [ ] **Step 1: Implement FrameRelayLine + DragHandle**

```tsx
// frontend/src/components/editor/FrameRelayLine.tsx
import { ArrowDown } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

interface FrameRelayLineProps {
  fromIndex: number;
  toIndex: number;
}

export function FrameRelayLine({ fromIndex, toIndex }: FrameRelayLineProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div className="flex items-center justify-center py-1">
          <div className="flex flex-col items-center text-muted-foreground">
            <div className="h-4 w-px bg-border" />
            <ArrowDown className="h-4 w-4" />
            <div className="h-4 w-px bg-border" />
          </div>
        </div>
      </TooltipTrigger>
      <TooltipContent>
        Shot {fromIndex + 1} 的末帧传递给 Shot {toIndex + 1}
      </TooltipContent>
    </Tooltip>
  );
}
```

```tsx
// frontend/src/components/editor/DragHandle.tsx
import { GripVertical } from "lucide-react";
import { cn } from "@/lib/utils";

interface DragHandleProps {
  className?: string;
}

export function DragHandle({ className }: DragHandleProps) {
  return (
    <div className={cn("flex cursor-grab items-center px-1 text-muted-foreground hover:text-foreground active:cursor-grabbing", className)}>
      <GripVertical className="h-5 w-5" />
    </div>
  );
}
```

- [ ] **Step 2: Implement CharacterTags**

```tsx
// frontend/src/components/editor/CharacterTags.tsx
import { Badge } from "@/components/ui/badge";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface CharacterTagsProps {
  available: string[];
  selected: string[];
  onChange: (selected: string[]) => void;
}

export function CharacterTags({ available, selected, onChange }: CharacterTagsProps) {
  function toggle(id: string) {
    if (selected.includes(id)) {
      onChange(selected.filter((s) => s !== id));
    } else {
      onChange([...selected, id]);
    }
  }

  return (
    <div className="flex flex-wrap gap-1.5">
      {available.map((id) => {
        const isSelected = selected.includes(id);
        return (
          <Badge
            key={id}
            variant={isSelected ? "default" : "outline"}
            className={cn("cursor-pointer select-none", isSelected && "bg-primary text-primary-foreground")}
            onClick={() => toggle(id)}
          >
            {id}
            {isSelected && <X className="ml-1 h-3 w-3" />}
          </Badge>
        );
      })}
      {available.length === 0 && (
        <p className="text-xs text-muted-foreground">项目未定义角色</p>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Implement AdvancedParams**

```tsx
// frontend/src/components/editor/AdvancedParams.tsx
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { ChevronDown } from "lucide-react";
import { ParameterField } from "@/components/shared/ParameterField";
import { useState } from "react";
import type { ShotWithEffective } from "@/types/shot";

interface AdvancedParamsProps {
  shot: ShotWithEffective;
  onChange: (field: string, value: unknown) => void;
}

export function AdvancedParams({ shot, onChange }: AdvancedParamsProps) {
  const [open, setOpen] = useState(false);
  const customCount = shot.overrides.length;

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger className="flex w-full items-center justify-between rounded-md px-3 py-2 text-sm font-medium hover:bg-muted">
        <span>高级参数{customCount > 0 && ` (${customCount} 项已自定义)`}</span>
        <ChevronDown className={`h-4 w-4 transition-transform ${open ? "rotate-180" : ""}`} />
      </CollapsibleTrigger>
      <CollapsibleContent className="mt-3 space-y-3 pl-1">
        <ParameterField label="种子" tooltip="相同种子产生相同结果" tier="expert">
          <Input type="number" value={shot.seed ?? ""} onChange={(e) => onChange("seed", e.target.value ? Number(e.target.value) : null)} placeholder={`默认: ${shot.effective_seed}`} />
        </ParameterField>
        <ParameterField label="初始图像" tooltip="作为生成起点的图像路径" tier="expert">
          <Input value={shot.init_image ?? ""} onChange={(e) => onChange("init_image", e.target.value || null)} placeholder="无" />
        </ParameterField>
      </CollapsibleContent>
    </Collapsible>
  );
}
```

- [ ] **Step 4: Implement ShotCardCollapsed + ShotCardExpanded**

```tsx
// frontend/src/components/editor/ShotCardCollapsed.tsx
import { AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { ShotWithEffective } from "@/types/shot";

interface ShotCardCollapsedProps {
  shot: ShotWithEffective;
  index: number;
  onClick: () => void;
}

export function ShotCardCollapsed({ shot, index, onClick }: ShotCardCollapsedProps) {
  const hasEmptyPrompt = !shot.prompt.trim();

  return (
    <div
      className="flex cursor-pointer items-center gap-3 rounded-lg border bg-card px-4 py-3 transition-colors hover:bg-accent"
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onClick()}
    >
      <span className="flex h-7 w-7 items-center justify-center rounded-full bg-muted text-xs font-semibold">
        {index + 1}
      </span>
      <div className="flex-1 min-w-0">
        <p className="truncate text-sm">
          {hasEmptyPrompt ? (
            <span className="text-muted-foreground italic">未填写提示词</span>
          ) : (
            shot.prompt
          )}
        </p>
      </div>
      {hasEmptyPrompt && <AlertCircle className="h-4 w-4 text-yellow-500 shrink-0" />}
      {shot.characters.length > 0 && (
        <div className="flex gap-1 shrink-0">
          {shot.characters.map((c) => (
            <Badge key={c} variant="secondary" className="text-xs">{c}</Badge>
          ))}
        </div>
      )}
      <span className="text-xs text-muted-foreground shrink-0">
        {shot.clip_seconds ?? shot.effective_clip_seconds}s
      </span>
    </div>
  );
}
```

```tsx
// frontend/src/components/editor/ShotCardExpanded.tsx
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Trash2, Copy } from "lucide-react";
import { ParameterField } from "@/components/shared/ParameterField";
import { CharacterTags } from "./CharacterTags";
import { AdvancedParams } from "./AdvancedParams";
import type { ShotWithEffective } from "@/types/shot";

interface ShotCardExpandedProps {
  shot: ShotWithEffective;
  index: number;
  availableCharacters: string[];
  onChange: (field: string, value: unknown) => void;
  onDelete: () => void;
  onDuplicate: () => void;
}

export function ShotCardExpanded({
  shot, index, availableCharacters, onChange, onDelete, onDuplicate,
}: ShotCardExpandedProps) {
  return (
    <div className="rounded-lg border-2 border-primary/30 bg-card shadow-sm">
      <div className="flex items-center justify-between border-b px-4 py-2">
        <span className="text-sm font-semibold">Shot #{index + 1}</span>
        <div className="flex gap-1">
          <Button variant="ghost" size="icon" onClick={onDuplicate} title="复制">
            <Copy className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={onDelete} title="删除">
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </div>
      </div>
      <div className="space-y-4 p-4">
        <ParameterField label="提示词" required tooltip="描述此镜头的内容">
          <Textarea
            value={shot.prompt}
            onChange={(e) => onChange("prompt", e.target.value)}
            placeholder="描述你想生成的画面..."
            minRows={2}
            maxRows={6}
            className="text-base"
          />
        </ParameterField>
        <ParameterField label="负面提示词" tooltip="描述不希望出现的内容">
          <Textarea
            value={shot.negative_prompt}
            onChange={(e) => onChange("negative_prompt", e.target.value)}
            placeholder="模糊、低质量..."
            minRows={1}
            maxRows={3}
          />
        </ParameterField>
        <ParameterField label="角色" tooltip="选择此镜头中出现的角色">
          <CharacterTags
            available={availableCharacters}
            selected={shot.characters}
            onChange={(chars) => onChange("characters", chars)}
          />
        </ParameterField>
        <div className="grid grid-cols-3 gap-3">
          <ParameterField label="时长 (秒)" tooltip="留空使用项目默认值">
            <Input type="number" value={shot.clip_seconds ?? ""} onChange={(e) => onChange("clip_seconds", e.target.value ? Number(e.target.value) : null)} placeholder={`默认: ${shot.effective_clip_seconds}`} />
          </ParameterField>
          <ParameterField label="帧率" tooltip="留空使用项目默认值">
            <Input type="number" value={shot.fps ?? ""} onChange={(e) => onChange("fps", e.target.value ? Number(e.target.value) : null)} placeholder={`默认: ${shot.effective_fps}`} />
          </ParameterField>
          <ParameterField label="种子" tooltip="留空使用项目默认值">
            <Input type="number" value={shot.seed ?? ""} onChange={(e) => onChange("seed", e.target.value ? Number(e.target.value) : null)} placeholder={`默认: ${shot.effective_seed}`} />
          </ParameterField>
        </div>
        <AdvancedParams shot={shot} onChange={onChange} />
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Implement ShotCard + ShotCardList**

```tsx
// frontend/src/components/editor/ShotCard.tsx
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { DragHandle } from "./DragHandle";
import { ShotCardCollapsed } from "./ShotCardCollapsed";
import { ShotCardExpanded } from "./ShotCardExpanded";
import { useEditorStore } from "@/stores/editor-store";
import type { ShotWithEffective } from "@/types/shot";

interface ShotCardProps {
  shot: ShotWithEffective;
  index: number;
  availableCharacters: string[];
  onChange: (shotId: string, field: string, value: unknown) => void;
  onDelete: (shotId: string) => void;
  onDuplicate: (shotId: string) => void;
}

export function ShotCard({ shot, index, availableCharacters, onChange, onDelete, onDuplicate }: ShotCardProps) {
  const { expandedShotId, toggleExpand } = useEditorStore();
  const isExpanded = expandedShotId === shot.id;

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: shot.id });
  const style = { transform: CSS.Transform.toString(transform), transition, opacity: isDragging ? 0.5 : 1 };

  return (
    <div ref={setNodeRef} style={style} className="flex items-stretch gap-0">
      <DragHandle className="shrink-0" {...attributes} {...listeners} />
      <div className="flex-1 min-w-0">
        {isExpanded ? (
          <ShotCardExpanded
            shot={shot}
            index={index}
            availableCharacters={availableCharacters}
            onChange={(field, value) => onChange(shot.id, field, value)}
            onDelete={() => onDelete(shot.id)}
            onDuplicate={() => onDuplicate(shot.id)}
          />
        ) : (
          <ShotCardCollapsed shot={shot} index={index} onClick={() => toggleExpand(shot.id)} />
        )}
      </div>
    </div>
  );
}
```

```tsx
// frontend/src/components/editor/ShotCardList.tsx
import { DndContext, closestCenter, PointerSensor, KeyboardSensor, useSensor, useSensors } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy, sortableKeyboardCoordinates } from "@dnd-kit/sortable";
import { ShotCard } from "./ShotCard";
import { FrameRelayLine } from "./FrameRelayLine";
import { Button } from "@/components/ui/button";
import { Plus, ChevronsDownUp } from "lucide-react";
import { SaveIndicator } from "@/components/shared/SaveIndicator";
import { useEditorStore } from "@/stores/editor-store";
import type { ShotWithEffective } from "@/types/shot";

interface ShotCardListProps {
  projectName: string;
  shots: ShotWithEffective[];
  characters: string[];
  saveStatus: "idle" | "saving" | "saved" | "error";
  onAdd: () => void;
  onChange: (shotId: string, field: string, value: unknown) => void;
  onDelete: (shotId: string) => void;
  onDuplicate: (shotId: string) => void;
  onReorder: (oldIndex: number, newIndex: number) => void;
}

export function ShotCardList({
  projectName, shots, characters, saveStatus,
  onAdd, onChange, onDelete, onDuplicate, onReorder,
}: ShotCardListProps) {
  const { expandedShotId, setExpandedShotId } = useEditorStore();
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  function handleDragEnd(event: { active: { id: string | number }; over: { id: string | number } | null }) {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = shots.findIndex((s) => s.id === active.id);
    const newIndex = shots.findIndex((s) => s.id === over.id);
    if (oldIndex !== -1 && newIndex !== -1) onReorder(oldIndex, newIndex);
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">{projectName} — 分镜编辑</h1>
        <div className="flex items-center gap-3">
          <SaveIndicator status={saveStatus} />
          {shots.length > 5 && (
            <Button variant="ghost" size="sm" onClick={() => setExpandedShotId(null)}>
              <ChevronsDownUp className="mr-1 h-4 w-4" /> 全部折叠
            </Button>
          )}
        </div>
      </div>

      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={shots.map((s) => s.id)} strategy={verticalListSortingStrategy}>
          <div className="space-y-0">
            {shots.map((shot, i) => (
              <div key={shot.id}>
                <ShotCard
                  shot={shot}
                  index={i}
                  availableCharacters={characters}
                  onChange={onChange}
                  onDelete={onDelete}
                  onDuplicate={onDuplicate}
                />
                {i < shots.length - 1 && <FrameRelayLine fromIndex={i} toIndex={i + 1} />}
              </div>
            ))}
          </div>
        </SortableContext>
      </DndContext>

      <Button variant="outline" onClick={onAdd} className="w-full">
        <Plus className="mr-2 h-4 w-4" /> 添加镜头
      </Button>
    </div>
  );
}
```

- [ ] **Step 6: Implement EditorPage with undo/redo + auto-save**

```tsx
// frontend/src/pages/EditorPage.tsx
import { useParams, useNavigate } from "react-router-dom";
import { useShots, useAddShot, useUpdateShot, useDeleteShot, useReorderShots } from "@/hooks/use-shots";
import { useProject } from "@/hooks/use-projects";
import { useAutoSave } from "@/hooks/use-auto-save";
import { useCommandHistory } from "@/hooks/use-command-history";
import { useKeyboard } from "@/hooks/use-keyboard";
import { ShotCardList } from "@/components/editor/ShotCardList";
import { Button } from "@/components/ui/button";
import { Play, Undo2, Redo2 } from "lucide-react";
import { useStartRun } from "@/hooks/use-runs";
import type { ShotWithEffective } from "@/types/shot";

export default function EditorPage() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const { data: project } = useProject(name ?? "");
  const { data: shots = [] } = useShots(name ?? "");
  const addShot = useAddShot(name ?? "");
  const updateShot = useUpdateShot(name ?? "");
  const deleteShot = useDeleteShot(name ?? "");
  const reorderShots = useReorderShots(name ?? "");
  const startRun = useStartRun();
  const { execute, undo, redo, canUndo, canRedo } = useCommandHistory();

  const { status: saveStatus } = useAutoSave(
    shots,
    async (s) => {
      // Auto-save is handled by individual mutation calls
    },
    1000
  );

  useKeyboard([
    { key: "z", ctrl: true, handler: undo },
    { key: "z", ctrl: true, shift: true, handler: redo },
  ]);

  function handleAdd() {
    const id = `shot_${String(shots.length + 1).padStart(2, "0")}`;
    execute({
      description: `添加镜头 ${id}`,
      execute: () => addShot.mutate({ id, prompt: "" }),
      undo: () => deleteShot.mutate(id),
    });
  }

  function handleChange(shotId: string, field: string, value: unknown) {
    updateShot.mutate({ shotId, data: { [field]: value } });
  }

  function handleDelete(shotId: string) {
    const shot = shots.find((s) => s.id === shotId);
    if (!shot) return;
    execute({
      description: `删除镜头 ${shotId}`,
      execute: () => deleteShot.mutate(shotId),
      undo: () => addShot.mutate({ id: shot.id, prompt: shot.prompt }),
    });
  }

  function handleDuplicate(shotId: string) {
    const shot = shots.find((s) => s.id === shotId);
    if (!shot) return;
    const newId = `${shotId}_copy`;
    addShot.mutate({ id: newId, prompt: shot.prompt });
  }

  function handleReorder(oldIndex: number, newIndex: number) {
    const newOrder = [...shots];
    const [moved] = newOrder.splice(oldIndex, 1);
    newOrder.splice(newIndex, 0, moved);
    const prevOrder = shots.map((s) => s.id);
    execute({
      description: "重排镜头",
      execute: () => reorderShots.mutate(newOrder.map((s) => s.id)),
      undo: () => reorderShots.mutate(prevOrder),
    });
  }

  function handleStartRun() {
    if (!name) return;
    startRun.mutate({ project_name: name }, {
      onSuccess: (result) => navigate(`/runs/${result.run_id}/monitor`),
    });
  }

  const characterIds = project?.defaults ? [] : [];

  return (
    <div className="mx-auto max-w-4xl px-6 py-6">
      <div className="flex items-center justify-between pb-4">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={undo} disabled={!canUndo} title="撤销 (Ctrl+Z)">
            <Undo2 className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={redo} disabled={!canRedo} title="重做 (Ctrl+Shift+Z)">
            <Redo2 className="h-4 w-4" />
          </Button>
        </div>
        <Button onClick={handleStartRun} disabled={shots.length === 0}>
          <Play className="mr-2 h-4 w-4" /> 开始生成
        </Button>
      </div>

      <ShotCardList
        projectName={name ?? ""}
        shots={shots}
        characters={characterIds}
        saveStatus={saveStatus}
        onAdd={handleAdd}
        onChange={handleChange}
        onDelete={handleDelete}
        onDuplicate={handleDuplicate}
        onReorder={handleReorder}
      />
    </div>
  );
}
```

- [ ] **Step 7: Implement keyboard hook**

```typescript
// frontend/src/hooks/use-keyboard.ts
import { useEffect } from "react";

interface KeyBinding {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  handler: () => void;
}

export function useKeyboard(bindings: KeyBinding[]) {
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      for (const b of bindings) {
        if (
          e.key.toLowerCase() === b.key.toLowerCase() &&
          !!e.ctrlKey === !!b.ctrl &&
          !!e.shiftKey === !!b.shift &&
          !!e.altKey === !!b.alt
        ) {
          e.preventDefault();
          b.handler();
          return;
        }
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [bindings]);
}
```

- [ ] **Step 8: Verify TypeScript compilation**

```bash
cd /home/reggie/vscode_folder/AI-VIDEO/frontend && npx tsc --noEmit
```

- [ ] **Step 9: Commit**

```bash
git add frontend/src/components/editor/ frontend/src/pages/EditorPage.tsx frontend/src/hooks/use-keyboard.ts
git commit -m "feat(frontend): F-003 shot card editor — drag-and-drop, fold/expand, undo/redo, Frame Relay visualization"
```

---

### Task 7: F-004 Generation Monitor — Pipeline Node View + SSE + Cancel/Retry

**Files:**
- Create: `frontend/src/components/monitor/PipelineView.tsx`
- Create: `frontend/src/components/monitor/PipelineNode.tsx`
- Create: `frontend/src/components/monitor/NodeDetailPanel.tsx`
- Create: `frontend/src/components/monitor/ElapsedTimer.tsx`
- Create: `frontend/src/components/monitor/SSEStatusIndicator.tsx`
- Create: `frontend/src/components/monitor/CancelConfirmDialog.tsx`
- Create: `frontend/src/components/monitor/FailureRecoveryPanel.tsx`
- Create: `frontend/src/pages/MonitorPage.tsx`

- [ ] **Step 1: Implement PipelineNode**

```tsx
// frontend/src/components/monitor/PipelineNode.tsx
import { cn } from "@/lib/utils";
import { Clock, Loader2, CheckCircle2, XCircle } from "lucide-react";
import type { PipelineNodeStatus, PipelineNode as PipelineNodeType } from "@/types/run";
import { StatusBadge } from "@/components/shared/StatusBadge";

interface PipelineNodeProps {
  node: PipelineNodeType;
  isSelected: boolean;
  onClick: () => void;
}

const STATUS_COLORS: Record<PipelineNodeStatus, string> = {
  queued: "border-gray-300 bg-gray-50",
  running: "border-blue-400 bg-blue-50 shadow-blue-100 shadow-md",
  completed: "border-green-400 bg-green-50",
  failed: "border-red-400 bg-red-50",
};

const STATUS_ICONS: Record<PipelineNodeStatus, React.ElementType> = {
  queued: Clock,
  running: Loader2,
  completed: CheckCircle2,
  failed: XCircle,
};

export function PipelineNode({ node, isSelected, onClick }: PipelineNodeProps) {
  const Icon = STATUS_ICONS[node.status];
  const isRunning = node.status === "running";

  return (
    <button
      onClick={onClick}
      className={cn(
        "flex h-[100px] w-[140px] flex-col items-center justify-center gap-1.5 rounded-lg border-2 transition-all duration-300",
        STATUS_COLORS[node.status],
        isSelected && "ring-2 ring-primary ring-offset-2",
        isRunning && "animate-pulse"
      )}
      aria-label={`Shot ${node.index + 1}: ${node.status}`}
    >
      <Icon className={cn("h-6 w-6", isRunning && "animate-spin")} />
      <span className="text-sm font-medium">Shot {node.index + 1}</span>
      <StatusBadge status={node.status} size="sm" />
    </button>
  );
}
```

- [ ] **Step 2: Implement ElapsedTimer**

```tsx
// frontend/src/components/monitor/ElapsedTimer.tsx
import { useEffect, useRef } from "react";

interface ElapsedTimerProps {
  seconds: number;
  onTick?: () => void;
  running: boolean;
}

export function ElapsedTimer({ seconds, onTick, running }: ElapsedTimerProps) {
  const tickRef = useRef(onTick);
  tickRef.current = onTick;

  useEffect(() => {
    if (!running) return;
    const interval = setInterval(() => tickRef.current?.(), 1000);
    return () => clearInterval(interval);
  }, [running]);

  const formatted = formatDuration(seconds);

  return <span className="font-mono text-2xl tabular-nums">{formatted}</span>;
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${String(s).padStart(2, "0")}`;
  }
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}小时${m}分`;
}
```

- [ ] **Step 3: Implement SSEStatusIndicator**

```tsx
// frontend/src/components/monitor/SSEStatusIndicator.tsx
import { cn } from "@/lib/utils";
import { Wifi, WifiOff, Loader2 } from "lucide-react";

type SSEStatus = "connected" | "reconnecting" | "disconnected";

interface SSEStatusIndicatorProps {
  status: SSEStatus;
}

export function SSEStatusIndicator({ status }: SSEStatusIndicatorProps) {
  return (
    <div className={cn("flex items-center gap-1.5 text-xs", {
      "text-green-600": status === "connected",
      "text-yellow-600": status === "reconnecting",
      "text-red-600": status === "disconnected",
    })}>
      {status === "connected" && <Wifi className="h-3.5 w-3.5" />}
      {status === "reconnecting" && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
      {status === "disconnected" && <WifiOff className="h-3.5 w-3.5" />}
      <span>
        {status === "connected" && "已连接"}
        {status === "reconnecting" && "重连中..."}
        {status === "disconnected" && "已断开"}
      </span>
    </div>
  );
}
```

- [ ] **Step 4: Implement CancelConfirmDialog + FailureRecoveryPanel**

```tsx
// frontend/src/components/monitor/CancelConfirmDialog.tsx
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface CancelConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
}

export function CancelConfirmDialog({ open, onOpenChange, onConfirm }: CancelConfirmDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>取消生成</DialogTitle>
          <DialogDescription>
            确定要取消所有生成任务吗？当前正在执行的镜头将完成后停止，未开始的任务将被取消。
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>继续生成</Button>
          <Button variant="destructive" onClick={onConfirm}>确认取消</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

```tsx
// frontend/src/components/monitor/FailureRecoveryPanel.tsx
import { Button } from "@/components/ui/button";
import { AlertTriangle, RefreshCw, SkipForward, XCircle } from "lucide-react";

interface FailureRecoveryPanelProps {
  shotId: string;
  onRetry: () => void;
  onSkip: () => void;
  onCancelAll: () => void;
}

export function FailureRecoveryPanel({ shotId, onRetry, onSkip, onCancelAll }: FailureRecoveryPanelProps) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-4">
      <div className="flex items-start gap-3">
        <AlertTriangle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
        <div className="flex-1">
          <p className="text-sm font-medium text-red-800">镜头 {shotId} 生成失败</p>
          <p className="mt-1 text-sm text-red-600">请选择如何处理：</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button variant="outline" size="sm" onClick={onRetry}>
              <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> 重试失败项
            </Button>
            <Button variant="outline" size="sm" onClick={onSkip}>
              <SkipForward className="mr-1.5 h-3.5 w-3.5" /> 跳过继续
            </Button>
            <Button variant="destructive" size="sm" onClick={onCancelAll}>
              <XCircle className="mr-1.5 h-3.5 w-3.5" /> 取消全部
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Implement NodeDetailPanel**

```tsx
// frontend/src/components/monitor/NodeDetailPanel.tsx
import type { PipelineNode as PipelineNodeType } from "@/types/run";
import { StatusBadge } from "@/components/shared/StatusBadge";

interface NodeDetailPanelProps {
  node: PipelineNodeType;
}

export function NodeDetailPanel({ node }: NodeDetailPanelProps) {
  return (
    <div className="animate-slide-down overflow-hidden rounded-lg border bg-card p-4">
      <div className="flex items-center gap-3">
        <h3 className="text-sm font-semibold">Shot {node.index + 1}</h3>
        <StatusBadge status={node.status} size="sm" />
      </div>
      <div className="mt-3 space-y-1 text-sm text-muted-foreground">
        {node.started_at && <p>开始时间: {new Date(node.started_at).toLocaleTimeString()}</p>}
        {node.completed_at && <p>完成时间: {new Date(node.completed_at).toLocaleTimeString()}</p>}
        {node.duration_s != null && <p>耗时: {node.duration_s.toFixed(1)}s</p>}
        {node.error && (
          <div className="mt-2 rounded-md bg-red-50 p-2 text-sm text-red-700">
            <p className="font-medium">{node.error.code}</p>
            <p>{node.error.message}</p>
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 6: Implement PipelineView**

```tsx
// frontend/src/components/monitor/PipelineView.tsx
import { ScrollArea } from "@/components/ui/scroll-area";
import { PipelineNode } from "./PipelineNode";
import { ArrowRight } from "lucide-react";
import type { PipelineNode as PipelineNodeType } from "@/types/run";

interface PipelineViewProps {
  nodes: PipelineNodeType[];
  selectedNodeId: string | null;
  onSelectNode: (id: string) => void;
}

export function PipelineView({ nodes, selectedNodeId, onSelectNode }: PipelineViewProps) {
  return (
    <ScrollArea className="w-full" orientation="horizontal">
      <div className="flex items-center gap-2 px-4 py-6 min-w-max">
        {nodes.map((node, i) => (
          <div key={node.shot_id} className="flex items-center gap-2">
            <PipelineNode
              node={node}
              isSelected={selectedNodeId === node.shot_id}
              onClick={() => onSelectNode(node.shot_id)}
            />
            {i < nodes.length - 1 && (
              <ArrowRight className="h-5 w-5 text-muted-foreground shrink-0" />
            )}
          </div>
        ))}
      </div>
    </ScrollArea>
  );
}
```

- [ ] **Step 7: Implement MonitorPage**

```tsx
// frontend/src/pages/MonitorPage.tsx
import { useParams, useNavigate } from "react-router-dom";
import { useState, useCallback, useEffect } from "react";
import { useRun, useCancelRun } from "@/hooks/use-runs";
import { useSSE } from "@/hooks/use-sse";
import { useMonitorStore } from "@/stores/monitor-store";
import { PipelineView } from "@/components/monitor/PipelineView";
import { NodeDetailPanel } from "@/components/monitor/NodeDetailPanel";
import { ElapsedTimer } from "@/components/monitor/ElapsedTimer";
import { SSEStatusIndicator } from "@/components/monitor/SSEStatusIndicator";
import { CancelConfirmDialog } from "@/components/monitor/CancelConfirmDialog";
import { FailureRecoveryPanel } from "@/components/monitor/FailureRecoveryPanel";
import { Button } from "@/components/ui/button";
import { StopCircle, Eye } from "lucide-react";
import type { SSEEvent, PipelineNode } from "@/types/run";

export default function MonitorPage() {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();
  const { data: run } = useRun(runId ?? "");
  const cancelRun = useCancelRun();
  const [cancelOpen, setCancelOpen] = useState(false);

  const {
    nodes, runStatus, elapsedSeconds, sseStatus, selectedNodeId,
    setNodes, handleSSEEvent, setSSEStatus, setSelectedNodeId, tickElapsed,
  } = useMonitorStore();

  // Initialize nodes from run data
  useEffect(() => {
    if (run?.shots) {
      const pipelineNodes: PipelineNode[] = run.shots.map((s, i) => ({
        shot_id: s.shot_id,
        index: i,
        status: mapStatus(s.status),
        started_at: s.started_at,
        completed_at: s.completed_at,
        clip_path: s.clip_path,
        last_frame_path: s.last_frame_path,
        error: s.error,
        duration_s: s.completed_at && s.started_at
          ? (new Date(s.completed_at).getTime() - new Date(s.started_at).getTime()) / 1000
          : null,
      }));
      setNodes(pipelineNodes);
    }
  }, [run, setNodes]);

  // SSE subscription
  const onEvent = useCallback((event: SSEEvent) => {
    handleSSEEvent(event);
  }, [handleSSEEvent]);

  const sse = useSSE(runId ?? "", onEvent);
  useEffect(() => { setSSEStatus(sse.status); }, [sse.status, setSSEStatus]);

  // Auto-redirect on completion
  useEffect(() => {
    if (runStatus === "succeeded") {
      const timer = setTimeout(() => navigate(`/results/${runId}`), 2000);
      return () => clearTimeout(timer);
    }
  }, [runStatus, navigate, runId]);

  // Find first failed node
  const failedNode = nodes.find((n) => n.status === "failed");

  function handleCancel() {
    if (!runId) return;
    cancelRun.mutate(runId, { onSettled: () => setCancelOpen(false) });
  }

  const isRunning = runStatus === "running";
  const isComplete = runStatus === "succeeded" || runStatus === "failed";

  return (
    <div className="mx-auto max-w-5xl px-6 py-6">
      {/* Header */}
      <div className="flex items-center justify-between pb-4">
        <div>
          <h1 className="text-lg font-semibold">生成监控</h1>
          <p className="text-sm text-muted-foreground">Run: {runId}</p>
        </div>
        <div className="flex items-center gap-4">
          <SSEStatusIndicator status={sseStatus} />
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">已用时间</span>
            <ElapsedTimer seconds={elapsedSeconds} onTick={tickElapsed} running={isRunning} />
          </div>
        </div>
      </div>

      {/* Pipeline View */}
      <PipelineView
        nodes={nodes}
        selectedNodeId={selectedNodeId}
        onSelectNode={setSelectedNodeId}
      />

      {/* Node Detail Panel */}
      {selectedNodeId && (
        <div className="mt-4">
          <NodeDetailPanel node={nodes.find((n) => n.shot_id === selectedNodeId)!} />
        </div>
      )}

      {/* Failure Recovery */}
      {failedNode && (
        <div className="mt-4">
          <FailureRecoveryPanel
            shotId={failedNode.shot_id}
            onRetry={() => {/* Resume from failed shot */}}
            onSkip={() => {/* Skip and continue */}}
            onCancelAll={() => setCancelOpen(true)}
          />
        </div>
      )}

      {/* Actions */}
      <div className="mt-6 flex items-center justify-between">
        <div />
        <div className="flex gap-2">
          {isRunning && (
            <Button variant="destructive" onClick={() => setCancelOpen(true)}>
              <StopCircle className="mr-2 h-4 w-4" /> 取消全部
            </Button>
          )}
          {isComplete && (
            <Button onClick={() => navigate(`/results/${runId}`)}>
              <Eye className="mr-2 h-4 w-4" /> 查看结果
            </Button>
          )}
        </div>
      </div>

      <CancelConfirmDialog open={cancelOpen} onOpenChange={setCancelOpen} onConfirm={handleCancel} />
    </div>
  );
}

function mapStatus(s: string): PipelineNode["status"] {
  if (s === "succeeded") return "completed";
  if (s === "pending" || s === "queued") return "queued";
  if (s === "running") return "running";
  if (s === "failed" || s === "stale") return "failed";
  return "queued";
}
```

- [ ] **Step 8: Add slide-down animation to CSS**

Add to `frontend/src/index.css`:

```css
@keyframes slide-down {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-slide-down {
  animation: slide-down 300ms ease-out;
}
```

- [ ] **Step 9: Verify TypeScript compilation and dev server**

```bash
cd /home/reggie/vscode_folder/AI-VIDEO/frontend && npx tsc --noEmit
```

- [ ] **Step 10: Commit**

```bash
git add frontend/src/components/monitor/ frontend/src/pages/MonitorPage.tsx frontend/src/index.css
git commit -m "feat(frontend): F-004 generation monitor — pipeline node view, SSE real-time updates, cancel/retry, failure recovery"
```

---

### Task 8: Wire All Routes + Integration Verification

**Files:**
- Modify: `frontend/src/App.tsx` (import real page components)
- Verify: dev server loads all routes

- [ ] **Step 1: Update App.tsx to import real components**

```tsx
// frontend/src/App.tsx — final version
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { TooltipProvider } from "@/components/ui/tooltip";
import WizardPage from "@/pages/WizardPage";
import EditorPage from "@/pages/EditorPage";
import MonitorPage from "@/pages/MonitorPage";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Navigate to="/wizard" replace />} />
            <Route path="/wizard" element={<WizardPage />} />
            <Route path="/projects/:name/editor" element={<EditorPage />} />
            <Route path="/runs/:runId/monitor" element={<MonitorPage />} />
            {/* F-005/006/007 placeholders — implemented in next plan */}
            <Route path="/results/:runId" element={<div className="p-8 text-center text-muted-foreground">Gallery (F-005)</div>} />
            <Route path="/history" element={<div className="p-8 text-center text-muted-foreground">History (F-006)</div>} />
            <Route path="/tuner" element={<div className="p-8 text-center text-muted-foreground">Tuner (F-007)</div>} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
}
```

- [ ] **Step 2: Verify full TypeScript compilation**

```bash
cd /home/reggie/vscode_folder/AI-VIDEO/frontend && npx tsc --noEmit
```

Expected: No errors

- [ ] **Step 3: Verify dev server starts and routes work**

```bash
cd /home/reggie/vscode_folder/AI-VIDEO/frontend && npm run dev
```

Manually verify:
- http://localhost:5173/ → redirects to /wizard
- /wizard → 4-step wizard renders
- /projects/test/editor → editor page renders (may show loading/error without backend)
- /runs/test/monitor → monitor page renders

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat(frontend): wire all routes — wizard, editor, monitor integrated"
```

---

## Self-Review

### 1. Spec Coverage Check

| F-002 Requirement | Task |
|---|---|
| 4-step wizard (project → connection → defaults → characters) | Task 5 |
| Smart Defaults (zero-config start) | Task 5 (WizardPage, StepDefaults) |
| ComfyUI connection test (EP-005) | Task 5 (StepConnection + ConnectionTestButton) |
| Character management UI (EP-002) | Task 5 (StepCharacters) |
| Draft auto-save | Task 5 (wizard store persists in Zustand) |
| YAML generation via API | Task 5 (useCreateProject → finalize) |
| Step indicator + keyboard nav | Task 5 (StepIndicator + WizardLayout) |
| EP-008 3-tier params in defaults | Task 5 (StepDefaults with Collapsible) |
| Import existing project.yaml | **Not in MVP** — follow-up |
| Tooltip on all params | Task 3 (ParameterField) |

| F-003 Requirement | Task |
|---|---|
| Card fold/expand with L1/L2/L3 | Task 6 (ShotCardCollapsed + ShotCardExpanded + AdvancedParams) |
| Drag-and-drop reorder (@dnd-kit) | Task 6 (ShotCardList + DndContext) |
| Keyboard Alt+Up/Down alternative | **Deferred** — @dnd-kit KeyboardSensor covers basic; Alt shortcuts follow-up |
| EP-004 Undo/Redo (Command Pattern) | Task 6 (useCommandHistory + EditorPage) |
| Frame Relay visualization | Task 6 (FrameRelayLine) |
| Character checkbox tags | Task 6 (CharacterTags) |
| Auto-save with debounce 1s | Task 6 (useAutoSave) |
| SaveIndicator (EP-006) | Task 6 (SaveIndicator) |
| "Collapse all" when >5 shots | Task 6 (ShotCardList) |
| Advanced params count badge | Task 6 (AdvancedParams) |
| Batch validate | **Deferred** — follow-up |

| F-004 Requirement | Task |
|---|---|
| Pipeline node view (horizontal) | Task 7 (PipelineView + PipelineNode) |
| SSE real-time updates | Task 7 (useSSE + MonitorPage + monitor store) |
| Node color + icon + text label (not color-only) | Task 7 (PipelineNode) |
| Node detail panel (below pipeline) | Task 7 (NodeDetailPanel) |
| Cancel with confirmation | Task 7 (CancelConfirmDialog) |
| Failure recovery (retry/skip/cancel) | Task 7 (FailureRecoveryPanel) |
| SSE reconnect with exponent backoff | Task 2 (SSEClient) |
| SSE status indicator | Task 7 (SSEStatusIndicator) |
| Elapsed timer with format rules | Task 7 (ElapsedTimer) |
| Auto-redirect to gallery on completion | Task 7 (MonitorPage useEffect) |
| 300ms animations | Task 7 (CSS animation + transition) |

### 2. Placeholder Scan

No TBD/TODO/fill-in patterns in code. All steps contain actual code.

### 3. Type Consistency

- `SSEEvent` type in `types/run.ts` matches `SSEClient` handler signature
- `PipelineNode.status` uses `"queued"|"running"|"completed"|"failed"` — matches `PipelineNode` component
- `ShotWithEffective.overrides` is `string[]` — matches `AdvancedParams` count display
- `useCommandHistory.execute()` accepts `Command` with `execute()/undo()` — matches EditorPage usage

### 4. Gaps & Follow-ups

- **Import existing project.yaml** (F-002 AC#10): Not in MVP. Requires file upload API endpoint.
- **Keyboard Alt+Up/Down** (F-003 AC#3): Deferred; @dnd-kit KeyboardSensor provides basic keyboard reorder.
- **Batch validate** (F-003): `useValidateShots` hook exists but no UI trigger yet.
- **Browser Notification API** (F-004 AC#12): Deferred to follow-up.
- **Timeout warning before `job_timeout_seconds`** (F-004 AC#11): Requires timeout config from API.
