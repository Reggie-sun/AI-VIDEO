# Image Story To Film With Audio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local-first pipeline that takes one or more character reference images plus a story excerpt, automatically splits it into shots, generates multi-character shot prompts, renders a stitched film with stable character identity, and adds a narration audio track to the final video.

**Architecture:** Keep the existing `validate/run/resume` video pipeline intact and add an upstream planning layer plus a downstream audio layer. Story planning stays deterministic and local-first for MVP, using explicit config models and generated `ShotSpec` objects in memory during validation and on disk during `run` so `resume` remains manifest-driven and reproducible. Character consistency is handled through per-character LoRA training plus per-shot slot assignment so we only inject the characters needed by the current shot and stay within practical VRAM limits on a 5090.

**Tech Stack:** Python 3.11, Pydantic models, existing ComfyUI + ffmpeg pipeline, local rule-based text planning, `pyttsx3` for offline narration TTS, pytest.

---

## File Map

- Create: `src/ai_video/storyboard.py`
  - Deterministic story-to-shot planning and shot prompt generation.
- Create: `src/ai_video/audio.py`
  - Local narration synthesis and audio track assembly helpers.
- Create: `src/ai_video/character_lora.py`
  - Character consistency LoRA training job orchestration and artifact helpers.
- Create: `tests/test_storyboard.py`
  - Coverage for story splitting, duration estimation, and prompt generation.
- Create: `tests/test_audio.py`
  - Coverage for narration synthesis orchestration with mocked provider/ffmpeg.
- Create: `tests/test_character_lora.py`
  - Coverage for LoRA training job planning and workflow application.
- Modify: `src/ai_video/models.py`
  - Add story source config, audio config, character LoRA training config, and richer shot metadata fields.
- Modify: `src/ai_video/config.py`
  - Resolve new paths and validate story/audio/LoRA settings.
- Modify: `src/ai_video/cli.py`
  - Add additive `draft-story` and `train-character-lora` commands plus optional auto-generation path for `run`.
- Modify: `src/ai_video/pipeline.py`
  - Persist generated shot file paths and invoke audio finalization after video stitch.
- Modify: `src/ai_video/ffmpeg_tools.py`
  - Add narration mux helpers without breaking existing stitch contract.
- Modify: `src/ai_video/workflow_renderer.py`
  - Apply trained character LoRA weights into workflow bindings during render with per-shot slot allocation.
- Modify: `src/ai_video/manifest.py`
  - Store generated story/audio artifact paths for resume and debugging.
- Modify: `workflows/bindings/wan22_i2v_binding.yaml`
  - Add dynamic binding paths for optional character-consistency LoRA slots.
- Modify: `README.md`
  - Document the new story-driven flow, character LoRA training step, and local audio dependency.
- Modify: `tests/test_config.py`
  - Cover story/audio/LoRA config loading and path resolution.
- Modify: `tests/test_cli.py`
  - Cover `draft-story`, `train-character-lora`, and story-driven `run`.
- Modify: `tests/test_pipeline.py`
  - Cover final audio assembly integration.
- Modify: `tests/test_workflow_renderer.py`
  - Cover dynamic application of character LoRA paths and weights.
- Modify: `tests/test_resume_e2e.py`
  - Ensure resume respects generated shots path and completed audio output.

## Scope Notes

- MVP narration will be local/offline only via `pyttsx3`.
- MVP story planning will be deterministic and rule-based, not LLM-dependent.
- MVP soundtrack includes narration plus optional background music file, but not auto-generated SFX.
- MVP character consistency will support one LoRA training job per character profile, invoked through a configurable local trainer command and then applied automatically at render time.
- MVP multi-character support will keep `project.characters[]` as the source of truth and `shot.characters[]` as the per-shot cast list.
- MVP VRAM budget for a 5090 will reserve `lora_0` for the existing `LIGHTX2V` slot and cap active character LoRAs at **2 per shot** by default, leaving headroom for style/control LoRAs in `lora_3` and `lora_4`.
- If a shot references more than 2 characters in MVP, the planner should split that beat into multiple shots rather than loading all character LoRAs into one render.
- MVP must distinguish **identity-locked characters** from **background extras**:
  - identity-locked characters use `project.characters[]`, can have reference images and optional trained LoRAs, and count toward the per-shot LoRA budget.
  - background extras do **not** use LoRAs and should be expressed as prompt-level scene dressing such as crowd count, distance, blur, silhouette, or background actions.
