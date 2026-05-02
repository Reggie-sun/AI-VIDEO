# AI-VIDEO Frontend Enhancements (F-005 + F-006 + F-007) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the three frontend enhancement features: result gallery (F-005), run history (F-006), and parameter tuner (F-007). These complete the user journey: view results → browse history → tune parameters → re-run.

**Architecture:** Extends the frontend app built in the core-loop plan. Adds new pages, components, and hooks following the same patterns (React + Vite + TypeScript + Tailwind + shadcn/ui + Zustand + React Query).

**Prerequisites:** F-001 API Server plan complete, F-002/003/004 Frontend Core Loop plan complete.

---

## File Structure (Additions Only)

```
frontend/src/
├── hooks/
│   ├── use-gallery.ts               # React Query hooks for gallery API
│   └── use-run-history.ts           # React Query hooks for history API + drift detection
├── components/
│   ├── gallery/
│   │   ├── GalleryLayout.tsx        # Gallery page shell with final video + shot grid
│   │   ├── FinalVideoSection.tsx    # Prominent final.mp4 player
│   │   ├── ShotResultCard.tsx       # Shot artifact card (16:9, poster, clip)
│   │   ├── VideoPlayer.tsx          # HTML5 video wrapper with enhanced prop
│   │   ├── FrameThumbnail.tsx       # Thumbnail from last_frame.png
│   │   ├── TimelineView.tsx         # Horizontal filmstrip view
│   │   ├── GridView.tsx             # 3-column card grid (default)
│   │   └── ViewModeToggle.tsx       # Grid/Timeline icon toggle
│   ├── history/
│   │   ├── RunCard.tsx              # History run card with aggregate status
│   │   ├── RunDetailDrawer.tsx      # Run detail panel/drawer
│   │   ├── MiniShotStatus.tsx       # Row of shot status dots
│   │   ├── ConfigDriftWarning.tsx   # Config drift alert banner
│   │   ├── HistoryFilters.tsx       # Status filter tabs
│   │   └── LoadMoreButton.tsx       # "Load More" pagination
│   └── tuner/
│       ├── TunerLayout.tsx          # Dual-panel layout (40%/60%)
│       ├── ParameterPanel.tsx       # Left panel: param groups with EP-008 tiers
│       ├── PreviewPanel.tsx         # Right panel: JSON/Visual toggle
│       ├── JsonPreview.tsx          # Syntax-highlighted workflow JSON
│       ├── VisualPreview.tsx        # Image-based preview (last_frame, init_image)
│       ├── SeedControl.tsx          # Seed: value + random + lock + increment
│       ├── OverrideIndicator.tsx    # "Custom" badge + Reset button
│       ├── ScopeSelector.tsx        # Current/All/Default scope tabs
│       ├── ChangeSummary.tsx        # Pre-rerun change summary dialog
│       └── ConflictDialog.tsx       # 409 active run conflict dialog
├── pages/
│   ├── GalleryPage.tsx              # /results/:runId
│   ├── HistoryPage.tsx              # /history
│   └── TunerPage.tsx                # /tuner?run=...&shot=...&scope=...
└── lib/
    └── time-format.ts               # Relative/absolute time formatting (shared)
```

---

### Task 1: Shared Utilities — Time Formatting + Gallery/History Hooks

**Files:**
- Create: `frontend/src/lib/time-format.ts`
- Create: `frontend/src/hooks/use-gallery.ts`
- Create: `frontend/src/hooks/use-run-history.ts`

- [ ] **Step 1: Implement time formatting utility**

```typescript
// frontend/src/lib/time-format.ts

const SEVEN_DAYS_MS = 7 * 24 * 60 * 60 * 1000;

export function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();

  if (diffMs > SEVEN_DAYS_MS) {
    return date.toLocaleDateString("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit" });
  }

  const diffSeconds = Math.floor(diffMs / 1000);
  if (diffSeconds < 60) return "刚刚";
  const diffMinutes = Math.floor(diffSeconds / 60);
  if (diffMinutes < 60) return `${diffMinutes} 分钟前`;
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours} 小时前`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays === 1) return "昨天";
  if (diffDays < 7) return `${diffDays} 天前`;
  return date.toLocaleDateString("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit" });
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) {
    const m = Math.floor(seconds / 60);
    const s = Math.round(seconds % 60);
    return `${m}:${String(s).padStart(2, "0")}`;
  }
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}小时${m}分`;
}

export function formatFullTimestamp(isoString: string): string {
  return new Date(isoString).toLocaleString("zh-CN", {
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit",
  });
}
```

- [ ] **Step 2: Implement gallery hooks**

```typescript
// frontend/src/hooks/use-gallery.ts
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

export interface GalleryIndex {
  run_id: string;
  final_output: { video: string; duration_s: number } | null;
  shots: Array<{
    shot_id: string;
    clip: string;
    last_frame: string;
    normalized_clip: string | null;
    duration_s: number;
  }>;
}

export function useGallery(runId: string) {
  return useQuery({
    queryKey: ["gallery", runId],
    queryFn: () => api.get<GalleryIndex>(`/api/runs/${runId}/gallery`),
    enabled: !!runId,
  });
}

export function useLatestGallery() {
  return useQuery({
    queryKey: ["gallery", "latest"],
    queryFn: () => api.get<GalleryIndex>("/api/runs/latest/gallery"),
  });
}
```

- [ ] **Step 3: Implement run history hooks**

```typescript
// frontend/src/hooks/use-run-history.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { RunSummary, RunDetail } from "@/types/run";

export interface RunHistoryParams {
  status?: string;
  project?: string;
  offset?: number;
  limit?: number;
}

export interface RunHistoryResponse {
  data: RunSummary[];
  meta: { offset: number; limit: number; total: number };
}

export function useRunHistory(params: RunHistoryParams = {}) {
  const searchParams = new URLSearchParams();
  if (params.status) searchParams.set("status", params.status);
  if (params.project) searchParams.set("project", params.project);
  if (params.offset) searchParams.set("offset", String(params.offset));
  if (params.limit) searchParams.set("limit", String(params.limit));

  return useQuery({
    queryKey: ["runs", params],
    queryFn: () => api.get<RunHistoryResponse>(`/api/runs?${searchParams.toString()}`),
  });
}

export function useRunDetail(runId: string) {
  return useQuery({
    queryKey: ["run", runId, "detail"],
    queryFn: () => api.get<RunDetail>(`/api/runs/${runId}`),
    enabled: !!runId,
  });
}

export function useDeleteRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (runId: string) => api.delete(`/api/runs/${runId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["runs"] }),
  });
}

export interface ConfigDriftResult {
  drifted: boolean;
  changes: Array<{ field: string; old_hash: string; new_hash: string }>;
}

export function useConfigDrift(runId: string, enabled: boolean) {
  return useQuery({
    queryKey: ["run", runId, "drift"],
    queryFn: () => api.get<ConfigDriftResult>(`/api/runs/${runId}/config-drift`),
    enabled: enabled && !!runId,
  });
}

