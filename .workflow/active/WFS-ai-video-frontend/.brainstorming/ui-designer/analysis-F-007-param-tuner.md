# F-007 Param Tuner -- UI Designer Analysis

**Feature**: param-tuner | **Priority**: Medium | **Framework**: @../guidance-specification.md

## 1. Layout Design

### Split-Panel Layout

The param tuner MUST use a split-panel layout: parameters on the left, preview on the right.

```
+------------------------------------------------------------------+
|  Param Tuner: shot_001                    [Reset] [Save] [Run]   |
+------------------------------------------------------------------+
|                          |                                       |
|  PARAMETERS              |  PREVIEW                              |
|  +---------------------+ |  +---------------------------------+ |
|  | Prompt *            | |  |                                 | |
|  | [textarea         ] | |  |  Workflow JSON Preview          | |
|  |                     | |  |  (or)                           | |
|  | Negative Prompt     | |  |  Last Frame Preview             | |
|  | [textarea         ] | |  |                                 | |
|  |                     | |  +---------------------------------+ |
|  | Seed [42] [Random]  | |                                       |
|  | Duration [2]s       | |  VALIDATION                           |
|  | FPS [16]            | |  +---------------------------------+ |
|  | Width [512]         | |  | All parameters valid            | |
|  | Height [512]        | |  | Seed: derived from previous     | |
|  |                     | |  +---------------------------------+ |
|  | Characters [hero +] | |                                       |
|  +---------------------+ |                                       |
+------------------------------------------------------------------+
```

- Left panel: 40% width, scrollable
- Right panel: 60% width, sticky (does not scroll with left)
- Divider: draggable resizer (optional, MAY be fixed in MVP)

## 2. Parameter Panel Design

### Grouped Parameters

Parameters MUST be organized into logical groups using shadcn/ui `<Accordion>`:

**Group 1: Prompt & Content** (always expanded)
- Prompt (`prompt`): `<Textarea>`, required, auto-resize
- Negative Prompt (`negative_prompt`): `<Textarea>`, optional
- Continuity Note (`continuity_note`): `<Textarea>`, optional

**Group 2: Generation Settings** (always expanded)
- Seed (`seed`): Number input + "Randomize" button
- Clip Duration (`clip_seconds`): Slider (1-10s) with number display
- FPS (`fps`): Slider (8-30) with number display

**Group 3: Dimensions** (expanded by default)
- Width (`width`): Number input with preset buttons
- Height (`height`): Number input with preset buttons
- Resolution presets: "512x512", "832x480", "1280x720" (same as F-002)

**Group 4: Characters & References** (collapsed by default)
- Character selection: Badge picker (same as F-003)
- Init Image (`init_image`): `<PathSelector>` with `<FrameThumbnail>` preview
- IPAdapter settings: Per-character weight sliders

**Group 5: Advanced** (collapsed by default)
- Max Attempts (`max_attempts`): Number input (1-5)
- Poll Interval (`poll_interval_seconds`): Number input
- Job Timeout (`job_timeout_seconds`): Number input

### Parameter Field Component

All parameter inputs MUST use `<ParameterField>` with:
- `label`: Human-readable name
- `description`: One-line explanation
- `tooltip`: Extended help on `?` icon hover
- `validation`: Inline error on invalid value
- `default`: Show "Default: X" in muted text when value differs from project default

### Override Indicators

When a shot parameter overrides the project default, the UI MUST indicate this:

- Show a small "override" badge next to the field label
- Badge text: "Custom" or "Override"
- Badge style: `bg-accent/10 text-accent text-xs px-1.5 py-0.5 rounded`
- "Reset to default" button appears next to the badge
- On reset: field value reverts to project default, badge disappears

This is critical for non-technical users to understand which parameters they have customized.

## 3. Preview Panel

### Dual Preview Modes

The right panel MUST support two preview modes:

**Mode 1: Workflow JSON Preview**

Shows the resulting workflow JSON (after binding) that will be sent to ComfyUI:

```
+-----------------------------------------+
| Workflow JSON           [Copy] [Expand] |
+-----------------------------------------+
| {                                       |
|   "3": {                                |
|     "class_type": "KSampler",           |
|     "inputs": {                         |
|       "seed": 42,                       |
|       "steps": 20,                      |
|       "cfg": 7.0,                       |
|       "prompt": "hero enters..."        |
|     }                                   |
|   }                                     |
| }                                       |
+-----------------------------------------+
```

