# F-003 Shot Card Editor -- UI Designer Analysis

**Feature**: shot-card-editor | **Priority**: High | **Framework**: @../guidance-specification.md

## 1. Layout Transition

Per @../guidance-specification.md D-015, when entering the shot editing step, the layout MUST transition from the centered wizard content to a full-width card-list layout:

```
BEFORE (wizard centered):          AFTER (card list full-width):
+---------------------------+      +-------------------------------+
|     [  Content  ]         |      | [Step: 1>2>[3]>4]            |
|     [  680px    ]         |  →   |                               |
|     [  centered ]         |      | [Card1] [Card2] [Card3] [+Add]|
|                           |      | [======= Drag Area ========]  |
+---------------------------+      +-------------------------------+
```

The transition SHOULD animate at 300ms with the content area expanding to full width and cards fading in with a stagger effect (50ms delay per card).

## 2. Shot Card Design

### Card Structure

Each shot maps to a `ShotSpec` model instance. The card MUST present shot information at two density levels:

**Collapsed State** (default):
```
+----------------------------------------------------------+
| [::]  shot_001                               [v] [X]    |
|       hero enters a quiet studio, medium shot             |
|       Characters: [hero]  |  2s  |  512x512  |  seed:42 |
+----------------------------------------------------------+
```

- Drag handle (`::`) on left: 6-dot grip icon
- Shot ID: monospace, `text-sm font-medium`
- Prompt: truncated to 2 lines, `text-muted-foreground`
- Metadata row: character badges, duration, resolution, seed
- Expand toggle (`v`): chevron icon
- Delete button (`X`): red on hover, confirmation required

**Expanded State** (editing):
```
+----------------------------------------------------------+
| [::]  shot_001                               [^] [X]    |
|----------------------------------------------------------|
|                                                          |
|  Prompt *                                                |
|  [hero enters a quiet studio, medium shot               ]|
|                                                          |
|  Negative Prompt                                         |
|  [blur, inconsistent face                               ]|
|                                                          |
|  Characters    [hero +]                                  |
|  Init Image     [Choose File...]                         |
|  Continuity Note                                         |
|  [smooth transition from previous shot                  ]|
|                                                          |
|  --- Parameters ---                                      |
|  Seed [42] [Randomize]   Duration [2s]   FPS [16]       |
|  Width [512]   Height [512]                              |
+----------------------------------------------------------+
```

### Card Visual Specifications

- Background: `var(--card)` with `border border-border`
- Border-radius: `rounded-xl` (0.75rem)
- Hover: subtle shadow lift `shadow-md`
- Expanded: left accent border `border-l-4 border-l-accent`
- Selected/active: `ring-2 ring-ring ring-offset-2`

## 3. Drag-and-Drop Interaction

### Drag Behavior

- The drag handle (`::`) MUST be the only drag initiation point
- On drag start: card lifts with `--easing-spring [S1→1.02, shadow+2]` animation
- During drag: other cards shift to make space with 200ms transitions
- On drop: card settles with `--easing-default [S1.02→1, shadow-2]`
- Ghost placeholder: dashed border, `bg-muted/50`

### Keyboard Alternative

Per @analysis-cross-cutting.md Section 7, drag-and-drop MUST have keyboard alternative:
- Focus on card: arrow keys move card up/down in list
- Visual: focused card shows `ring-2` and move buttons appear on hover

### Shot Order Semantics

- Shot order determines video generation sequence
- The UI MUST visually indicate sequence: numbered badges (1, 2, 3...) on cards
- After reorder, the UI MUST show a toast: "Shot order updated"

## 4. Field-Level Design

### Prompt Field

The prompt field is the most important field for content creators.

- MUST use `<Textarea>` with auto-resize (min 2 lines, max 6 lines)
- SHOULD show character count (not word count -- this is a prompt, not a document)
- MUST support multiline input for complex prompts
- Placeholder text: "Describe what happens in this shot..."

### Character Selection

Characters are defined in F-002 Step 3. The shot editor MUST reference them:

- Display as removable badges: `[hero x]`
- "Add" button opens a dropdown of available characters from the project
- If no characters defined: show inline link "Add characters in project settings"
- Badge style: `bg-accent/10 text-accent rounded-full px-2 py-0.5 text-sm`

### Init Image

- File picker via `<PathSelector>` with image filter
- MUST show `<FrameThumbnail>` preview when image is set
- SHOULD support drag-and-drop image file onto the card
- Clear button to remove image

### Parameter Grouping

Advanced parameters (seed, dimensions, fps, clip_seconds) MUST be grouped in a collapsible section:
- Default: collapsed, showing only non-default values in the metadata row
- Label: "Parameters" with count badge showing override count
- Inside: use `<ParameterField>` with slider variants for numeric values

### Continuity Note

- Simple `<Textarea>`, 1-2 lines
- Placeholder: "Note how this shot connects to the previous one..."
- This field is uniquely creative -- SHOULD NOT feel like a technical field
- Style: `bg-muted/30 border-dashed` to differentiate from required fields

## 5. Add Shot Interaction

### "Add Shot" Button

Position: after the last card in the list, as a dashed-border card placeholder:

```
+----------------------------------------------------------+
|                                                          |
|              [+] Add Shot                                |
|                                                          |
+----------------------------------------------------------+
```

- Style: `border-2 border-dashed border-muted-foreground/30`
- On hover: border becomes solid, accent color
- On click: creates a new card with auto-generated ID (shot_NNN)
- New card MUST expand immediately for editing

### Batch Operations

The editor SHOULD support:
- Duplicate shot (icon button on each card)
- Select multiple (checkbox mode) for bulk delete
- These are post-MVP enhancements

## 6. Visual Sequence Indicator

Since shot order is critical for Frame Relay (the mechanism where last_frame of shot N feeds shot N+1), the UI MUST make sequence visually explicit:

- Cards show sequential number badges
- Between cards, a subtle connector line with arrow:
```
[Card 1] ──→ [Card 2] ──→ [Card 3]
```
- The connector SHOULD animate on hover to highlight the flow direction
- Frame Relay note on hover: "Last frame from Shot 1 feeds into Shot 2"

## 7. Validation & Feedback

### Real-Time Validation

- Prompt: MUST not be empty (red border on blur if empty)
- Character references: MUST exist in project (badge turns red if invalid)
- Init image path: MUST be valid file (inline error if not found)

### Save Behavior

- Auto-save on change with 1-second debounce (spinner on card header during save)
- Manual save with Ctrl+S / Cmd+S
- Unsaved changes indicator: dot on card header, "Unsaved changes" in footer

## 8. Key Recommendations

1. The card MUST default to collapsed state -- only expand on user action, to prevent overwhelming the list
2. Prompt field MUST dominate the expanded view -- it is the primary creative input
3. Drag-and-drop reordering MUST feel lightweight and responsive (no confirmation dialog for reordering)
4. The visual sequence connector between cards MUST make Frame Relay flow obvious without explanation
5. Auto-save MUST be the default -- explicit save buttons create anxiety for non-technical users