- A shot may contain many extras, but no more than **2 identity-locked LoRA characters** in MVP.
- Existing `validate/run/resume` commands remain; `draft-story` is additive, not a rename.

### Task 1: Extend Project And Shot Models For Story And Audio

**Files:**
- Modify: `src/ai_video/models.py`
- Modify: `src/ai_video/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write the failing config tests**

```python
def test_load_project_resolves_story_and_audio_paths(tmp_path: Path):
    project = tmp_path / "project.yaml"
    refs = tmp_path / "refs"
    refs.mkdir()
    (refs / "hero.png").write_bytes(b"img")
    (tmp_path / "story.txt").write_text("First sentence. Second sentence.", encoding="utf-8")
    (tmp_path / "music.mp3").write_bytes(b"mp3")
    project.write_text(
        "project_name: story-demo\n"
        "comfy:\n  base_url: http://127.0.0.1:8188\n"
        "workflow:\n  template: workflows/template.json\n  binding: workflows/binding.yaml\n"
        "output:\n  root: runs\n  min_free_gb: 0\n"
        "story:\n"
        "  image: refs/hero.png\n"
        "  text_path: story.txt\n"
        "  max_sentences_per_shot: 2\n"
        "audio:\n"
        "  narration_enabled: true\n"
        "  bgm_path: music.mp3\n",
        encoding="utf-8",
    )
    loaded = load_project(project)
    assert loaded.story is not None
    assert loaded.story.image == tmp_path / "refs/hero.png"
    assert loaded.story.text_path == tmp_path / "story.txt"
    assert loaded.audio is not None
    assert loaded.audio.bgm_path == tmp_path / "music.mp3"


def test_load_project_rejects_story_without_image(tmp_path: Path):
    project = tmp_path / "project.yaml"
    project.write_text(
        "project_name: bad-story\n"
        "comfy:\n  base_url: http://127.0.0.1:8188\n"
        "workflow:\n  template: workflows/template.json\n  binding: workflows/binding.yaml\n"
        "story:\n  text_path: story.txt\n",
        encoding="utf-8",
    )
    with pytest.raises(AiVideoError) as exc:
        load_project(project)
    assert exc.value.code is ErrorCode.CONFIG_INVALID
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_config.py::test_load_project_resolves_story_and_audio_paths tests/test_config.py::test_load_project_rejects_story_without_image -v`
Expected: FAIL with missing `story` / `audio` fields on `ProjectConfig`

- [ ] **Step 3: Add minimal models and config resolution**

```python
class StorySourceConfig(BaseModel):
    image: Path
    text_path: Path
    max_sentences_per_shot: int = 2
    min_clip_seconds: int = 3
    max_clip_seconds: int = 6
    subject_description: str = ""


class AudioConfig(BaseModel):
    narration_enabled: bool = True
    voice: str = "default"
    rate: int = 180
    bgm_path: Path | None = None
    bgm_volume: float = 0.2


class ShotSpec(BaseModel):
    ...
    narration: str = ""
    camera: str = ""
    beat_summary: str = ""
    source_text: str = ""
    extras_prompt: str = ""


class ProjectConfig(BaseModel):
    ...
    story: StorySourceConfig | None = None
    audio: AudioConfig | None = None
```

```python
def resolve_project_paths(project: ProjectConfig, base_dir: Path) -> ProjectConfig:
    data = project.model_dump()
    ...
    if project.story is not None:
        data["story"]["image"] = _resolve_path(base_dir, project.story.image)
        data["story"]["text_path"] = _resolve_path(base_dir, project.story.text_path)
    if project.audio is not None and project.audio.bgm_path is not None:
        data["audio"]["bgm_path"] = _resolve_path(base_dir, project.audio.bgm_path)
    return ProjectConfig.model_validate(data)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_config.py::test_load_project_resolves_story_and_audio_paths tests/test_config.py::test_load_project_rejects_story_without_image -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ai_video/models.py src/ai_video/config.py tests/test_config.py
git commit -m "feat: add story and audio config models"
```

### Task 2: Add Deterministic Storyboard Planning

**Files:**
- Create: `src/ai_video/storyboard.py`
- Modify: `src/ai_video/models.py`
- Test: `tests/test_storyboard.py`

- [ ] **Step 1: Write the failing storyboard tests**

```python
def test_split_story_into_beats_groups_sentences():
    story = "Rain fell over the city. Mira hid the letter. Footsteps stopped outside the door."
    beats = split_story_into_beats(story, max_sentences_per_shot=2)
    assert beats == [
        "Rain fell over the city. Mira hid the letter.",
        "Footsteps stopped outside the door.",
    ]