export function useRerun() {
  return useMutation({
    mutationFn: (params: { source_run_id: string; overrides: Record<string, unknown> }) =>
      api.post<{ run_id: string }>("/api/runs/re-run", params),
  });
}
```

- [ ] **Step 4: Verify TypeScript compilation**

```bash
cd /home/reggie/vscode_folder/AI-VIDEO/frontend && npx tsc --noEmit
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/time-format.ts frontend/src/hooks/use-gallery.ts frontend/src/hooks/use-run-history.ts
git commit -m "feat(frontend): time formatting, gallery hooks, run history hooks with config drift"
```

---

### Task 2: F-005 Result Gallery — VideoPlayer, GridView, TimelineView

**Files:**
- Create: `frontend/src/components/gallery/VideoPlayer.tsx`
- Create: `frontend/src/components/gallery/FrameThumbnail.tsx`
- Create: `frontend/src/components/gallery/ShotResultCard.tsx`
- Create: `frontend/src/components/gallery/FinalVideoSection.tsx`
- Create: `frontend/src/components/gallery/GridView.tsx`
- Create: `frontend/src/components/gallery/TimelineView.tsx`
- Create: `frontend/src/components/gallery/ViewModeToggle.tsx`
- Create: `frontend/src/components/gallery/GalleryLayout.tsx`
- Create: `frontend/src/pages/GalleryPage.tsx`

- [ ] **Step 1: Implement VideoPlayer (native + enhanced prop)**

```tsx
// frontend/src/components/gallery/VideoPlayer.tsx
import { cn } from "@/lib/utils";

interface VideoPlayerProps {
  src: string;
  poster?: string;
  enhanced?: boolean;
  className?: string;
  onEnded?: () => void;
}

export function VideoPlayer({ src, poster, enhanced = false, className, onEnded }: VideoPlayerProps) {
  return (
    <video
      controls
      preload="metadata"
      poster={poster}
      onEnded={onEnded}
      className={cn("w-full rounded-lg bg-black", className)}
      data-enhanced={enhanced}
    >
      <source src={src} type="video/mp4" />
      您的浏览器不支持视频播放
    </video>
  );
}
```

- [ ] **Step 2: Implement FrameThumbnail**

```tsx
// frontend/src/components/gallery/FrameThumbnail.tsx
import { cn } from "@/lib/utils";

interface FrameThumbnailProps {
  src: string;
  size?: "sm" | "md" | "lg";
  clickable?: boolean;
  onClick?: () => void;
  className?: string;
}

const SIZE_MAP = { sm: "h-16 w-28", md: "h-24 w-42", lg: "h-36 w-64" };

export function FrameThumbnail({ src, size = "md", clickable = false, onClick, className }: FrameThumbnailProps) {
  return (
    <img
      src={src}
      alt="末帧缩略图"
      loading="lazy"
      onClick={clickable ? onClick : undefined}
      className={cn(
        "rounded-md object-cover",
        SIZE_MAP[size],
        clickable && "cursor-pointer hover:opacity-80 transition-opacity",
        className
      )}
    />
  );
}
```

- [ ] **Step 3: Implement ShotResultCard**

```tsx
// frontend/src/components/gallery/ShotResultCard.tsx
import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Download, Play, AlertCircle, ImagePlus } from "lucide-react";
import { VideoPlayer } from "./VideoPlayer";
import { FrameThumbnail } from "./FrameThumbnail";

interface ShotResultCardProps {
  shotId: string;
  clipUrl: string | null;
  lastFrameUrl: string | null;
  durationS: number;
  index: number;
  onSetInitImage?: (shotId: string, lastFrameUrl: string) => void;
}

export function ShotResultCard({ shotId, clipUrl, lastFrameUrl, durationS, index, onSetInitImage }: ShotResultCardProps) {
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState(false);

  return (
    <Card className="overflow-hidden">
      <div className="relative aspect-video bg-muted">
        {error ? (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-muted-foreground">
            <AlertCircle className="h-8 w-8" />
            <p className="text-sm">视频无法加载</p>
            <Button variant="outline" size="sm" onClick={() => setError(false)}>重试</Button>
          </div>
        ) : playing && clipUrl ? (
          <VideoPlayer
            src={clipUrl}
            poster={lastFrameUrl ?? undefined}
            className="aspect-video"
            onEnded={() => setPlaying(false)}
          />
        ) : (
          <div
            className="flex h-full cursor-pointer items-center justify-center"
            onClick={() => clipUrl && setPlaying(true)}
          >
            {lastFrameUrl ? (
              <FrameThumbnail src={lastFrameUrl} size="lg" clickable className="absolute inset-0 h-full w-full" />
            ) : (
              <div className="flex items-center justify-center bg-muted h-full w-full">
                <Play className="h-10 w-10 text-muted-foreground" />
              </div>
            )}
            {clipUrl && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 hover:opacity-100 transition-opacity">
                <Play className="h-10 w-10 text-white" />
              </div>
            )}
          </div>
        )}
      </div>
      <div className="flex items-center justify-between p-3">
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="text-xs">Shot {index + 1}</Badge>
          <span className="text-xs text-muted-foreground">{durationS.toFixed(1)}s</span>
        </div>
        <div className="flex gap-1">
          {lastFrameUrl && onSetInitImage && (
            <Button variant="ghost" size="icon" className="h-7 w-7" title="设为初始图像" onClick={() => onSetInitImage(shotId, lastFrameUrl)}>
              <ImagePlus className="h-3.5 w-3.5" />
            </Button>
          )}
          {clipUrl && (
            <a href={`${clipUrl}/download`} download>
              <Button variant="ghost" size="icon" className="h-7 w-7" title="下载">
                <Download className="h-3.5 w-3.5" />
              </Button>
            </a>
          )}
        </div>
      </div>
    </Card>
  );
}
```

- [ ] **Step 4: Implement FinalVideoSection**

```tsx
// frontend/src/components/gallery/FinalVideoSection.tsx
import { VideoPlayer } from "./VideoPlayer";
import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";

interface FinalVideoSectionProps {
  videoUrl: string;
  durationS: number;
}

export function FinalVideoSection({ videoUrl, durationS }: FinalVideoSectionProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">最终合成视频</h2>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">{durationS.toFixed(1)}s</span>
          <a href={`${videoUrl}/download`} download>
            <Button variant="outline" size="sm"><Download className="mr-1.5 h-3.5 w-3.5" /> 下载</Button>
          </a>
        </div>
      </div>
      <VideoPlayer src={videoUrl} className="max-h-[640px]" />
    </div>
  );
}
```

- [ ] **Step 5: Implement GridView + TimelineView + ViewModeToggle**

```tsx
// frontend/src/components/gallery/GridView.tsx
import { ShotResultCard } from "./ShotResultCard";

interface GridViewProps {
  shots: Array<{
    shot_id: string;
    clip: string | null;
    last_frame: string | null;
    duration_s: number;
  }>;
  onSetInitImage?: (shotId: string, lastFrameUrl: string) => void;
}

export function GridView({ shots, onSetInitImage }: GridViewProps) {
  return (
    <div className="grid grid-cols-3 gap-4 max-[1280px]:grid-cols-2">
      {shots.map((shot, i) => (
        <ShotResultCard
          key={shot.shot_id}
          shotId={shot.shot_id}
          clipUrl={shot.clip}
          lastFrameUrl={shot.last_frame}
          durationS={shot.duration_s}
          index={i}
          onSetInitImage={onSetInitImage}
        />
      ))}
    </div>
  );
}
```

```tsx
// frontend/src/components/gallery/TimelineView.tsx
import { FrameThumbnail } from "./FrameThumbnail";
import { ArrowRight } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

interface TimelineViewProps {
  shots: Array<{ shot_id: string; last_frame: string | null; duration_s: number }>;
  onSelectShot?: (shotId: string) => void;
}

export function TimelineView({ shots, onSelectShot }: TimelineViewProps) {
  return (
    <div className="flex items-center gap-2 overflow-x-auto py-4 px-2">
      {shots.map((shot, i) => (
        <div key={shot.shot_id} className="flex items-center gap-2 shrink-0">
          <Tooltip>
            <TooltipTrigger asChild>
              <div
                className="cursor-pointer rounded-md border-2 border-transparent hover:border-primary transition-colors"
                onClick={() => onSelectShot?.(shot.shot_id)}
              >
                {shot.last_frame ? (
                  <FrameThumbnail src={shot.last_frame} size="md" clickable />
                ) : (
                  <div className="flex h-24 w-42 items-center justify-center rounded-md bg-muted text-xs text-muted-foreground">
                    无预览
                  </div>
                )}
              </div>
            </TooltipTrigger>
            <TooltipContent>
              Shot {i + 1} — {shot.duration_s.toFixed(1)}s
            </TooltipContent>
          </Tooltip>
          {i < shots.length - 1 && <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />}
        </div>
      ))}
    </div>
  );
}
```

```tsx
// frontend/src/components/gallery/ViewModeToggle.tsx
import { Button } from "@/components/ui/button";
import { LayoutGrid, Film } from "lucide-react";
import { cn } from "@/lib/utils";

