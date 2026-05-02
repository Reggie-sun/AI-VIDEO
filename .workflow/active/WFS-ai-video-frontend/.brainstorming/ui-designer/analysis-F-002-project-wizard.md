# F-002 Project Wizard -- UI Designer Analysis

**Feature**: project-wizard | **Priority**: High | **Framework**: @../guidance-specification.md

## 1. Screen Layout

### Wizard Container

The project wizard MUST be the first experience users encounter. It follows the full-screen single-task pattern from @analysis-cross-cutting.md Section 3.

```
+----------------------------------------------------+
| [AI-VIDEO Logo]    Step 1 > 2 > 3 > 4     [? Help] |
+----------------------------------------------------+
|                                                    |
|        +--------------------------------+          |
|        |   Step Content Area            |          |
|        |   max-width: 680px             |          |
|        |   centered                     |          |
|        +--------------------------------+          |
|                                                    |
+----------------------------------------------------+
| [< Back]                            [Next >]      |
+----------------------------------------------------+
```

### Step Indicator Design

The step indicator MUST show:
- Current step: filled accent color, bold label
- Completed steps: checkmark icon, muted clickable
- Future steps: outlined, disabled
- Step labels: "1. Project", "2. Characters", "3. Shots", "4. Review"

Transitions between steps MUST use the page transition animation from @analysis-cross-cutting.md Section 4.

## 2. Step-by-Step Design

### Step 1: Project Setup

Maps to `ProjectConfig` model fields.

**Fields**:
- **Project Name** (`project_name`): Text input, required, auto-suggested "My Project"
- **ComfyUI URL** (`comfy.base_url`): Text input with URL validation, default `http://127.0.0.1:8188`
  - MUST show connection test button ("Test Connection") with status indicator
- **Output Directory** (`output.root`): `<PathSelector>` component, default `runs/`
- **Minimum Free Space** (`output.min_free_gb`): Number input with "GB" suffix, default 1.0

**Advanced Section** (collapsed by default):
- Allow Non-Local (`comfy.allow_non_local`): Toggle switch with warning badge
- Poll Interval (`defaults.poll_interval_seconds`): Number input, slider variant
- Job Timeout (`defaults.job_timeout_seconds`): Number input with "seconds" suffix

**Design Notes**:
- The "Test Connection" button is the primary affordance for non-technical users to verify setup
- Advanced section uses `<Accordion>` from shadcn/ui to hide complexity
- All fields MUST have tooltip descriptions (hover `?` icon)

### Step 2: Default Parameters

Maps to `DefaultsConfig` model fields.

**Layout**: Two-column grid for dimensions/fps, single-column for prompts.

**Fields**:
- **Resolution**: Side-by-side Width x Height number inputs
  - SHOULD offer preset buttons: "512x512", "832x480", "1280x720"
- **FPS** (`fps`): Number input with slider (range 8-30)
- **Clip Duration** (`clip_seconds`): Number input with slider (range 1-10)
- **Seed** (`seed`): Number input + "Randomize" button (dice icon)
- **Seed Policy** (`seed_policy`): Select dropdown -- "derived" / "fixed" / "random"
- **Negative Prompt** (`negative_prompt`): `<Textarea>` with character count
- **Style Prompt** (`style_prompt`): `<Textarea>` with character count

**Design Notes**:
- Resolution presets reduce cognitive load for non-technical users
- Seed "Randomize" button makes the concept approachable
- Prompt textareas SHOULD auto-resize up to 4 lines

### Step 3: Characters

Maps to `CharacterProfile` model fields.

**Layout**: List of character cards + "Add Character" button.

**Character Card**:
```
+------------------------------------------+
| [Avatar]  Character: hero          [X]   |
|           Name: Hero                      |
|           Description: same face, same... |
|           Ref Images: [thumb1] [+add]     |
|           IPAdapter Weight: [====] 0.8    |
+------------------------------------------+
```

**Fields per Character**:
- **ID** (`id`): Text input, auto-generated from name (slugified), editable
- **Name** (`name`): Text input, required
- **Description** (`description`): Textarea, optional
- **Reference Images** (`reference_images`): File picker via `<PathSelector>`, thumbnail grid
- **IPAdapter Weight** (`ipadapter.weight`): Slider 0-1, step 0.1
- **IPAdapter Range** (`start_at`/`end_at`): Optional number inputs

**Empty State**: "No characters yet. Characters help maintain visual consistency across shots."

**Design Notes**:
- Character cards use `<Collapsible>` -- expanded when active, collapsed when viewing list
- Reference images MUST show `<FrameThumbnail>` previews
- Deleting a character MUST warn if referenced by existing shots

### Step 4: Review & Confirm

**Layout**: Summary view of all configured parameters, grouped by section.

**Content**:
- Project info summary card (name, comfy url, output dir)
- Defaults summary card (resolution, fps, seed policy)
- Characters summary (name + image count)
- Shot list preview (if shots already exist -- links to F-003)

**Actions**:
- "Create Project" primary button (creates project.yaml via API)
- "Edit" links next to each section that jump back to relevant step

## 3. Component Specifications

### `<WizardStep>` Component

- MUST accept: `title`, `description`, `children`
- Step title: `text-2xl font-semibold`
- Step description: `text-muted-foreground` below title
- Content area: `mt-6` spacing below description

### `<ParameterField>` Usage in Wizard

Each input MUST be wrapped in `<ParameterField>`:
- `label`: Human-readable field name
- `description`: One-line explanation (shows as muted text below label)
- `tooltip`: Extended explanation (shows on `?` icon hover)
- `required`: Boolean, shows asterisk
- `error`: Validation error message

### Connection Test Button

The ComfyUI URL field MUST include an inline connection test:
- Idle state: "Test Connection" button (outline variant)
- Loading: Spinner on button
- Success: Green checkmark + "Connected" text (fades after 3s)
- Failure: Red X + "Could not connect" + retry prompt

## 4. Validation Strategy

### Progressive Validation

- Step 1 fields: Validate on blur, block "Next" until valid
- Step 2 fields: Validate on change for sliders, on blur for text
- Step 3: Character ID uniqueness enforced on blur
- Step 4: No validation needed (review only)

### Cross-Step Validation

The wizard MUST validate across steps:
- Character IDs referenced in shots (F-003) MUST exist in Step 3
- Workflow template path MUST be a valid JSON file

## 5. Key Recommendations

1. Step 1 MUST prioritize the "Test Connection" interaction -- this is the primary trust-builder for non-technical users
2. Resolution presets MUST be the primary interaction mode; raw number inputs are secondary
3. The "Advanced" accordion in Step 1 MUST be collapsed by default to avoid overwhelming new users
4. Character management in Step 3 MUST feel lightweight -- avoid form-heavy layouts
5. The Review step MUST provide clear "Edit" links back to each section, not force linear re-navigation