def test_build_shots_from_story_uses_first_image_only(tmp_path: Path):
    story = "Mira opened the gate. Jae followed her into the courtyard."
    hero = tmp_path / "hero.png"
    sidekick = tmp_path / "sidekick.png"
    hero.write_bytes(b"img")
    sidekick.write_bytes(b"img")
    project = ProjectConfig.model_validate(
        {
            "project_name": "demo",
            "workflow": {"template": "x.json", "binding": "y.yaml"},
            "story": {"image": str(hero), "text_path": str(tmp_path / "story.txt")},
            "characters": [
                {"id": "mira", "name": "Mira", "description": "female lead", "reference_images": [str(hero)]},
                {"id": "jae", "name": "Jae", "description": "male companion", "reference_images": [str(sidekick)]},
            ],
        }
    )
    shots = build_shots_from_story(
        project=project,
        story_text=story,
        style_prompt="cinematic",
    )
    assert shots[0].init_image == hero
    assert shots[1].init_image is None
    assert shots[0].beat_summary
    assert shots[0].narration
    assert shots[0].characters == ["mira", "jae"]
    assert "background extras" in shots[0].extras_prompt
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_storyboard.py -v`
Expected: FAIL with missing module/function errors

- [ ] **Step 3: Implement local story splitting and shot generation**

```python
def split_story_into_beats(story_text: str, *, max_sentences_per_shot: int) -> list[str]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?。！？])\s+", story_text) if s.strip()]
    beats: list[str] = []
    for i in range(0, len(sentences), max_sentences_per_shot):
        beats.append(" ".join(sentences[i:i + max_sentences_per_shot]))
    return beats


def estimate_clip_seconds(beat: str, *, min_seconds: int, max_seconds: int) -> int:
    word_count = len(beat.split())
    estimated = max(min_seconds, min(max_seconds, math.ceil(word_count / 8)))
    return estimated


def build_shots_from_story(*, project: ProjectConfig, story_text: str, style_prompt: str) -> list[ShotSpec]:
    story = project.story
    assert story is not None
    beats = split_story_into_beats(story_text, max_sentences_per_shot=story.max_sentences_per_shot)
    cast_ids = [character.id for character in project.characters]
    shots: list[ShotSpec] = []
    for index, beat in enumerate(beats, start=1):
        clip_seconds = estimate_clip_seconds(
            beat,
            min_seconds=story.min_clip_seconds,
            max_seconds=story.max_clip_seconds,
        )
        prompt = build_prompt_from_beat(
            beat=beat,
            subject_description=story.subject_description,
            style_prompt=style_prompt,
            index=index,
        )
        shots.append(
            ShotSpec(
                id=f"shot_{index:03d}",
                prompt=prompt,
                init_image=project.characters[0].reference_images[0] if index == 1 and project.characters else story.image,
                clip_seconds=clip_seconds,
                beat_summary=beat,
                narration=beat,
                source_text=beat,
                characters=cast_ids,
                extras_prompt="background extras only, no locked identity, distant crowd silhouettes when needed",
                continuity_note="same main subject and environment continuity",
            )
        )
    return shots
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_storyboard.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ai_video/storyboard.py src/ai_video/models.py tests/test_storyboard.py
git commit -m "feat: add deterministic story to shot planner"
```

### Task 3: Add Character Consistency LoRA Training And Workflow Application

**Files:**
- Create: `src/ai_video/character_lora.py`
- Modify: `src/ai_video/models.py`
- Modify: `src/ai_video/config.py`
- Modify: `src/ai_video/workflow_renderer.py`
- Modify: `workflows/bindings/wan22_i2v_binding.yaml`
- Test: `tests/test_character_lora.py`
- Test: `tests/test_workflow_renderer.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write the failing LoRA tests**