export type ViewMode = "grid" | "timeline";

interface ViewModeToggleProps {
  mode: ViewMode;
  onChange: (mode: ViewMode) => void;
}

export function ViewModeToggle({ mode, onChange }: ViewModeToggleProps) {
  return (
    <div className="flex rounded-md border">
      <Button
        variant="ghost"
        size="icon"
        className={cn("h-8 w-8 rounded-r-none", mode === "grid" && "bg-accent")}
        onClick={() => onChange("grid")}
        title="网格视图"
      >
        <LayoutGrid className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        className={cn("h-8 w-8 rounded-l-none", mode === "timeline" && "bg-accent")}
        onClick={() => onChange("timeline")}
        title="时间线视图"
      >
        <Film className="h-4 w-4" />
      </Button>
    </div>
  );
}
```

- [ ] **Step 6: Implement GalleryLayout + GalleryPage**

```tsx
// frontend/src/components/gallery/GalleryLayout.tsx
import { useState } from "react";
import { FinalVideoSection } from "./FinalVideoSection";
import { GridView } from "./GridView";
import { TimelineView } from "./TimelineView";
import { ViewModeToggle, type ViewMode } from "./ViewModeToggle";
import { EmptyState } from "@/components/shared/EmptyState";
import { Video } from "lucide-react";
import type { GalleryIndex } from "@/hooks/use-gallery";

interface GalleryLayoutProps {
  gallery: GalleryIndex;
  onSetInitImage?: (shotId: string, lastFrameUrl: string) => void;
}

export function GalleryLayout({ gallery, onSetInitImage }: GalleryLayoutProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("grid");

  if (gallery.shots.length === 0 && !gallery.final_output) {
    return (
      <EmptyState
        icon={<Video className="h-12 w-12" />}
        title="尚无生成结果"
        description="完成第一次视频生成后，结果将在这里展示"
        actionLabel="开始第一次生成"
      />
    );
  }

  return (
    <div className="space-y-8">
      {gallery.final_output && (
        <FinalVideoSection videoUrl={gallery.final_output.video} durationS={gallery.final_output.duration_s} />
      )}
      {!gallery.final_output && (
        <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
          最终视频尚未合成（部分镜头未完成）
        </div>
      )}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">镜头产物</h2>
        <ViewModeToggle mode={viewMode} onChange={setViewMode} />
      </div>
      {viewMode === "grid" ? (
        <GridView shots={gallery.shots} onSetInitImage={onSetInitImage} />
      ) : (
        <TimelineView shots={gallery.shots} />
      )}
    </div>
  );
}
```

```tsx
// frontend/src/pages/GalleryPage.tsx
import { useParams } from "react-router-dom";
import { useGallery } from "@/hooks/use-gallery";
import { GalleryLayout } from "@/components/gallery/GalleryLayout";
import { Skeleton } from "@/components/ui/skeleton";

export default function GalleryPage() {
  const { runId } = useParams<{ runId: string }>();
  const { data: gallery, isLoading, error } = useGallery(runId ?? "");

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-6 space-y-6">
        <Skeleton className="h-[360px] w-full rounded-lg" />
        <div className="grid grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="aspect-video rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (error || !gallery) {
    return <div className="p-8 text-center text-destructive">加载画廊失败</div>;
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-6">
      <h1 className="mb-6 text-xl font-semibold">生成结果</h1>
      <GalleryLayout gallery={gallery} />
    </div>
  );
}
```

- [ ] **Step 7: Verify TypeScript compilation**

```bash
cd /home/reggie/vscode_folder/AI-VIDEO/frontend && npx tsc --noEmit
```

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/gallery/ frontend/src/pages/GalleryPage.tsx
git commit -m "feat(frontend): F-005 result gallery — VideoPlayer, Grid/Timeline views, FinalVideo section, FrameThumbnail"
```

---

### Task 3: F-006 Run History — Run Cards, Filters, Config Drift, Detail Drawer

**Files:**
- Create: `frontend/src/components/history/MiniShotStatus.tsx`
- Create: `frontend/src/components/history/RunCard.tsx`
- Create: `frontend/src/components/history/RunDetailDrawer.tsx`
- Create: `frontend/src/components/history/ConfigDriftWarning.tsx`
- Create: `frontend/src/components/history/HistoryFilters.tsx`
- Create: `frontend/src/components/history/LoadMoreButton.tsx`
- Create: `frontend/src/pages/HistoryPage.tsx`

- [ ] **Step 1: Implement MiniShotStatus**

```tsx
// frontend/src/components/history/MiniShotStatus.tsx
import { cn } from "@/lib/utils";

type DotStatus = "completed" | "running" | "failed" | "pending";

interface MiniShotStatusProps {
  shots: Array<{ status: string }>;
}

function mapToDot(status: string): DotStatus {
  if (status === "succeeded" || status === "completed") return "completed";
  if (status === "running") return "running";
  if (status === "failed") return "failed";
  return "pending";
}

const DOT_COLORS: Record<DotStatus, string> = {
  completed: "bg-green-500",
  running: "bg-blue-500 animate-pulse",
  failed: "bg-red-500",
  pending: "bg-gray-300",
};

export function MiniShotStatus({ shots }: MiniShotStatusProps) {
  return (
    <div className="flex gap-1" aria-label="镜头状态">
      {shots.map((shot, i) => (
        <div
          key={i}
          className={cn("h-2.5 w-2.5 rounded-full", DOT_COLORS[mapToDot(shot.status)])}
          title={`Shot ${i + 1}: ${shot.status}`}
        />
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Implement RunCard**

```tsx
// frontend/src/components/history/RunCard.tsx
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Eye, RotateCcw, Trash2, Settings2, Play } from "lucide-react";
import { cn } from "@/lib/utils";
import { MiniShotStatus } from "./MiniShotStatus";
import { formatRelativeTime, formatDuration } from "@/lib/time-format";
import type { RunSummary, RunDetail } from "@/types/run";

export type AggregateStatus = "completed" | "partial" | "failed" | "running";

const STATUS_STYLES: Record<AggregateStatus, { border: string; badge: string; label: string }> = {
  completed: { border: "border-l-green-500", badge: "bg-green-100 text-green-700", label: "已完成" },
  partial: { border: "border-l-yellow-500", badge: "bg-yellow-100 text-yellow-700", label: "部分完成" },
  failed: { border: "border-l-red-500", badge: "bg-red-100 text-red-700", label: "失败" },
  running: { border: "border-l-blue-500", badge: "bg-blue-100 text-blue-700", label: "进行中" },
};

export function computeAggregate(run: RunDetail | RunSummary): AggregateStatus {
  if ("shots" in run && Array.isArray(run.shots)) {
    const detail = run as RunDetail;
    const completed = detail.shots.filter((s) => s.status === "succeeded").length;
    const failed = detail.shots.filter((s) => s.status === "failed").length;
    const running = detail.shots.filter((s) => s.status === "running").length;
    if (running > 0) return "running";
    if (failed === 0) return "completed";
    if (completed > 0) return "partial";
    return "failed";
  }
  if (run.status === "running") return "running";
  if (run.status === "succeeded") return "completed";
  if (run.status === "failed") return "failed";
  return "failed";
}

