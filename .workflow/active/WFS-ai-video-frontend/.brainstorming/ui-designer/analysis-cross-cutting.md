# UI Designer Cross-Cutting Analysis

**Role**: ui-designer | **Framework**: @../guidance-specification.md | **Date**: 2026-05-02

## 1. Design Token System

### Color Palette

The system MUST define a coherent color token hierarchy using OKLCH space for consistency across light/dark themes.

**Semantic Tokens** (MUST be defined at `:root` level):

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--background` | `oklch(0.99 0 0)` | `oklch(0.12 0 0)` | Page background |
| `--foreground` | `oklch(0.14 0 0)` | `oklch(0.98 0 0)` | Primary text |
| `--card` | `oklch(1.0 0 0)` | `oklch(0.16 0 0)` | Card surfaces |
| `--muted` | `oklch(0.96 0 0)` | `oklch(0.20 0 0)` | Secondary backgrounds |
| `--accent` | `oklch(0.70 0.15 250)` | `oklch(0.70 0.15 250)` | Brand accent (teal) |
| `--destructive` | `oklch(0.55 0.20 25)` | `oklch(0.55 0.20 25)` | Error/danger states |
| `--success` | `oklch(0.65 0.18 145)` | `oklch(0.65 0.18 145)` | Completed states |
| `--warning` | `oklch(0.75 0.15 85)` | `oklch(0.75 0.15 85)` | Pending/attention states |

**Pipeline Status Colors** (MUST be consistent across F-003, F-004, F-006):

| Status | Token | Color | Visual |
|--------|-------|-------|--------|
| Queued | `--status-queued` | `oklch(0.70 0 0)` | Gray, pulse animation |
| Running | `--status-running` | `oklch(0.70 0.15 250)` | Accent, spinner |
| Completed | `--status-completed` | `oklch(0.65 0.18 145)` | Green, checkmark |
| Failed | `--status-failed` | `oklch(0.55 0.20 25)` | Red, error icon |

### Typography

The system MUST use the following font stack:

- **UI Text**: `Inter, system-ui, sans-serif` -- all labels, buttons, body text
- **Monospace**: `JetBrains Mono, monospace` -- JSON preview, technical values, IDs, paths
- **Heading Scale**: `text-2xl` (page title), `text-xl` (section), `text-lg` (card title), `text-base` (body), `text-sm` (caption/hint)

### Spacing & Layout Grid

- **Base Unit**: 4px (Tailwind default)
- **Component Gap**: 8px (tight), 16px (standard), 24px (section)
- **Page Margins**: 24px mobile, 48px desktop
- **Max Content Width**: 1200px (centered for wizard steps)
- **Card Dimensions**: min-width 280px, max-width 400px (shot cards)

## 2. Shared Component Library

### Components That Span Multiple Features

The following components MUST be built once and reused across features:

**`<StatusBadge>`** -- F-003, F-004, F-006, F-007
- Displays shot/run status with color dot + label
- Props: `status` (queued|running|completed|failed), `size` (sm|md), `animated` (boolean)
- MUST use pipeline status tokens from Section 1

**`<PathSelector>`** -- F-002, F-007
- File/directory picker that communicates with API to browse local filesystem
- MUST show current path, allow navigation, support file type filtering
- SHOULD validate path existence on blur

**`<ParameterField>`** -- F-002, F-003, F-007
- Unified parameter input component with label, description, validation
- Variants: text, number, select, slider, toggle
- MUST support `tooltip` prop for inline help (non-technical users)
- MUST show validation error inline below the field

**`<VideoPlayer>`** -- F-005, F-006
- Wraps HTML5 `<video>` with consistent controls
- MUST support `src` as local file URL served by API
- SHOULD be designed for future swappable enhancement (video.js/plyr)
- MUST show poster frame (last_frame.png) before play

**`<FrameThumbnail>`** -- F-003, F-004, F-005
- Displays init_image or last_frame as thumbnail
- Props: `src`, `size` (sm|md|lg), `clickable` (boolean)
- MUST show placeholder skeleton while loading

**`<EmptyState>`** -- All features
- Illustrated empty state with icon, message, and CTA
- Must be used consistently: no shots, no runs, no results

## 3. Layout Architecture

### Full-Screen Single-Task Pattern

Per @../guidance-specification.md D-014, the layout MUST use full-screen single-task as primary strategy.

**Layout Structure**:
```
+------------------------------------------+
| [Logo] AI-VIDEO    [Wizard Steps]  [Help] |
+------------------------------------------+
|                                          |
|         Step Content (full-width)        |
|         max-width: 1200px, centered      |
|                                          |
+------------------------------------------+
| [Back]                    [Next / Run]   |
+------------------------------------------+
```

**Header** MUST contain:
- Project name / logo (left)
- Wizard step indicator (center) -- F-002
- Help toggle (right)

**Footer** MUST contain:
- Back navigation (left)
- Primary action button (right)

### Wizard-to-Card Transition

Per @../guidance-specification.md D-015, when entering the shot editing step (F-003), the layout MUST transition from centered single-content to a card-list layout:

- Step indicator highlights "Edit Shots"
- Content area expands to full width
- Cards arranged in a scrollable vertical list with drag handles
- Footer remains with "Back" and "Run Pipeline" actions

This transition SHOULD use a smooth 300ms animation to indicate context change without disorienting the user.

## 4. Motion & Animation Specification

### Global Motion Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--duration-fast` | 150ms | Hover, focus, toggle |
| `--duration-normal` | 300ms | Page transitions, card expand |
| `--duration-slow` | 500ms | Complex layout shifts |
| `--easing-default` | `cubic-bezier(0.4, 0, 0.2, 1)` | Standard transitions |
| `--easing-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Playful micro-interactions |

### Animation Patterns

**Page Transition** (wizard step change):
- Outgoing: `300ms ease-out [X0→-40, α1→0]`
- Incoming: `300ms ease-out [X40→0, α0→1]`

**Card Drag** (F-003):
- Lift: `150ms --easing-spring [S1→1.02, shadow+2]`
- Drop: `200ms --easing-default [S1.02→1, shadow-2]`

**Status Update** (F-004):
- Pulse for running: `2000ms ∞ [α0.6→1→0.6]` on status dot
- Flash on change: `400ms ease-out [bg: accent→transparent]`

**Skeleton Loading** (all features):
- `1500ms ∞ [bg: muted→accent/10→muted]`

## 5. Error & Loading Patterns

### Loading States

Every feature MUST implement three loading states:

1. **Skeleton**: Initial page load, structure unknown -- use shadcn/ui `<Skeleton>`
2. **Spinner**: Action in progress (save, run) -- use `<Loader2>` icon with `animate-spin`
3. **Progress**: Long-running task (pipeline execution) -- use progress bar or node view (F-004)

### Error States

The system MUST handle errors at three levels:

1. **Field-level**: Inline validation messages below `<ParameterField>`, red border + error text
2. **Feature-level**: `<Alert variant="destructive">` at top of content area, dismissible
3. **System-level**: Full-page error boundary with retry button, contact info

### Empty States

Every list/gallery view MUST implement an `<EmptyState>` with:
- Relevant Lucide icon (e.g., `Film`, `Image`, `Clock`)
- Descriptive message ("No shots yet. Create your first shot to get started.")
- Primary CTA button

## 6. Responsive Strategy

MVP targets **desktop-primary** (1280px+) with graceful degradation:

| Breakpoint | Width | Layout Adaptation |
|------------|-------|-------------------|
| Desktop XL | 1440px+ | Max-width 1200px centered |
| Desktop | 1280px | Full width with margins |
| Tablet | 768px-1279px | Stack sidebar content, card grid 2-col |
| Mobile | < 768px | Single column, stacked cards, bottom sheet for details |

MVP MUST support Desktop and Desktop XL. Tablet and Mobile SHOULD be supported but MAY defer to post-MVP.

## 7. Accessibility Foundation

- All interactive elements MUST be keyboard navigable (shadcn/ui provides this via Radix)
- Color MUST NOT be the sole indicator of state (always pair with icon/text)
- Focus rings MUST use `ring-2 ring-ring ring-offset-2` pattern
- Form fields MUST have associated `<label>` elements
- Video content MUST have `aria-label` describing the shot
- Drag-and-drop (F-003) MUST provide keyboard alternative (move up/down buttons)

## 8. Dark/Light Theme

- Dark theme MUST be the default (video creators typically work in dark environments)
- Theme toggle SHOULD be available in header
- Theme preference MUST persist in localStorage
- All components MUST pass WCAG AA contrast in both themes
- Video/image content MUST NOT be affected by theme changes (always original color)