```python
def test_load_project_resolves_character_lora_training_paths(tmp_path: Path):
    refs = tmp_path / "refs"
    refs.mkdir()
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    output_dir = tmp_path / "loras"
    output_dir.mkdir()
    (refs / "hero.png").write_bytes(b"img")
    project_path = tmp_path / "project.yaml"
    project_path.write_text(
        "project_name: lora-demo\n"
        "comfy:\n  base_url: http://127.0.0.1:8188\n"
        "workflow:\n  template: workflows/template.json\n  binding: workflows/binding.yaml\n"
        "characters:\n"
        "  - id: hero\n"
        "    name: Hero\n"
        "    reference_images: [refs/hero.png]\n"
        "    future_lora:\n"
        "      weight: 0.8\n"
        "      training:\n"
        "        dataset_dir: dataset\n"
        "        output_dir: loras\n"
        "        trigger_phrase: hero-token\n"
        "        trainer_command: [python, tools/train_lora.py]\n",
        encoding="utf-8",
    )
    project = load_project(project_path)
    training = project.characters[0].future_lora.training
    assert training is not None
    assert training.dataset_dir == tmp_path / "dataset"
    assert training.output_dir == tmp_path / "loras"


def test_render_workflow_applies_character_lora_paths(tmp_path: Path):
    shot = ShotSpec(id="shot_001", prompt="hero and villain confront each other", characters=["hero", "villain"])
    hero = CharacterProfile.model_validate(
        {
            "id": "hero",
            "name": "Hero",
            "reference_images": [str(tmp_path / "hero.png")],
            "future_lora": {"path": str(tmp_path / "hero.safetensors"), "weight": 0.75},
        }
    )
    villain = CharacterProfile.model_validate(
        {
            "id": "villain",
            "name": "Villain",
            "reference_images": [str(tmp_path / "villain.png")],
            "future_lora": {"path": str(tmp_path / "villain.safetensors"), "weight": 0.65},
        }
    )
    rendered = render_workflow(
        template=workflow_with_lora_slots(),
        binding=binding_with_character_loras(),
        shot=shot,
        defaults=DefaultsConfig(seed=100),
        characters={"hero": hero, "villain": villain},
        shot_index=0,
        chain_image_name="hero.png",
        character_image_names={},
        output_prefix="demo/run/shot_001/attempt_1",
    )
    assert rendered.workflow["565"]["inputs"]["lora_1"] == "hero.safetensors"
    assert rendered.workflow["565"]["inputs"]["strength_1"] == 0.75
    assert rendered.workflow["565"]["inputs"]["lora_2"] == "villain.safetensors"
    assert rendered.workflow["565"]["inputs"]["strength_2"] == 0.65


def test_render_workflow_ignores_extras_for_lora_budget(tmp_path: Path):
    shot = ShotSpec(
        id="shot_001",
        prompt="hero confronts villain in a crowded street",
        characters=["hero", "villain"],
        extras_prompt="ten distant background pedestrians, blurred market crowd",
    )
    hero = CharacterProfile.model_validate(
        {
            "id": "hero",
            "name": "Hero",
            "reference_images": [str(tmp_path / "hero.png")],
            "future_lora": {"path": str(tmp_path / "hero.safetensors"), "weight": 0.75},
        }
    )
    villain = CharacterProfile.model_validate(
        {
            "id": "villain",
            "name": "Villain",
            "reference_images": [str(tmp_path / "villain.png")],
            "future_lora": {"path": str(tmp_path / "villain.safetensors"), "weight": 0.65},
        }
    )
    rendered = render_workflow(
        template=workflow_with_lora_slots(),
        binding=binding_with_character_loras(),
        shot=shot,
        defaults=DefaultsConfig(seed=100),
        characters={"hero": hero, "villain": villain},
        shot_index=0,
        chain_image_name="hero.png",
        character_image_names={},
        output_prefix="demo/run/shot_001/attempt_1",
    )
    assert rendered.workflow["565"]["inputs"]["lora_1"] == "hero.safetensors"
    assert rendered.workflow["565"]["inputs"]["lora_2"] == "villain.safetensors"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_config.py::test_load_project_resolves_character_lora_training_paths tests/test_character_lora.py tests/test_workflow_renderer.py::test_render_workflow_applies_character_lora_paths -v`
Expected: FAIL because training config, multi-character slot allocation, extras-vs-locked-character semantics, and character LoRA bindings do not exist

- [ ] **Step 3: Add training config, trainer wrapper, and workflow binding support**

```python
class CharacterLoraTrainingConfig(BaseModel):
    dataset_dir: Path
    output_dir: Path
    trigger_phrase: str
    trainer_command: list[str]
    steps: int = 1200
    learning_rate: float = 1e-4
    rank: int = 16


class FutureLoraConfig(BaseModel):
    path: Path | None = None
    weight: float | None = None
    training: CharacterLoraTrainingConfig | None = None


class CharacterLoraSlotBinding(BaseModel):
    slot_index: int
    lora_path: JsonPathBinding
    weight_path: JsonPathBinding


class WorkflowBinding(BaseModel):
    ...
    character_lora_slots: list[CharacterLoraSlotBinding] = Field(default_factory=list)
```