interface RunCardProps {
  run: RunSummary;
  shots?: Array<{ status: string }>;
  onViewResults: (runId: string) => void;
  onRestoreParams: (runId: string) => void;
  onRerun: (runId: string) => void;
  onDelete: (runId: string) => void;
  onViewMonitor?: (runId: string) => void;
}

export function RunCard({ run, shots, onViewResults, onRestoreParams, onRerun, onDelete, onViewMonitor }: RunCardProps) {
  const aggregate = computeAggregate(run);
  const style = STATUS_STYLES[aggregate];

  return (
    <Card className={cn("border-l-4", style.border)}>
      <div className="flex items-start justify-between p-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">{run.project_name || "未知项目"}</span>
            <Badge className={cn("text-xs", style.badge)}>{style.label}</Badge>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">{formatRelativeTime(run.created_at)}</p>
          {shots && <MiniShotStatus shots={shots} className="mt-2" />}
        </div>
        <div className="flex gap-1">
          {aggregate === "running" && onViewMonitor && (
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => onViewMonitor(run.run_id)} title="查看进度">
              <Play className="h-4 w-4" />
            </Button>
          )}
          {aggregate !== "running" && (
            <>
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => onViewResults(run.run_id)} title="查看结果">
                <Eye className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => onRestoreParams(run.run_id)} title="恢复参数">
                <Settings2 className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => onRerun(run.run_id)} title="重新运行">
                <RotateCcw className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => onDelete(run.run_id)} title="删除">
                <Trash2 className="h-4 w-4" />
              </Button>
            </>
          )}
        </div>
      </div>
    </Card>
  );
}
```

- [ ] **Step 3: Implement ConfigDriftWarning**

```tsx
// frontend/src/components/history/ConfigDriftWarning.tsx
import { AlertTriangle } from "lucide-react";
import type { ConfigDriftResult } from "@/hooks/use-run-history";

interface ConfigDriftWarningProps {
  drift: ConfigDriftResult;
}

