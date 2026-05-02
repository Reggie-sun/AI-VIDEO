# F-005 Result Gallery -- UI Designer Analysis

**Feature**: result-gallery | **Priority**: Medium | **Framework**: @../guidance-specification.md

## 1. Gallery Layout

### Primary Layout: Grid with Shot Context

The gallery MUST present results organized by shot, showing the visual artifacts (clip, last_frame, final) for each shot in the run.

```
+------------------------------------------------------------------+
|  Results: "My Project" -- Run #3              [Grid] [Timeline]  |
+------------------------------------------------------------------+
|                                                                   |
|  +-- shot_001 --+  +-- shot_002 --+  +-- shot_003 --+           |
|  | [Video Play] |  | [Video Play] |  | [Video Play] |           |
|  |              |  |              |  |              |           |
|  | [clip] [lf] |  | [clip] [lf] |  | [clip] [lf] |           |
|  | "hero enters"|  | "hero turns"|  | "hero walks"|           |
|  +--------------+  +--------------+  +--------------+           |
|                                                                   |
|  +-- Final Output --------------------------------------------+  |
|  |  [Final Video Player -- full width]                        |  |
|  |  Download: [MP4] [All Frames ZIP]                         |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+
```

### View Modes

The gallery MUST support two view modes:

1. **Grid View** (default): Shot cards in responsive grid (3 columns on desktop)
2. **Timeline View**: Horizontal strip showing shots in sequence with Frame Relay connectors

Toggle between views: icon buttons in header (`LayoutGrid` / `Film`)

## 2. Video Player Component

Per @../guidance-specification.md D-013, the video player MUST use native HTML5 video for MVP, with swappable enhancement reserved.

### Native Player Design

```
+------------------------------------------+
|                                          |
|           [Video Content]                |
|                                          |
+------------------------------------------+
| 00:00 [========------] 00:02  [CC] [FS] |
+------------------------------------------+
```

**Player Specifications**:
- MUST use `<video>` element with `controls` attribute
- MUST set `poster` to `last_frame.png` for instant visual feedback
- MUST support `preload="metadata"` for fast initial load
- Playback controls: native browser controls (MVP)
- Full-screen: native `controlsList` with fullscreen enabled

### Swappable Enhancement Architecture

The `<VideoPlayer>` component MUST be designed for future enhancement:

```
Props:
  - src: string (video URL)
  - poster?: string (thumbnail URL)
  - enhanced?: boolean (future: switch to video.js/plyr)
  - onEnded?: callback
```

- MVP: `enhanced={false}` renders `<video>` directly
- Future: `enhanced={true}` renders `<VideoJsPlayer>` or `<PlyrPlayer>`
- The component interface MUST NOT change when switching implementations

### Video Source URL

Videos are served by the API server from local filesystem:
- Clip: `/api/files/{run_id}/{shot_id}/clip`
- Last Frame: `/api/files/{run_id}/{shot_id}/last_frame`
- Final: `/api/files/{run_id}/final`

The `<VideoPlayer>` MUST construct these URLs from run context, not hardcode paths.

## 3. Shot Result Card

### Card Structure

Each shot result is displayed as a card with video and metadata:

```
+------------------------------------------+
| [Video Player - 16:9 aspect ratio]       |
|                                          |
+------------------------------------------+
| shot_001  |  Completed  |  1.8s          |
| "hero enters a quiet studio..."          |
|                                          |
| [Clip]  [Last Frame]  [Final]            |
| [Download] [Open in Tuner]               |
+------------------------------------------+
```

**Video Area**:
- 16:9 aspect ratio container (consistent across all cards)
- Poster frame: `last_frame.png`
- On hover: play icon overlay
- On click: inline playback (no modal)

**Metadata Row**:
- Shot ID: monospace, `text-sm`
- Status: `<StatusBadge>` component
- Duration: clip duration from metadata

**Artifact Tabs**:
- Toggle between clip, last_frame, and final views
- Active tab: accent underline
- Last frame view: `<img>` tag instead of video player

**Action Buttons**:
- Download: saves file to user's downloads directory
- Open in Tuner: navigates to F-007 param-tuner with this shot's params

## 4. Frame Gallery

### Individual Frame View

When viewing "Last Frame" tab, the card MUST show:

```
+------------------------------------------+
| [Full Image - last_frame.png]            |
|                                          |
+------------------------------------------+
| 512 x 512  |  PNG  |  234 KB            |
| [Download Image] [Set as Init Image]     |
+------------------------------------------+
```

- "Set as Init Image" copies this frame as init_image for another shot
- MUST open a shot selector dropdown: "Use as init image for which shot?"

### Frame Comparison

The gallery SHOULD support a side-by-side comparison mode:
- Select two shots to compare their last frames
- Split view with slider divider
- This is a post-MVP enhancement

## 5. Final Output Section

### Concatenated Video

After all shots complete, the pipeline produces a final concatenated video. This MUST be prominently featured:

- Full-width video player below the shot grid
- Larger player size: 640px height (vs 280px for shot clips)
- Label: "Final Video -- All Shots Combined"
- Download options: MP4, All Frames as ZIP

### Download Options

The download interface MUST be clear and accessible:

- Single file download: direct link button
- Batch download: "Download All" button (triggers ZIP creation via API)
- Download progress: toast notification with progress
- Download complete: success toast with "Open" button (if browser supports)

## 6. Empty & Loading States

### No Results Yet

If no completed run exists:
```
+------------------------------------------+
|         [Film icon]                       |
|   No results yet.                         |
|   Run the pipeline to generate videos.    |
|   [Go to Pipeline]                        |
+------------------------------------------+
```

### Partial Results

If some shots completed but not all:
- Completed shots: normal card display
- Incomplete/failed shots: show card with placeholder + status badge
- Clear indicator: "2 of 3 shots completed"

### Loading Frames/Videos

- Videos: `<VideoPlayer>` shows poster frame immediately, loads video on play
- Images: `<FrameThumbnail>` with skeleton while loading
- Error: broken image icon with "Failed to load" message

## 7. Gallery Navigation

### From Generation Monitor

After pipeline completes (F-004), the "View Results" CTA MUST navigate to the gallery with the completed run context.

### From Run History

From F-006, selecting a past run MUST open the gallery for that run.

### URL Structure

Gallery MUST be accessible via URL:
- `/results/{run_id}` -- shows results for a specific run
- `/results/latest` -- shows results for the most recent run

## 8. Key Recommendations

1. The video player MUST show poster frames instantly -- do not wait for video download
2. Shot result cards MUST be consistent in size (16:9 ratio) to create visual rhythm in the grid
3. The final output video MUST be the visual climax of the page -- give it prominence
4. Download interactions MUST provide clear feedback (progress, completion) since files can be large
5. The "Set as Init Image" cross-feature interaction (gallery to editor) MUST be intuitive and well-explained