```python
def build_lora_training_command(*, training: CharacterLoraTrainingConfig, character: CharacterProfile) -> list[str]:
    return [
        *training.trainer_command,
        "--dataset", str(training.dataset_dir),
        "--output_dir", str(training.output_dir),
        "--trigger", training.trigger_phrase,
        "--steps", str(training.steps),
        "--learning_rate", str(training.learning_rate),
        "--rank", str(training.rank),
    ]


def run_character_lora_training(*, training: CharacterLoraTrainingConfig, character: CharacterProfile) -> Path:
    command = build_lora_training_command(training=training, character=character)
    subprocess.run(command, check=True)
    return training.output_dir / f"{character.id}.safetensors"
```

```python
active_cast = []
for character_id in shot.characters:
    character = characters.get(character_id)
    if character is None or character.future_lora.path is None:
        continue
    active_cast.append(character)

if len(active_cast) > 2:
    raise _fail(
        ErrorCode.CONFIG_INVALID,
        f"Shot {shot.id} uses {len(active_cast)} LoRA-backed characters; MVP limit is 2.",
    )

# extras_prompt affects only prompt composition and never consumes LoRA slots

for slot_binding, character in zip(binding.character_lora_slots, active_cast, strict=False):
    _set_binding_value(
        workflow,
        slot_binding.lora_path,
        character.future_lora.path.name,
        f"character_lora_slots.slot_{slot_binding.slot_index}.path",
    )
    _set_binding_value(
        workflow,
        slot_binding.weight_path,
        character.future_lora.weight or 1.0,
        f"character_lora_slots.slot_{slot_binding.slot_index}.weight",
    )
```

```yaml
character_lora_slots:
  - slot_index: 1
    lora_path:
      paths:
        - ["565", "inputs", "lora_1"]
        - ["564", "inputs", "lora_1"]
    weight_path:
      paths:
        - ["565", "inputs", "strength_1"]
        - ["564", "inputs", "strength_1"]
  - slot_index: 2
    lora_path:
      paths:
        - ["565", "inputs", "lora_2"]
        - ["564", "inputs", "lora_2"]
    weight_path:
      paths:
        - ["565", "inputs", "strength_2"]
        - ["564", "inputs", "strength_2"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_config.py::test_load_project_resolves_character_lora_training_paths tests/test_character_lora.py tests/test_workflow_renderer.py::test_render_workflow_applies_character_lora_paths -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ai_video/character_lora.py src/ai_video/models.py src/ai_video/config.py src/ai_video/workflow_renderer.py workflows/bindings/wan22_i2v_binding.yaml tests/test_character_lora.py tests/test_workflow_renderer.py tests/test_config.py
git commit -m "feat: add character lora training and workflow injection"
```

### Task 4: Add Draft Command, LoRA Training Command, And Story-Driven Shot Materialization

**Files:**
- Modify: `src/ai_video/cli.py`
- Create: `src/ai_video/storyboard.py`
- Create: `src/ai_video/character_lora.py`
- Modify: `src/ai_video/config.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing CLI tests**

```python
def test_draft_story_writes_generated_shots(tmp_path, capsys):
    project_path = write_story_project(tmp_path)
    output_path = tmp_path / "generated.shots.yaml"
    code = main(["draft-story", "--project", str(project_path), "--output", str(output_path)])
    captured = capsys.readouterr()
    assert code == 0
    assert output_path.exists()
    assert "shot_001" in output_path.read_text(encoding="utf-8")
    assert "drafted" in captured.out.lower()


def test_run_uses_project_story_when_shots_omitted(tmp_path, monkeypatch):
    project_path = write_story_project(tmp_path)
    captured = {}

    class FakeRunner:
        def __init__(self, project, shots, binding, template, progress_callback=None):
            captured["shot_count"] = len(shots)
        def run(self, **kwargs):
            captured["project_config_path"] = kwargs["project_config_path"]
            captured["shot_list_path"] = kwargs["shot_list_path"]
            return SimpleNamespace(final_output="runs/demo/final/final.mp4")

    monkeypatch.setattr("ai_video.cli.PipelineRunner", FakeRunner)
    code = main(["run", "--project", str(project_path), "--run-id", "story-run"])
    assert code == 0
    assert captured["shot_count"] >= 1
    assert Path(captured["shot_list_path"]).name.endswith(".generated.shots.yaml")