export function ConfigDriftWarning({ drift }: ConfigDriftWarningProps) {
  if (!drift.drifted) return null;

  return (
    <div className="flex items-start gap-3 rounded-lg border border-yellow-200 bg-yellow-50 p-3">
      <AlertTriangle className="h-5 w-5 text-yellow-600 shrink-0 mt-0.5" />
      <div>
        <p className="text-sm font-medium text-yellow-800">配置已变更</p>
        <p className="mt-1 text-xs text-yellow-600">
          当前项目配置与此次运行时的配置不同，恢复参数可能产生不同结果
        </p>
        <ul className="mt-2 space-y-1">
          {drift.changes.map((c, i) => (
            <li key={i} className="text-xs text-yellow-700">
              {c.field}: hash 已变更
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Implement HistoryFilters + LoadMoreButton**

```tsx
// frontend/src/components/history/HistoryFilters.tsx
import { cn } from "@/lib/utils";

type FilterStatus = "all" | "completed" | "partial" | "failed";

interface HistoryFiltersProps {
  current: FilterStatus;
  onChange: (status: FilterStatus) => void;
}

const FILTERS: Array<{ value: FilterStatus; label: string }> = [
  { value: "all", label: "全部" },
  { value: "completed", label: "已完成" },
  { value: "partial", label: "部分完成" },
  { value: "failed", label: "失败" },
];

export function HistoryFilters({ current, onChange }: HistoryFiltersProps) {
  return (
    <div className="flex gap-1 rounded-lg border p-1">
      {FILTERS.map((f) => (
        <button
          key={f.value}
          onClick={() => onChange(f.value)}
          className={cn(
            "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
            current === f.value ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted"
          )}
        >
          {f.label}
        </button>
      ))}
    </div>
  );
}
```

```tsx
// frontend/src/components/history/LoadMoreButton.tsx
import { Button } from "@/components/ui/button";

interface LoadMoreButtonProps {
  showing: number;
  total: number;
  loading: boolean;
  onLoadMore: () => void;
}

export function LoadMoreButton({ showing, total, loading, onLoadMore }: LoadMoreButtonProps) {
  if (showing >= total) return null;

  return (
    <div className="flex flex-col items-center gap-2 py-4">
      <p className="text-sm text-muted-foreground">
        显示 {showing} / {total} 条记录
      </p>
      <Button variant="outline" onClick={onLoadMore} disabled={loading}>
        {loading ? "加载中..." : "加载更多"}
      </Button>
    </div>
  );
}
```

- [ ] **Step 5: Implement RunDetailDrawer**

```tsx
// frontend/src/components/history/RunDetailDrawer.tsx
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { ConfigDriftWarning } from "./ConfigDriftWarning";
import { useRunDetail, useConfigDrift } from "@/hooks/use-run-history";
import { formatFullTimestamp, formatDuration } from "@/lib/time-format";
import { Skeleton } from "@/components/ui/skeleton";

interface RunDetailDrawerProps {
  runId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function RunDetailDrawer({ runId, open, onOpenChange }: RunDetailDrawerProps) {
  const { data: run, isLoading } = useRunDetail(runId ?? "");
  const { data: drift } = useConfigDrift(runId ?? "", open && !!runId);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-[480px] sm:w-[540px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>运行详情</SheetTitle>
        </SheetHeader>
        {isLoading ? (
          <div className="mt-4 space-y-3">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-32 w-full" />
          </div>
        ) : run ? (
          <div className="mt-4 space-y-4 text-sm">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="font-medium">Run ID:</span>
                <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{run.run_id}</code>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-medium">状态:</span>
                <StatusBadge status={run.status} size="sm" />
              </div>
              <p>创建时间: {formatFullTimestamp(run.created_at)}</p>
              {run.total_duration_s != null && <p>总耗时: {formatDuration(run.total_duration_s)}</p>}
            </div>

            {drift && <ConfigDriftWarning drift={drift} />}

            <div>
              <h4 className="font-medium mb-2">镜头状态</h4>
              <div className="space-y-1">
                {run.shots.map((shot, i) => (
                  <div key={shot.shot_id} className="flex items-center justify-between rounded-md px-2 py-1.5 hover:bg-muted">
                    <span>Shot {i + 1}</span>
                    <StatusBadge status={shot.status} size="sm" />
                  </div>
                ))}
              </div>
            </div>

            <details className="rounded-md border">
              <summary className="cursor-pointer px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-muted">
                查看原始数据
              </summary>
              <pre className="max-h-64 overflow-auto bg-muted p-3 text-xs">{JSON.stringify(run, null, 2)}</pre>
            </details>
          </div>
        ) : (
          <p className="mt-4 text-sm text-muted-foreground">未找到运行记录</p>
        )}
      </SheetContent>
    </Sheet>
  );
}
```

- [ ] **Step 6: Implement HistoryPage**

```tsx
// frontend/src/pages/HistoryPage.tsx
import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useRunHistory, useDeleteRun } from "@/hooks/use-run-history";
import { RunCard } from "@/components/history/RunCard";
import { HistoryFilters, type FilterStatus } from "@/components/history/HistoryFilters";
import { LoadMoreButton } from "@/components/history/LoadMoreButton";
import { RunDetailDrawer } from "@/components/history/RunDetailDrawer";
import { EmptyState } from "@/components/shared/EmptyState";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Clock } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

export default function HistoryPage() {
  const [filter, setFilter] = useState<FilterStatus>("all");
  const [offset, setOffset] = useState(0);
  const [detailRunId, setDetailRunId] = useState<string | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const navigate = useNavigate();
  const deleteRun = useDeleteRun();

  const limit = 20;
  const statusParam = filter === "all" ? undefined : filter;

  const { data, isLoading } = useRunHistory({ status: statusParam, offset, limit });
  const runs = data?.data ?? [];
  const total = data?.meta.total ?? 0;

  function handleViewResults(runId: string) {
    navigate(`/results/${runId}`);
  }

  function handleRestoreParams(runId: string) {
    navigate(`/tuner?run=${runId}&scope=default`);
  }

  function handleRerun(runId: string) {
    navigate(`/tuner?run=${runId}&scope=current`);
  }

  function handleViewMonitor(runId: string) {
    navigate(`/runs/${runId}/monitor`);
  }

  function handleDeleteConfirm() {
    if (!deleteTarget) return;
    deleteRun.mutate(deleteTarget, { onSettled: () => setDeleteTarget(null) });
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">运行历史</h1>
        <HistoryFilters current={filter} onChange={(f) => { setFilter(f); setOffset(0); }} />
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full rounded-lg" />
          ))}
        </div>
      ) : runs.length === 0 ? (
        <EmptyState
          icon={<Clock className="h-12 w-12" />}
          title="还没有运行记录"
          description="创建第一个视频后，运行记录将在这里展示"
          actionLabel="创建项目"
          onAction={() => navigate("/wizard")}
        />
      ) : (
        <div className="space-y-3">
          {runs.map((run) => (
            <RunCard
              key={run.run_id}
              run={run}
              onViewResults={handleViewResults}
              onRestoreParams={handleRestoreParams}
              onRerun={handleRerun}
              onDelete={setDeleteTarget}
              onViewMonitor={handleViewMonitor}
            />
          ))}
        </div>
      )}

      <LoadMoreButton
        showing={runs.length}
        total={total}
        loading={isLoading}
        onLoadMore={() => setOffset((prev) => prev + limit)}
      />

      <RunDetailDrawer
        runId={detailRunId}
        open={detailOpen}
        onOpenChange={setDetailOpen}
      />

      <Dialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>确定要删除此运行记录吗？此操作不可撤销。</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>取消</Button>
            <Button variant="destructive" onClick={handleDeleteConfirm}>删除</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
```

- [ ] **Step 7: Verify TypeScript compilation**

```bash
cd /home/reggie/vscode_folder/AI-VIDEO/frontend && npx tsc --noEmit
```

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/history/ frontend/src/pages/HistoryPage.tsx
git commit -m "feat(frontend): F-006 run history — run cards, aggregate status, config drift, filters, Load More pagination"
```

---

### Task 4: F-007 Parameter Tuner — Dual-Panel, Seed Control, JSON Preview, Rerun

**Files:**
- Create: `frontend/src/components/tuner/SeedControl.tsx`
- Create: `frontend/src/components/tuner/OverrideIndicator.tsx`
- Create: `frontend/src/components/tuner/ScopeSelector.tsx`
- Create: `frontend/src/components/tuner/ParameterPanel.tsx`
- Create: `frontend/src/components/tuner/JsonPreview.tsx`
- Create: `frontend/src/components/tuner/VisualPreview.tsx`
- Create: `frontend/src/components/tuner/PreviewPanel.tsx`
- Create: `frontend/src/components/tuner/ChangeSummary.tsx`
- Create: `frontend/src/components/tuner/ConflictDialog.tsx`
- Create: `frontend/src/components/tuner/TunerLayout.tsx`
- Create: `frontend/src/pages/TunerPage.tsx`

- [ ] **Step 1: Implement SeedControl**

```tsx
// frontend/src/components/tuner/SeedControl.tsx
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Shuffle, Lock, Unlock, Plus } from "lucide-react";
import { useState } from "react";

interface SeedControlProps {
  value: number | null;
  defaultValue: number;
  onChange: (value: number | null) => void;
}

export function SeedControl({ value, defaultValue, onChange }: SeedControlProps) {
  const [locked, setLocked] = useState(value !== null);

  function randomize() {
    onChange(Math.floor(Math.random() * 2 ** 32));
    setLocked(true);
  }

  function toggleLock() {
    if (locked) {
      onChange(null);
      setLocked(false);
    } else {
      onChange(value ?? defaultValue);
      setLocked(true);
    }
  }

  function increment() {
    onChange((value ?? defaultValue) + 1);
    setLocked(true);
  }

  return (
    <div className="flex items-center gap-1.5">
      <Input
        type="number"
        value={value ?? ""}
        onChange={(e) => {
          const v = e.target.value ? Number(e.target.value) : null;
          onChange(v);
          setLocked(v !== null);
        }}
        placeholder={`默认: ${defaultValue}`}
        className="flex-1"
      />
      <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0" onClick={randomize} title="随机种子">
        <Shuffle className="h-4 w-4" />
      </Button>
      <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0" onClick={toggleLock} title={locked ? "解锁 (使用随机)" : "锁定种子"}>
        {locked ? <Lock className="h-4 w-4 text-primary" /> : <Unlock className="h-4 w-4" />}
      </Button>
      <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0" onClick={increment} title="递增 +1">
        <Plus className="h-4 w-4" />
      </Button>
    </div>
  );
}
```

- [ ] **Step 2: Implement OverrideIndicator**

```tsx
// frontend/src/components/tuner/OverrideIndicator.tsx
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RotateCcw } from "lucide-react";

interface OverrideIndicatorProps {
  isCustom: boolean;
  onReset: () => void;
}

export function OverrideIndicator({ isCustom, onReset }: OverrideIndicatorProps) {
  if (!isCustom) return null;

  return (
    <div className="flex items-center gap-1.5">
      <Badge variant="secondary" className="text-xs bg-accent/10 text-accent">Custom</Badge>
      <Button variant="ghost" size="sm" className="h-6 px-2 text-xs" onClick={onReset}>
        <RotateCcw className="mr-1 h-3 w-3" /> 重置
      </Button>
    </div>
  );
}
```

- [ ] **Step 3: Implement ScopeSelector**

```tsx
// frontend/src/components/tuner/ScopeSelector.tsx
import { cn } from "@/lib/utils";

export type ParamScope = "current" | "all" | "default";

interface ScopeSelectorProps {
  scope: ParamScope;
  onChange: (scope: ParamScope) => void;
}

const SCOPES: Array<{ value: ParamScope; label: string; desc: string }> = [
  { value: "current", label: "当前镜头", desc: "仅修改当前选中的镜头" },
  { value: "all", label: "全部镜头", desc: "批量修改所有镜头的共有参数" },
  { value: "default", label: "项目默认", desc: "修改项目默认参数" },
];

export function ScopeSelector({ scope, onChange }: ScopeSelectorProps) {
  return (
    <div className="flex gap-1 rounded-lg border p-1">
      {SCOPES.map((s) => (
        <button
          key={s.value}
          onClick={() => onChange(s.value)}
          title={s.desc}
          className={cn(
            "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
            scope === s.value ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted"
          )}
        >
          {s.label}
        </button>
      ))}
    </div>
  );
}
```

- [ ] **Step 4: Implement ParameterPanel**

```tsx
// frontend/src/components/tuner/ParameterPanel.tsx
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ChevronDown } from "lucide-react";
import { ParameterField } from "@/components/shared/ParameterField";
import { SeedControl } from "./SeedControl";
import { OverrideIndicator } from "./OverrideIndicator";
import { useState } from "react";
import type { ShotWithEffective } from "@/types/shot";
import type { DefaultsConfig } from "@/types/project";
import type { ParamScope } from "./ScopeSelector";

interface ParameterPanelProps {
  scope: ParamScope;
  shot: ShotWithEffective | null;
  defaults: DefaultsConfig | null;
  availableCharacters: string[];
  onChange: (field: string, value: unknown) => void;
}

export function ParameterPanel({ scope, shot, defaults, availableCharacters, onChange }: ParameterPanelProps) {
  const [advancedOpen, setAdvancedOpen] = useState(false);

  if (scope === "default" && defaults) {
    return <DefaultsPanel defaults={defaults} onChange={onChange} />;
  }

  if (!shot) {
    return <p className="text-sm text-muted-foreground">请选择一个镜头进行编辑</p>;
  }

  return (
    <div className="space-y-4">
      <ParameterField label="提示词" required tooltip="描述此镜头的内容">
        <Textarea
          value={shot.prompt}
          onChange={(e) => onChange("prompt", e.target.value)}
          minRows={2} maxRows={6} className="text-base"
        />
      </ParameterField>
      <ParameterField label="负面提示词" tooltip="描述不希望出现的内容">
        <Textarea
          value={shot.negative_prompt}
          onChange={(e) => onChange("negative_prompt", e.target.value)}
          minRows={1} maxRows={3}
        />
      </ParameterField>
      <div className="grid grid-cols-2 gap-3">
        <ParameterField label="时长 (秒)" tooltip="留空使用项目默认值">
          <div className="flex items-center gap-2">
            <Input type="number" value={shot.clip_seconds ?? ""} onChange={(e) => onChange("clip_seconds", e.target.value ? Number(e.target.value) : null)} placeholder={`默认: ${shot.effective_clip_seconds}`} />
            <OverrideIndicator isCustom={shot.overrides.includes("clip_seconds")} onReset={() => onChange("clip_seconds", null)} />
          </div>
        </ParameterField>
        <ParameterField label="帧率" tooltip="留空使用项目默认值">
          <div className="flex items-center gap-2">
            <Input type="number" value={shot.fps ?? ""} onChange={(e) => onChange("fps", e.target.value ? Number(e.target.value) : null)} placeholder={`默认: ${shot.effective_fps}`} />
            <OverrideIndicator isCustom={shot.overrides.includes("fps")} onReset={() => onChange("fps", null)} />
          </div>
        </ParameterField>
      </div>
      <ParameterField label="种子" tooltip="相同种子产生相同结果">
        <SeedControl value={shot.seed} defaultValue={shot.effective_seed} onChange={(v) => onChange("seed", v)} />
      </ParameterField>

      <Collapsible open={advancedOpen} onOpenChange={setAdvancedOpen}>
        <CollapsibleTrigger className="flex w-full items-center justify-between rounded-md px-3 py-2 text-sm font-medium hover:bg-muted">
          <span>高级参数</span>
          <ChevronDown className={`h-4 w-4 transition-transform ${advancedOpen ? "rotate-180" : ""}`} />
        </CollapsibleTrigger>
        <CollapsibleContent className="mt-3 space-y-3 pl-1">
          <ParameterField label="初始图像" tooltip="作为生成起点的图像路径" tier="expert">
            <Input value={shot.init_image ?? ""} onChange={(e) => onChange("init_image", e.target.value || null)} placeholder="无" />
          </ParameterField>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}

function DefaultsPanel({ defaults, onChange }: { defaults: DefaultsConfig; onChange: (field: string, value: unknown) => void }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <ParameterField label="宽度">
          <Input type="number" value={defaults.width} onChange={(e) => onChange("width", Number(e.target.value))} />
        </ParameterField>
        <ParameterField label="高度">
          <Input type="number" value={defaults.height} onChange={(e) => onChange("height", Number(e.target.value))} />
        </ParameterField>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <ParameterField label="帧率">
          <Input type="number" value={defaults.fps} onChange={(e) => onChange("fps", Number(e.target.value))} />
        </ParameterField>
        <ParameterField label="时长 (秒)">
          <Input type="number" value={defaults.clip_seconds} onChange={(e) => onChange("clip_seconds", Number(e.target.value))} />
        </ParameterField>
      </div>
      <ParameterField label="种子">
        <SeedControl value={defaults.seed} defaultValue={0} onChange={(v) => onChange("seed", v)} />
      </ParameterField>
      <ParameterField label="负面提示词">
        <Textarea value={defaults.negative_prompt} onChange={(e) => onChange("negative_prompt", e.target.value)} minRows={1} maxRows={3} />
      </ParameterField>
      <ParameterField label="风格提示词">
        <Input value={defaults.style_prompt} onChange={(e) => onChange("style_prompt", e.target.value)} />
      </ParameterField>
    </div>
  );
}
```

- [ ] **Step 5: Implement JsonPreview + VisualPreview + PreviewPanel**

```tsx
// frontend/src/components/tuner/JsonPreview.tsx
import { cn } from "@/lib/utils";

interface JsonPreviewProps {
  json: Record<string, unknown> | null;
  diffPaths?: string[];
  loading?: boolean;
}

export function JsonPreview({ json, diffPaths = [], loading }: JsonPreviewProps) {
  if (loading) {
    return <div className="animate-pulse space-y-2 p-4"><div className="h-4 w-3/4 bg-muted rounded" /><div className="h-4 w-1/2 bg-muted rounded" /></div>;
  }

  if (!json) {
    return <p className="p-4 text-sm text-muted-foreground">修改参数后将显示 Workflow JSON 预览</p>;
  }

  const text = JSON.stringify(json, null, 2);

  return (
    <pre className="max-h-[600px] overflow-auto rounded-md bg-muted p-4 text-xs font-mono">
      {text.split("\n").map((line, i) => {
        const isDiff = diffPaths.some((p) => line.includes(`"${p}"`));
        return (
          <div key={i} className={cn(isDiff && "bg-yellow-100 dark:bg-yellow-900/30 -mx-4 px-4")}>
            {line}
          </div>
        );
      })}
    </pre>
  );
}
```

```tsx
// frontend/src/components/tuner/VisualPreview.tsx
import { FrameThumbnail } from "@/components/gallery/FrameThumbnail";

interface VisualPreviewProps {
  lastFrameUrl?: string | null;
  initImageUrl?: string | null;
  characterRefs?: Array<{ id: string; url: string }>;
}

export function VisualPreview({ lastFrameUrl, initImageUrl, characterRefs }: VisualPreviewProps) {
  return (
    <div className="space-y-4 p-4">
      {lastFrameUrl && (
        <div>
          <p className="mb-2 text-sm font-medium text-muted-foreground">前一镜头末帧</p>
          <FrameThumbnail src={lastFrameUrl} size="lg" />
        </div>
      )}
      {initImageUrl && (
        <div>
          <p className="mb-2 text-sm font-medium text-muted-foreground">初始图像</p>
          <FrameThumbnail src={initImageUrl} size="md" />
        </div>
      )}
      {characterRefs && characterRefs.length > 0 && (
        <div>
          <p className="mb-2 text-sm font-medium text-muted-foreground">角色参考图</p>
          <div className="flex gap-2">
            {characterRefs.map((ref) => (
              <div key={ref.id} className="text-center">
                <FrameThumbnail src={ref.url} size="sm" />
                <p className="mt-1 text-xs text-muted-foreground">{ref.id}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      {!lastFrameUrl && !initImageUrl && (!characterRefs || characterRefs.length === 0) && (
        <p className="text-sm text-muted-foreground">无可视化预览数据</p>
      )}
    </div>
  );
}
```

```tsx
// frontend/src/components/tuner/PreviewPanel.tsx
import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { JsonPreview } from "./JsonPreview";
import { VisualPreview } from "./VisualPreview";

type PreviewMode = "json" | "visual";

interface PreviewPanelProps {
  workflowJson: Record<string, unknown> | null;
  diffPaths: string[];
  lastFrameUrl?: string | null;
  initImageUrl?: string | null;
  characterRefs?: Array<{ id: string; url: string }>;
  loading?: boolean;
}

export function PreviewPanel({ workflowJson, diffPaths, lastFrameUrl, initImageUrl, characterRefs, loading }: PreviewPanelProps) {
  const [mode, setMode] = useState<PreviewMode>("json");

  return (
    <div className="sticky top-0">
      <Tabs value={mode} onValueChange={(v) => setMode(v as PreviewMode)}>
        <TabsList className="mb-2">
          <TabsTrigger value="json">JSON</TabsTrigger>
          <TabsTrigger value="visual">Visual</TabsTrigger>
        </TabsList>
        <TabsContent value="json">
          <JsonPreview json={workflowJson} diffPaths={diffPaths} loading={loading} />
        </TabsContent>
        <TabsContent value="visual">
          <VisualPreview lastFrameUrl={lastFrameUrl} initImageUrl={initImageUrl} characterRefs={characterRefs} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

- [ ] **Step 6: Implement ChangeSummary + ConflictDialog**

```tsx
// frontend/src/components/tuner/ChangeSummary.tsx
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface Change {
  field: string;
  oldValue: unknown;
  newValue: unknown;
}

interface ChangeSummaryProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  changes: Change[];
  onConfirm: () => void;
}

export function ChangeSummary({ open, onOpenChange, changes, onConfirm }: ChangeSummaryProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>确认参数变更</DialogTitle>
          <DialogDescription>
            将创建新的运行，以下参数与上次不同：
          </DialogDescription>
        </DialogHeader>
        {changes.length === 0 ? (
          <p className="py-4 text-sm text-muted-foreground">无参数变更</p>
        ) : (
          <ul className="space-y-1.5 py-2 text-sm">
            {changes.map((c, i) => (
              <li key={i} className="flex items-center gap-2">
                <span className="font-medium">{c.field}:</span>
                <span className="text-muted-foreground">{String(c.oldValue)}</span>
                <span className="text-muted-foreground">→</span>
                <span className="font-medium text-primary">{String(c.newValue)}</span>
              </li>
            ))}
          </ul>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>取消</Button>
          <Button onClick={onConfirm}>确认并重新生成</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

```tsx
// frontend/src/components/tuner/ConflictDialog.tsx
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface ConflictDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onViewProgress: () => void;
  activeRunId?: string;
}

export function ConflictDialog({ open, onOpenChange, onViewProgress, activeRunId }: ConflictDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>已有运行中的任务</DialogTitle>
          <DialogDescription>
            当前有生成任务正在执行（Run: {activeRunId ?? "..."}），请等待完成或取消后再试。
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>关闭</Button>
          <Button onClick={() => { onOpenChange(false); onViewProgress(); }}>查看进度</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

- [ ] **Step 7: Implement TunerLayout + TunerPage**

```tsx
// frontend/src/components/tuner/TunerLayout.tsx
import { ParameterPanel } from "./ParameterPanel";
import { PreviewPanel } from "./PreviewPanel";
import { ScopeSelector, type ParamScope } from "./ScopeSelector";
import type { ShotWithEffective } from "@/types/shot";
import type { DefaultsConfig } from "@/types/project";

interface TunerLayoutProps {
  scope: ParamScope;
  onScopeChange: (scope: ParamScope) => void;
  shot: ShotWithEffective | null;
  defaults: DefaultsConfig | null;
  availableCharacters: string[];
  onChange: (field: string, value: unknown) => void;
  workflowJson: Record<string, unknown> | null;
  diffPaths: string[];
  lastFrameUrl?: string | null;
  initImageUrl?: string | null;
  changeCount: number;
  previewLoading?: boolean;
}

export function TunerLayout({
  scope, onScopeChange, shot, defaults, availableCharacters,
  onChange, workflowJson, diffPaths, lastFrameUrl, initImageUrl,
  changeCount, previewLoading,
}: TunerLayoutProps) {
  return (
    <div className="flex h-[calc(100vh-4rem)] gap-4">
      {/* Left: Parameters (40%) */}
      <div className="w-[40%] overflow-y-auto border-r pr-4">
        <div className="mb-4">
          <ScopeSelector scope={scope} onChange={onScopeChange} />
        </div>
        <ParameterPanel
          scope={scope}
          shot={shot}
          defaults={defaults}
          availableCharacters={availableCharacters}
          onChange={onChange}
        />
        <div className="sticky bottom-0 border-t bg-background py-3 text-center text-sm text-muted-foreground">
          已修改 {changeCount} 项参数
        </div>
      </div>

      {/* Right: Preview (60%) */}
      <div className="w-[60%] overflow-y-auto">
        <PreviewPanel
          workflowJson={workflowJson}
          diffPaths={diffPaths}
          lastFrameUrl={lastFrameUrl}
          initImageUrl={initImageUrl}
          loading={previewLoading}
        />
      </div>
    </div>
  );
}
```

```tsx
// frontend/src/pages/TunerPage.tsx
import { useState, useCallback, useMemo } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useProject } from "@/hooks/use-projects";
import { useShots, useUpdateShot } from "@/hooks/use-shots";
import { useRerun } from "@/hooks/use-run-history";
import { useRun } from "@/hooks/use-runs";
import { TunerLayout } from "@/components/tuner/TunerLayout";
import { ChangeSummary } from "@/components/tuner/ChangeSummary";
import { ConflictDialog } from "@/components/tuner/ConflictDialog";
import { Button } from "@/components/ui/button";
import { Play, ArrowLeft } from "lucide-react";
import type { ParamScope } from "@/components/tuner/ScopeSelector";
import type { ShotWithEffective } from "@/types/shot";
import { ApiError } from "@/lib/api-client";

export default function TunerPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const sourceRunId = searchParams.get("run") ?? "";
  const initialScope = (searchParams.get("scope") as ParamScope) ?? "current";
  const initialShotId = searchParams.get("shot") ?? "";

  const [scope, setScope] = useState<ParamScope>(initialScope);
  const [selectedShotId, setSelectedShotId] = useState(initialShotId);
  const [changeSummaryOpen, setChangeSummaryOpen] = useState(false);
  const [conflictOpen, setConflictOpen] = useState(false);
  const [localChanges, setLocalChanges] = useState<Record<string, unknown>>({});

  const { data: run } = useRun(sourceRunId);
  const projectName = run?.project_name ?? "";
  const { data: project } = useProject(projectName);
  const { data: shots = [] } = useShots(projectName);
  const updateShot = useUpdateShot(projectName);
  const rerun = useRerun();

  const currentShot = useMemo(() => {
    if (!selectedShotId && shots.length > 0) return shots[0];
    return shots.find((s) => s.id === selectedShotId) ?? shots[0] ?? null;
  }, [shots, selectedShotId]);

  const changeCount = Object.keys(localChanges).length;

  const handleChange = useCallback((field: string, value: unknown) => {
    setLocalChanges((prev) => ({ ...prev, [field]: value }));
    if (currentShot && scope !== "default") {
      updateShot.mutate({ shotId: currentShot.id, data: { [field]: value } });
    }
  }, [currentShot, scope, updateShot]);

  const changes = useMemo(() => {
    return Object.entries(localChanges).map(([field, newValue]) => {
      const oldValue = currentShot
        ? (currentShot as unknown as Record<string, unknown>)[field] ?? "default"
        : "default";
      return { field, oldValue, newValue };
    });
  }, [localChanges, currentShot]);

  async function handleRerun() {
    try {
      const result = await rerun.mutateAsync({
        source_run_id: sourceRunId,
        overrides: localChanges,
      });
      navigate(`/runs/${result.run_id}/monitor`);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setConflictOpen(true);
      }
    }
  }

  function handleConflictViewProgress() {
    navigate(`/runs/${sourceRunId}/monitor`);
  }

  return (
    <div className="mx-auto max-w-7xl px-6 py-4">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <h1 className="text-lg font-semibold">参数调优</h1>
          {sourceRunId && <span className="text-sm text-muted-foreground">基于 Run: {sourceRunId.slice(0, 12)}...</span>}
        </div>
        <Button onClick={() => setChangeSummaryOpen(true)} disabled={changeCount === 0 && !sourceRunId}>
          <Play className="mr-2 h-4 w-4" /> 重新生成
        </Button>
      </div>

      <TunerLayout
        scope={scope}
        onScopeChange={setScope}
        shot={currentShot}
        defaults={project?.defaults ?? null}
        availableCharacters={[]}
        onChange={handleChange}
        workflowJson={null}
        diffPaths={[]}
        lastFrameUrl={null}
        initImageUrl={null}
        changeCount={changeCount}
      />

      <ChangeSummary
        open={changeSummaryOpen}
        onOpenChange={setChangeSummaryOpen}
        changes={changes}
        onConfirm={handleRerun}
      />

      <ConflictDialog
        open={conflictOpen}
        onOpenChange={setConflictOpen}
        onViewProgress={handleConflictViewProgress}
        activeRunId={sourceRunId}
      />
    </div>
  );
}
```

- [ ] **Step 8: Verify TypeScript compilation**

```bash
cd /home/reggie/vscode_folder/AI-VIDEO/frontend && npx tsc --noEmit
```

- [ ] **Step 9: Commit**

```bash
git add frontend/src/components/tuner/ frontend/src/pages/TunerPage.tsx
git commit -m "feat(frontend): F-007 param tuner — dual-panel, seed control, JSON preview, override indicators, rerun with conflict handling"
```

---

### Task 5: Wire All Routes + Final Integration Verification

**Files:**
- Modify: `frontend/src/App.tsx` (import real page components for F-005/006/007)
- Verify: all routes load without errors

- [ ] **Step 1: Update App.tsx with all real pages**

```tsx
// frontend/src/App.tsx — final version with all pages
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { TooltipProvider } from "@/components/ui/tooltip";
import WizardPage from "@/pages/WizardPage";
import EditorPage from "@/pages/EditorPage";
import MonitorPage from "@/pages/MonitorPage";
import GalleryPage from "@/pages/GalleryPage";
import HistoryPage from "@/pages/HistoryPage";
import TunerPage from "@/pages/TunerPage";

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
            <Route path="/results/:runId" element={<GalleryPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/tuner" element={<TunerPage />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
}
```

- [ ] **Step 2: Run full TypeScript check**

```bash
cd /home/reggie/vscode_folder/AI-VIDEO/frontend && npx tsc --noEmit
```

Expected: No errors

- [ ] **Step 3: Verify dev server renders all routes**

```bash
cd /home/reggie/vscode_folder/AI-VIDEO/frontend && npm run dev
```

Manually verify each route loads:
- `/wizard` — 4-step wizard
- `/projects/test/editor` — shot card editor
- `/runs/test/monitor` — pipeline node view
- `/results/test` — gallery page
- `/history` — run history
- `/tuner` — parameter tuner

- [ ] **Step 4: Run production build to verify no issues**

```bash
cd /home/reggie/vscode_folder/AI-VIDEO/frontend && npm run build
```

Expected: Build succeeds

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat(frontend): wire all 7 feature routes — wizard, editor, monitor, gallery, history, tuner"
```

---

## Self-Review

### 1. Spec Coverage Check

| F-005 Requirement | Task |
|---|---|
| Final video prominently displayed | Task 2 (FinalVideoSection) |
| Native HTML5 player with enhanced prop | Task 2 (VideoPlayer) |
| poster attribute from last_frame.png | Task 2 (ShotResultCard) |
| Grid View (3-col) + Timeline View | Task 2 (GridView + TimelineView) |
| ViewMode toggle | Task 2 (ViewModeToggle) |
| Video download (Content-Disposition) | Task 2 (download link on ShotResultCard) |
| "Set as Init Image" | Task 2 (ShotResultCard onSetInitImage) |
| 16:9 aspect ratio cards | Task 2 (ShotResultCard aspect-video) |
| Empty state CTA | Task 2 (GalleryLayout EmptyState) |
| Skeleton loading | Task 2 (GalleryPage Skeleton) |
| /results/{runId} URL | Task 5 (App.tsx route) |
| EP-006 skeleton patterns | Task 2 (loading states) |

| F-006 Requirement | Task |
|---|---|
| Manifest-based history display | Task 3 (useRunHistory) |
| Aggregate status (completed/partial/failed/running) | Task 3 (computeAggregate) |
| Mini shot status dots | Task 3 (MiniShotStatus) |
| Left color bar by status | Task 3 (RunCard border-l-4) |
| Relative time (<7 days) / absolute date | Task 3 (formatRelativeTime) |
| Status filter tabs | Task 3 (HistoryFilters) |
| "Load More" pagination | Task 3 (LoadMoreButton) |
| Config drift detection | Task 3 (ConfigDriftWarning + useConfigDrift) |
| Safe parameter restore (copy, not overwrite) | Task 3 (handleRestoreParams → /tuner) |
| Delete with confirmation | Task 3 (delete dialog) |
| Run detail drawer | Task 3 (RunDetailDrawer) |
| "View raw data" expandable | Task 3 (RunDetailDrawer details) |
| Skeleton screen loading | Task 3 (HistoryPage Skeleton) |
| Running run → monitor link | Task 3 (RunCard onViewMonitor) |

| F-007 Requirement | Task |
|---|---|
| Dual-panel layout (40%/60%) | Task 4 (TunerLayout) |
| 3 scope modes (current/all/default) | Task 4 (ScopeSelector + ParameterPanel) |
| EP-008 3-tier params | Task 4 (ParameterPanel with Collapsible) |
| Seed: value + random + lock + increment | Task 4 (SeedControl) |
| Override "Custom" badge + Reset | Task 4 (OverrideIndicator) |
| Real-time validation (300ms) | **Deferred** — debounce on API calls; inline validation follow-up |
| Workflow JSON preview with diff | Task 4 (JsonPreview with diffPaths) |
| Visual preview (JSON/Visual toggle) | Task 4 (PreviewPanel with Tabs) |
| Change summary before rerun | Task 4 (ChangeSummary) |
| 409 conflict dialog | Task 4 (ConflictDialog) |
| Re-run creates new Run | Task 4 (handleRerun → rerun mutation) |
| Change count in footer | Task 4 (TunerLayout bottom bar) |
| Unsaved changes warning | **Deferred** — beforeunload handler follow-up |
| Entry from F-003/F-005/F-006/F-004 | Task 4 (TunerPage via searchParams) |

### 2. Placeholder Scan

No TBD/TODO/fill-in patterns. All steps contain actual code.

### 3. Type Consistency

- `GalleryIndex` in `use-gallery.ts` matches `GalleryLayout` props
- `RunSummary` from `types/run.ts` reused in `RunCard` and `useRunHistory`
- `ShotWithEffective.overrides` string array used in `OverrideIndicator.isCustom` check
- `ApiError.status` checked for 409 in `TunerPage.handleRerun`
- `formatRelativeTime` and `formatDuration` shared across F-004 and F-006

### 4. Gaps & Follow-ups

- **Real-time inline validation** (F-007 AC#3): Debounce API validation calls; inline error display not in MVP.
- **Keyboard Alt+Up/Down** (F-003): Not addressed in this plan (was deferred in core-loop plan).
- **Unsaved changes beforeunload** (F-007 AC#13): Follow-up task.
- **Browser Notification API** (F-004 AC#12): Follow-up task.
- **Workflow JSON live preview** (F-007): `workflowJson` prop is `null` in MVP — requires API endpoint call with debounce; structure is ready.
- **Video frame-by-frame navigation** (F-005): Native `<video>` doesn't support precise frame stepping; follow-up with enhanced player.