- Syntax-highlighted JSON using `<pre>` with `font-mono text-sm`
- MUST update in real-time as parameters change (with 300ms debounce)
- "Copy" button: copies JSON to clipboard
- "Expand" button: opens JSON in full-screen modal

**Mode 2: Visual Preview**

Shows visual context for the shot:
- Last frame from previous shot (if available, for Frame Relay context)
- Init image (if set)
- Character reference images (if assigned)

This mode helps users understand the visual context their parameters will operate in.

### Preview Mode Toggle

- Tab switcher: [JSON] [Visual] in the panel header
- Default: JSON mode (for technical understanding)
- Visual mode for creative context

## 4. Real-Time Validation

### Validation Rules

The tuner MUST validate parameters in real-time:

| Parameter | Validation | Error Message |
|-----------|-----------|---------------|
| prompt | Required, non-empty | "Prompt is required" |
| seed | Integer >= 0 | "Seed must be a non-negative integer" |
| width | 256-2048, multiple of 8 | "Width must be 256-2048, multiple of 8" |
| height | 256-2048, multiple of 8 | "Height must be 256-2048, multiple of 8" |
| fps | 8-60 | "FPS must be between 8 and 60" |
| clip_seconds | 1-30 | "Duration must be 1-30 seconds" |
| characters | Must exist in project | "Character '{name}' not found in project" |

### Validation Display

- Invalid fields: red border, error message below
- Valid state: subtle green checkmark on field right edge (appears after user interaction)
- Summary in right panel: "3/5 parameters valid" or "All parameters valid"

### Cross-Field Validation

The tuner MUST validate relationships between parameters:
- Width/Height ratio warning for unusual aspect ratios
- FPS x clip_seconds > 500 frames: "This will generate a large number of frames. Consider reducing duration or FPS."
- Init image dimensions vs. target dimensions mismatch warning

## 5. "Run" Interaction

### Single Shot Run

The "Run" button MUST trigger generation for this specific shot only:

1. Validation check: all required fields valid
2. Confirmation dialog: "Generate shot_001? This may take a few minutes."
3. On confirm: navigate to F-004 generation monitor (filtered to this shot)
4. Toast: "Generation started for shot_001"

### Pipeline Run

The tuner MUST also offer a "Run Pipeline" option that runs all shots:
- This reuses the F-004 pipeline execution flow
- The tuner's "Run Pipeline" is equivalent to the monitor's "Start Pipeline"

### Run with Different Seed

A quick-action: "Run with Random Seed" -- generates with a new random seed without leaving the tuner. This supports iterative exploration.

## 6. Comparison & Diff

### Parameter Comparison (Post-MVP)

The tuner SHOULD support comparing parameters between:
- Current shot vs. project defaults
- Current shot vs. another shot
- Current run vs. previous run

This MUST be deferred to post-MVP but the data model SHOULD accommodate it.

### Change History

The tuner MAY track parameter changes within a session:
- Undo/Redo buttons for parameter changes
- Change history panel (optional)

## 7. Entry Points

The param tuner MUST be accessible from multiple contexts:

| Entry Point | Pre-filled State | Focus |
|-------------|-----------------|-------|
| From Shot Card Editor (F-003) | Current shot params | Prompt field |
| From Result Gallery (F-005) | Shot's params from completed run | Prompt field |
| From Run History (F-006) | Run's configuration | First parameter group |
| From Generation Monitor (F-004) | Failed shot's params | Failed parameter |

## 8. Key Recommendations

1. The split-panel layout MUST keep the preview visible while editing -- this is the primary feedback mechanism
2. Override indicators MUST be prominent -- non-technical users need to know what they have customized vs. inherited
3. Real-time workflow JSON preview MUST be instant (300ms debounce) to feel responsive
4. The "Run with Random Seed" quick-action MUST be easily accessible -- it supports the most common iterative workflow
5. Validation MUST be helpful (suggesting fixes) not punitive (just showing errors)
6. The visual preview mode MUST help users understand Frame Relay context -- showing the previous shot's last frame is essential