def test_train_character_lora_runs_configured_trainer(tmp_path, monkeypatch, capsys):
    project_path = write_story_project_with_character_lora(tmp_path)
    calls = {}

    def fake_run_character_lora_training(*, training, character):
        calls["character"] = character.id
        calls["trigger"] = training.trigger_phrase
        return tmp_path / "loras" / "hero.safetensors"

    monkeypatch.setattr("ai_video.cli.run_character_lora_training", fake_run_character_lora_training)
    code = main(["train-character-lora", "--project", str(project_path), "--character", "hero"])
    captured = capsys.readouterr()
    assert code == 0
    assert calls["character"] == "hero"
    assert "hero.safetensors" in captured.out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cli.py::test_draft_story_writes_generated_shots tests/test_cli.py::test_run_uses_project_story_when_shots_omitted tests/test_cli.py::test_train_character_lora_runs_configured_trainer -v`
Expected: FAIL because `draft-story` / `train-character-lora` do not exist and `run` requires `--shots`

- [ ] **Step 3: Implement additive story drafting path**

```python
def _materialize_story_shots(project: ProjectConfig, *, target: Path | None) -> tuple[list[ShotSpec], Path | None]:
    if project.story is None:
        return [], None
    story_text = project.story.text_path.read_text(encoding="utf-8")
    shots = build_shots_from_story(
        project=project,
        story_text=story_text,
        style_prompt=project.defaults.style_prompt,
    )
    if target is not None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(yaml.safe_dump({"shots": [shot.model_dump(mode="json") for shot in shots]}, sort_keys=False), encoding="utf-8")
    return shots, target


def _cmd_draft_story(args: argparse.Namespace) -> int:
    project = load_project(args.project)
    if project.story is None:
        print("Project is missing story config.", file=sys.stderr)
        return 1
    shots, output_path = _materialize_story_shots(project, target=Path(args.output))
    print(f"Drafted {len(shots)} shots to {output_path}")
    return 0


def _cmd_train_character_lora(args: argparse.Namespace) -> int:
    project = load_project(args.project)
    character = next((c for c in project.characters if c.id == args.character), None)
    if character is None or character.future_lora.training is None:
        print("Character is missing LoRA training config.", file=sys.stderr)
        return 1
    artifact = run_character_lora_training(
        training=character.future_lora.training,
        character=character,
    )
    print(f"Character LoRA trained: {artifact}")
    return 0
```

```python
draft_story = subcommands.add_parser("draft-story")
draft_story.add_argument("--project", required=True)
draft_story.add_argument("--output", required=True)
draft_story.set_defaults(func=_cmd_draft_story)

train_character_lora = subcommands.add_parser("train-character-lora")
train_character_lora.add_argument("--project", required=True)
train_character_lora.add_argument("--character", required=True)
train_character_lora.set_defaults(func=_cmd_train_character_lora)

run = subcommands.add_parser("run")
run.add_argument("--project", required=True)
run.add_argument("--shots")
...
if args.shots is None and project.story is not None:
    generated_path = project.output.root / "_generated" / f"{project.project_name}.generated.shots.yaml"
    shots, generated_path = _materialize_story_shots(project, target=generated_path)
else:
    shots = load_shots(args.shots, project)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cli.py::test_draft_story_writes_generated_shots tests/test_cli.py::test_run_uses_project_story_when_shots_omitted tests/test_cli.py::test_train_character_lora_runs_configured_trainer -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ai_video/cli.py src/ai_video/storyboard.py src/ai_video/character_lora.py tests/test_cli.py
git commit -m "feat: add story drafting and character lora cli flow"
```

### Task 5: Add Local Narration Audio Pipeline

**Files:**
- Create: `src/ai_video/audio.py`
- Modify: `src/ai_video/ffmpeg_tools.py`
- Test: `tests/test_audio.py`
- Test: `tests/test_ffmpeg_tools.py`

- [ ] **Step 1: Write the failing audio tests**

```python
def test_build_narration_track_synthesizes_segments(tmp_path, monkeypatch):
    calls = []

    class FakeTTS:
        def save_to_file(self, text, path):
            calls.append((text, Path(path)))
        def runAndWait(self):
            pass
        def setProperty(self, name, value):
            pass

    monkeypatch.setattr("ai_video.audio.pyttsx3.init", lambda: FakeTTS())
    shots = [
        ShotSpec(id="shot_001", prompt="x", narration="Line one", clip_seconds=3),
        ShotSpec(id="shot_002", prompt="y", narration="Line two", clip_seconds=4),
    ]
    plan = build_narration_track(shots=shots, output_dir=tmp_path, voice="default", rate=180)
    assert len(calls) == 2
    assert plan.segments[0].text == "Line one"
    assert plan.final_audio_path.name == "narration.wav"


def test_mix_video_with_audio_invokes_ffmpeg(tmp_path, monkeypatch):
    video = tmp_path / "video.mp4"
    audio = tmp_path / "audio.wav"
    output = tmp_path / "final.mp4"
    video.write_bytes(b"video")
    audio.write_bytes(b"audio")
    commands = []
    monkeypatch.setattr("ai_video.ffmpeg_tools._run", lambda args: commands.append(args))
    mux_video_with_audio(video, audio, output)
    assert commands
    assert commands[0][-1] == str(output)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_audio.py tests/test_ffmpeg_tools.py::test_mix_video_with_audio_invokes_ffmpeg -v`
Expected: FAIL because audio helpers do not exist

- [ ] **Step 3: Implement local narration and mux**

```python
@dataclass
class NarrationSegment:
    shot_id: str
    text: str
    clip_seconds: int
    audio_path: Path


@dataclass
class NarrationPlan:
    segments: list[NarrationSegment]
    final_audio_path: Path


def build_narration_track(*, shots: Sequence[ShotSpec], output_dir: Path, voice: str, rate: int) -> NarrationPlan:
    engine = pyttsx3.init()
    engine.setProperty("rate", rate)
    if voice != "default":
        engine.setProperty("voice", voice)
    output_dir.mkdir(parents=True, exist_ok=True)
    segments: list[NarrationSegment] = []
    for shot in shots:
        if not shot.narration.strip():
            continue
        audio_path = output_dir / f"{shot.id}.wav"
        engine.save_to_file(shot.narration, str(audio_path))
        segments.append(NarrationSegment(shot.id=shot.id, text=shot.narration, clip_seconds=shot.clip_seconds or 0, audio_path=audio_path))
    engine.runAndWait()
    final_audio = output_dir / "narration.wav"
    concatenate_audio_segments([segment.audio_path for segment in segments], final_audio)
    return NarrationPlan(segments=segments, final_audio_path=final_audio)
```

```python
def mux_video_with_audio(video_path: str | Path, audio_path: str | Path, output_path: str | Path) -> None:
    _run(
        [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(output_path),
        ]
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_audio.py tests/test_ffmpeg_tools.py::test_mix_video_with_audio_invokes_ffmpeg -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ai_video/audio.py src/ai_video/ffmpeg_tools.py tests/test_audio.py tests/test_ffmpeg_tools.py
git commit -m "feat: add local narration audio pipeline"
```

### Task 6: Integrate Audio Into Pipeline And Manifest

**Files:**
- Modify: `src/ai_video/pipeline.py`
- Modify: `src/ai_video/manifest.py`
- Modify: `tests/test_pipeline.py`
- Modify: `tests/test_resume_e2e.py`

- [ ] **Step 1: Write the failing pipeline tests**

```python
def test_pipeline_muxes_final_audio_when_narration_enabled(example_project_and_shots, tmp_path):
    project, shots, binding, template = example_project_and_shots
    project.audio = AudioConfig(narration_enabled=True)
    shots[0].narration = "Line one"
    shots[1].narration = "Line two"

    class FakeAudio:
        def build_narration_track(self, *, shots, output_dir, voice, rate):
            audio = output_dir / "narration.wav"
            audio.parent.mkdir(parents=True, exist_ok=True)
            audio.write_bytes(b"audio")
            return NarrationPlan(segments=[], final_audio_path=audio)

    class FakeFfmpegWithAudio(FakeFfmpeg):
        def mux_video_with_audio(self, video_path, audio_path, output_path):
            output_path.write_bytes(b"muxed")

    runner = PipelineRunner(
        project, shots, binding, template,
        comfy=FakeComfy(),
        ffmpeg=FakeFfmpegWithAudio(),
        audio=FakeAudio(),
    )
    manifest = runner.run(run_id="run-audio")
    assert manifest.final_output.endswith("final.mp4")
    assert manifest.final_audio_path is not None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_pipeline.py::test_pipeline_muxes_final_audio_when_narration_enabled -v`
Expected: FAIL because pipeline has no audio integration

- [ ] **Step 3: Add audio-aware pipeline finalization**

```python
class PipelineRunner:
    def __init__(..., audio: Any | None = None):
        ...
        self.audio = audio or audio_tools

    def _finalize_audio(self, manifest: RunManifest, run_root: Path) -> None:
        if self.project.audio is None or not self.project.audio.narration_enabled:
            return
        narration_plan = self.audio.build_narration_track(
            shots=self.shots,
            output_dir=run_root / "audio",
            voice=self.project.audio.voice,
            rate=self.project.audio.rate,
        )
        muxed_output = run_root / "final" / "final_with_audio.mp4"
        self.ffmpeg.mux_video_with_audio(manifest.final_output, narration_plan.final_audio_path, muxed_output)
        manifest.final_audio_path = str(narration_plan.final_audio_path)
        manifest.final_output = str(muxed_output)
```

```python
class RunManifest(BaseModel):
    ...
    final_audio_path: str | None = None
    generated_shot_list_path: str | None = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_pipeline.py::test_pipeline_muxes_final_audio_when_narration_enabled tests/test_resume_e2e.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ai_video/pipeline.py src/ai_video/manifest.py tests/test_pipeline.py tests/test_resume_e2e.py
git commit -m "feat: mux narration into final video output"
```

### Task 7: Document And Verify End-To-End Story Flow

**Files:**
- Modify: `README.md`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_pipeline.py`

- [ ] **Step 1: Add end-to-end CLI regression tests**

```python
def test_story_draft_then_run_flow(tmp_path, monkeypatch, capsys):
    project_path = write_story_project(tmp_path)
    generated = tmp_path / "story.generated.shots.yaml"
    assert main(["draft-story", "--project", str(project_path), "--output", str(generated)]) == 0
    assert generated.exists()
    code = main(["validate", "--project", str(project_path), "--shots", str(generated)])
    assert code == 0
```

- [ ] **Step 2: Run tests to verify they fail if docs/flow mismatch**

Run: `pytest tests/test_cli.py::test_story_draft_then_run_flow -v`
Expected: PASS only after Task 4 exists; if failing, fix integration before docs

- [ ] **Step 3: Update README with the new flow**

```markdown
## Story-Driven Flow

1. Put one reference image on disk.
2. Put your story excerpt in a UTF-8 `.txt` file.
3. Add `story:` and `audio:` blocks to the project config.
4. Draft shots:

```bash
ai-video draft-story --project configs/story.project.yaml --output configs/story.generated.shots.yaml
```

5. Validate and run:

```bash
ai-video validate --project configs/story.project.yaml --shots configs/story.generated.shots.yaml
ai-video run --project configs/story.project.yaml --shots configs/story.generated.shots.yaml --run-id story-demo
```
```

- [ ] **Step 4: Run the full targeted suite**

Run: `pytest tests/test_config.py tests/test_storyboard.py tests/test_audio.py tests/test_cli.py tests/test_pipeline.py tests/test_resume_e2e.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add README.md tests/test_cli.py tests/test_storyboard.py tests/test_audio.py tests/test_pipeline.py
git commit -m "docs: add story to film workflow and coverage"
```

## Self-Review

- Spec coverage:
  - Single image input and multi-character cast input: covered in Tasks 1-3 via `story.image` and `characters[]`.
  - Story excerpt to automatic shot splitting: covered in Task 2.
  - Automatic prompt generation: covered in Task 2.
  - Character consistency via trainable LoRA: covered in Tasks 1, 3, and 4.
  - Multi-character per-shot casting with VRAM-aware slot limits: covered in Tasks 2, 3, and 4.
  - Background extras that do not consume LoRA slots: covered in Tasks 1, 2, and 3 via `extras_prompt` and render-time slot budgeting.
  - Generated film output: existing pipeline reused, integrated in Tasks 4 and 6.
  - Sound in final video: covered in Tasks 5 and 6.
- Placeholder scan:
  - No `TODO` / `TBD` markers remain.
  - Every task contains files, commands, and concrete code direction.
- Type consistency:
  - `StorySourceConfig`, `AudioConfig`, `ShotSpec.narration`, `RunManifest.final_audio_path`, and `generated_shot_list_path` are referenced consistently across tasks.

## Execution Order Recommendation

1. Task 1
2. Task 2
3. Task 3
4. Task 4
5. Task 5
6. Task 6
7. Task 7

Plan complete and saved to `docs/superpowers/plans/2026-05-02-image-story-to-film-audio.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
