# Code Rot Report

> **REPORT READY** — The real project was not changed.

Project: `/home/reggie/vscode_folder/AI-VIDEO`  
Generated: `2026-10-20T16:10:33Z`

## Executive summary

| Result | Candidates | LOC | Size |
|---|---:|---:|---:|
| SAFE TO REMOVE | 0 | 0 | 0 B |
| REVIEW | 2 | 16 | 682 B |
| KEEP | 323 | 120,333 | 4.9 MB |

## Ranked candidates

| ID | Status | Category | Subject | Confidence | Risk | LOC | Proof |
|---|---|---|---|---|---|---:|---|
| CRT-001 | **KEEP** | orphan-file | `provider-console/src/continuity-review-contract.js` | medium | medium | 64 | KEEP: continuity-review.js:2-5 multiline-imports this module and re-exports it at lines 8-14; provider-console/tests/continuity-review-contract.test.mjs also imports it. Bundled regex misses multiline imports. |
| CRT-002 | **KEEP** | orphan-file | `src/ai_video/agent_memory/chunking.py` | medium | medium | 94 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/agent_memory/index.py, tests/test_agent_memory.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-003 | **KEEP** | orphan-file | `src/ai_video/agent_memory/config.py` | medium | medium | 79 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/agent_memory.py, src/ai_video/agent_memory/__init__.py, src/ai_video/agent_memory/embeddings.py and 5 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-004 | **KEEP** | orphan-file | `src/ai_video/agent_memory/corpus.py` | medium | medium | 435 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/agent_memory.py, src/ai_video/agent_memory/__init__.py, src/ai_video/agent_memory/index.py and 4 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-005 | **KEEP** | orphan-file | `src/ai_video/agent_memory/embeddings.py` | medium | medium | 235 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/agent_memory.py, src/ai_video/agent_memory/__init__.py, src/ai_video/agent_memory/manifest.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-006 | **KEEP** | orphan-file | `src/ai_video/agent_memory/hybrid.py` | medium | medium | 143 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/agent_memory/retrieval.py, tests/test_agent_memory.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-007 | **KEEP** | orphan-file | `src/ai_video/agent_memory/index.py` | medium | medium | 546 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/agent_memory.py, src/ai_video/agent_memory/__init__.py, src/ai_video/agent_memory/layout.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-008 | **KEEP** | orphan-file | `src/ai_video/agent_memory/layout.py` | medium | medium | 214 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/agent_memory.py, src/ai_video/agent_memory/__init__.py, src/ai_video/agent_memory/retrieval.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-009 | **KEEP** | orphan-file | `src/ai_video/agent_memory/maintenance.py` | medium | medium | 327 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/agent_memory.py, tests/test_agent_memory.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-010 | **KEEP** | orphan-file | `src/ai_video/agent_memory/manifest.py` | medium | medium | 280 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/agent_memory.py, src/ai_video/agent_memory/__init__.py, src/ai_video/agent_memory/index.py and 3 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-011 | **KEEP** | orphan-file | `src/ai_video/agent_memory/retrieval.py` | medium | medium | 954 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/agent_memory.py, src/ai_video/agent_memory/__init__.py, tests/test_agent_memory.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-012 | **KEEP** | orphan-file | `src/ai_video/canvas_assets.py` | medium | medium | 81 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py, src/ai_video/canvas_project_data.py, tests/test_canvas_assets.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-013 | **KEEP** | orphan-file | `src/ai_video/canvas_authoring.py` | medium | medium | 269 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_assets.py, src/ai_video/canvas_preflight.py, src/ai_video/canvas_production.py and 11 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-014 | **KEEP** | orphan-file | `src/ai_video/canvas_composition.py` | medium | medium | 174 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py, tests/test_canvas_edit_first.py, tests/test_canvas_native_audio_retime.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-015 | **KEEP** | orphan-file | `src/ai_video/canvas_dependencies.py` | medium | medium | 148 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_image.py, src/ai_video/canvas_production.py, tests/test_canvas_masked_image_workflow.py and 5 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-016 | **KEEP** | orphan-file | `src/ai_video/canvas_external_image.py` | medium | medium | 23 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_production_source.py, scripts/canvas_sequence_packet.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-017 | **KEEP** | orphan-file | `src/ai_video/canvas_handoff.py` | medium | medium | 255 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_planning.py, src/ai_video/canvas_production.py, src/ai_video/canvas_source_expression.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-018 | **KEEP** | orphan-file | `src/ai_video/canvas_image.py` | medium | medium | 23 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_canvas_masked_image_workflow.py, tests/test_image_candidate_frontier.py, tests/test_seedream_remote_image.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-019 | **KEEP** | orphan-file | `src/ai_video/canvas_image_workflow.py` | medium | medium | 59 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-020 | **KEEP** | orphan-file | `src/ai_video/canvas_planning.py` | medium | medium | 244 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py, src/ai_video/canvas_visual_style.py, tests/test_canvas_continuity.py and 4 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-021 | **KEEP** | orphan-file | `src/ai_video/canvas_preflight.py` | medium | medium | 162 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_production.py, tests/test_canvas_continuity.py, tests/test_canvas_project_data.py and 3 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-022 | **KEEP** | orphan-file | `src/ai_video/canvas_production.py` | medium | medium | 741 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_project_data.py, tests/test_canvas_assets.py, tests/test_canvas_continuity.py and 12 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-023 | **KEEP** | orphan-file | `src/ai_video/canvas_project_data.py` | medium | medium | 191 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_production.py, tests/test_canvas_external_image.py, tests/test_canvas_imported_audio_retime.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-024 | **KEEP** | orphan-file | `src/ai_video/canvas_recovery.py` | medium | medium | 239 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py, tests/test_canvas_recovery.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-025 | **KEEP** | orphan-file | `src/ai_video/canvas_review.py` | medium | medium | 194 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_authoring.py, src/ai_video/canvas_handoff.py, src/ai_video/canvas_production.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-026 | **KEEP** | orphan-file | `src/ai_video/canvas_source_expression.py` | medium | medium | 233 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_authoring.py, src/ai_video/canvas_handoff.py, src/ai_video/canvas_project_data.py and 3 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-027 | **KEEP** | orphan-file | `src/ai_video/canvas_source_revision.py` | medium | medium | 188 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_authoring.py, src/ai_video/canvas_production.py, tests/test_canvas_continuity.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-028 | **KEEP** | orphan-file | `src/ai_video/canvas_subject.py` | medium | medium | 36 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_production_source.py, scripts/canvas_sequence_packet.py, src/ai_video/canvas_assets.py and 3 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-029 | **KEEP** | orphan-file | `src/ai_video/canvas_target_gate.py` | medium | medium | 53 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_planning.py, src/ai_video/canvas_production.py, tests/test_canvas_continuity.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-030 | **KEEP** | orphan-file | `src/ai_video/canvas_visual_style.py` | medium | medium | 369 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_authoring.py, src/ai_video/canvas_preflight.py, src/ai_video/canvas_production.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-031 | **KEEP** | orphan-file | `src/ai_video/cli.py` | medium | medium | 111 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_cli.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-032 | **KEEP** | orphan-file | `src/ai_video/comfy_client.py` | medium | medium | 281 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/pipeline.py, src/ai_video/production/comfy_image.py, src/ai_video/production/comfy_t8_native_turbo_video.py and 16 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-033 | **KEEP** | orphan-file | `src/ai_video/config.py` | medium | medium | 131 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/cli.py, src/ai_video/manifest.py, src/ai_video/pipeline.py and 10 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-034 | **KEEP** | orphan-file | `src/ai_video/errors.py` | medium | medium | 101 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/agent_harness_canvas_data.py, scripts/canvas_production.py, scripts/execute_shot_continuity_source.py and 314 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-035 | **KEEP** | orphan-file | `src/ai_video/ffmpeg_tools.py` | medium | medium | 187 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/pipeline.py, src/ai_video/production/video_artifact.py, tests/test_ffmpeg_tools.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-036 | **KEEP** | orphan-file | `src/ai_video/manifest.py` | medium | medium | 159 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/cli.py, src/ai_video/pipeline.py, src/ai_video/provider_console.py and 7 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-037 | **KEEP** | orphan-file | `src/ai_video/models.py` | medium | medium | 140 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/cli.py, src/ai_video/config.py, src/ai_video/pipeline.py and 6 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-038 | **KEEP** | orphan-file | `src/ai_video/pipeline.py` | medium | medium | 661 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/cli.py, tests/test_pipeline.py, tests/test_resume_e2e.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-039 | **KEEP** | orphan-file | `src/ai_video/planning/_asset_readiness.py` | medium | medium | 314 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/_current_plan_projection.py, src/ai_video/planning/video_planner.py, src/ai_video/quality_gates/shot_readiness_gate.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-040 | **KEEP** | orphan-file | `src/ai_video/planning/_commercial_video_planning.py` | medium | medium | 217 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/__init__.py, src/ai_video/planning/video_planner.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-041 | **KEEP** | orphan-file | `src/ai_video/planning/_current_plan_projection.py` | medium | medium | 201 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/video_planner.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-042 | **KEEP** | orphan-file | `src/ai_video/planning/_planner_models.py` | medium | medium | 613 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/composition_playbooks.py, scripts/composition_shadow.py, src/ai_video/planning/__init__.py and 7 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-043 | **KEEP** | orphan-file | `src/ai_video/planning/generation_difficulty.py` | medium | medium | 39 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/video_planner.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-044 | **KEEP** | orphan-file | `src/ai_video/planning/generation_feedback_context.py` | medium | medium | 41 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/generation_feedback_driver.py, scripts/s01_strategy_regression.py, src/ai_video/canvas_planning.py and 3 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-045 | **KEEP** | orphan-file | `src/ai_video/planning/production_strategy.py` | medium | medium | 284 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/s01_strategy_regression.py, src/ai_video/production_planning.py, tests/test_canvas_production.py and 6 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-046 | **KEEP** | orphan-file | `src/ai_video/planning/sequence_continuity.py` | medium | medium | 256 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_sequence_handoff.py, src/ai_video/canvas_planning.py, src/ai_video/planning/__init__.py and 3 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-047 | **KEEP** | orphan-file | `src/ai_video/planning/video_planner.py` | medium | medium | 896 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_sequence_handoff.py, src/ai_video/planning/__init__.py, src/ai_video/planning/sequence_continuity.py and 9 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-048 | **KEEP** | orphan-file | `src/ai_video/production/_asset_registry_validation.py` | medium | medium | 211 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/models.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-049 | **KEEP** | orphan-file | `src/ai_video/production/_caption_quality_p6.py` | medium | medium | 378 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/ecommerce_ad_coordinator.py, src/ai_video/production/ecommerce_job_review.py, tests/production_e2e_support.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-050 | **KEEP** | orphan-file | `src/ai_video/production/_caption_review_models.py` | medium | medium | 157 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/models.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-051 | **KEEP** | orphan-file | `src/ai_video/production/_causal_prompt_context.py` | medium | medium | 97 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_causal_state_expression.py, src/ai_video/production/_sequence_source.py, src/ai_video/production/seedance_source_expression.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-052 | **KEEP** | orphan-file | `src/ai_video/production/_causal_state_expression.py` | medium | medium | 91 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_h3_prompt.py, src/ai_video/production/_remote_video_native_prompt.py, src/ai_video/production/generation_evaluation.py and 5 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-053 | **KEEP** | orphan-file | `src/ai_video/production/_commercial_project_reader.py` | medium | medium | 515 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/_commercial_video_planning.py, src/ai_video/production/_state_commit_dependency.py, src/ai_video/production/commercial_video_validation.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-054 | **KEEP** | orphan-file | `src/ai_video/production/_commercial_source_state.py` | medium | medium | 170 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_provider_manifest_fields.py, src/ai_video/production/models.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-055 | **KEEP** | orphan-file | `src/ai_video/production/_composition_native_audio.py` | medium | medium | 193 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/composition.py, tests/test_canvas_imported_audio_retime.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-056 | **KEEP** | orphan-file | `src/ai_video/production/_composition_source_duration.py` | medium | medium | 57 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/composition.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-057 | **KEEP** | orphan-file | `src/ai_video/production/_composition_visual.py` | medium | medium | 280 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/composition.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-058 | **KEEP** | orphan-file | `src/ai_video/production/_creative_project_reader.py` | medium | medium | 60 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/project.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-059 | **KEEP** | orphan-file | `src/ai_video/production/_dependency_authoring.py` | medium | medium | 334 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_dependencies.py, src/ai_video/production/dependency.py, src/ai_video/production/minimax_speech_batch.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-060 | **KEEP** | orphan-file | `src/ai_video/production/_dependency_primitives.py` | medium | medium | 27 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_dependency_authoring.py, src/ai_video/production/dependency.py, src/ai_video/production/video_pre_generation.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-061 | **KEEP** | orphan-file | `src/ai_video/production/_dependency_types.py` | medium | medium | 13 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/models.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-062 | **KEEP** | orphan-file | `src/ai_video/production/_ecommerce_quality_gate_p6.py` | medium | medium | 388 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/ecommerce_ad_coordinator.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-063 | **KEEP** | orphan-file | `src/ai_video/production/_generation_history_schema.py` | medium | medium | 38 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/models.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-064 | **KEEP** | orphan-file | `src/ai_video/production/_grok_auth_lock.py` | medium | medium | 46 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/grok_auth.py, tests/test_grok_auth.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-065 | **KEEP** | orphan-file | `src/ai_video/production/_h3_prompt.py` | medium | medium | 598 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/comfy_t8_native_turbo_video.py, src/ai_video/production/comfy_t8_turbo_video.py, src/ai_video/production/comfy_t8_video.py and 6 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-066 | **KEEP** | orphan-file | `src/ai_video/production/_hyperframes_audio.py` | medium | medium | 238 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/hyperframes.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-067 | **KEEP** | orphan-file | `src/ai_video/production/_hyperframes_native_audio.py` | medium | medium | 631 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/hyperframes.py, tests/test_canvas_imported_audio_retime.py, tests/test_hyperframes_native_audio_retime.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-068 | **KEEP** | orphan-file | `src/ai_video/production/_hyperframes_source.py` | medium | medium | 709 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/hyperframes.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-069 | **KEEP** | orphan-file | `src/ai_video/production/_image_project_reader.py` | medium | medium | 1149 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_image_activation.py, src/ai_video/production/_state_commit_image_recovery.py, src/ai_video/production/_state_commit_video.py and 8 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-070 | **KEEP** | orphan-file | `src/ai_video/production/_image_video_lineage.py` | medium | medium | 173 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_image_project_reader.py, tests/test_production_generated_video_e2e.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-071 | **KEEP** | orphan-file | `src/ai_video/production/_immutable_models.py` | medium | medium | 15 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/domain_acceptance.py, src/ai_video/production/models.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-072 | **KEEP** | orphan-file | `src/ai_video/production/_lifecycle_schema.py` | medium | medium | 1579 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py, src/ai_video/production/_generation_feedback_reader.py, src/ai_video/production/_generation_history_schema.py and 15 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-073 | **KEEP** | orphan-file | `src/ai_video/production/_paid_provider_project_reader.py` | medium | medium | 605 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/_remote_image_reader.py, src/ai_video/production/_state_commit_paid_provider.py and 10 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-074 | **KEEP** | orphan-file | `src/ai_video/production/_project_dependency_evidence.py` | medium | medium | 219 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/project.py, tests/test_production_project.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-075 | **KEEP** | orphan-file | `src/ai_video/production/_provider_manifest_fields.py` | medium | medium | 27 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/models.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-076 | **KEEP** | orphan-file | `src/ai_video/production/_remote_image_reader.py` | medium | medium | 120 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_image_project_reader.py, src/ai_video/production/_state_commit_image_candidate.py, src/ai_video/production/_state_commit_paid_provider.py and 3 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-077 | **KEEP** | orphan-file | `src/ai_video/production/_remote_video_native_prompt.py` | medium | medium | 371 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_vidu_prompt.py, src/ai_video/production/grok.py, src/ai_video/production/metaso_h3.py and 11 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-078 | **KEEP** | orphan-file | `src/ai_video/production/_remote_video_product_prompt.py` | medium | medium | 18 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_remote_video_native_prompt.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-079 | **KEEP** | orphan-file | `src/ai_video/production/_render_source_validation.py` | medium | medium | 117 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/project.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-080 | **KEEP** | orphan-file | `src/ai_video/production/_repair_freshness.py` | medium | medium | 44 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_transaction.py, src/ai_video/quality_intelligence/_capture_p6.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-081 | **KEEP** | orphan-file | `src/ai_video/production/_review_project_reader.py` | medium | medium | 118 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/project.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-082 | **KEEP** | orphan-file | `src/ai_video/production/_sequence_source.py` | medium | medium | 316 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_composition.py, src/ai_video/canvas_handoff.py, src/ai_video/canvas_planning.py and 11 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-083 | **KEEP** | orphan-file | `src/ai_video/production/_shot_router_contracts.py` | medium | medium | 1034 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/generation_feedback_driver.py, src/ai_video/canvas_planning.py, src/ai_video/planning/sequence_continuity.py and 10 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-084 | **KEEP** | orphan-file | `src/ai_video/production/_shot_visual_resolver.py` | medium | medium | 11 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/shot_router.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-085 | **KEEP** | orphan-file | `src/ai_video/production/_state_lifecycle.py` | medium | medium | 15 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/models.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-086 | **KEEP** | orphan-file | `src/ai_video/production/_video_capability_fingerprint.py` | medium | medium | 140 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_video_requirement_routing.py, src/ai_video/production/shot_router.py, src/ai_video/production/video.py and 9 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-087 | **KEEP** | orphan-file | `src/ai_video/production/_video_continuity.py` | medium | medium | 760 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/sequence_continuity.py, src/ai_video/production/shot_continuity_m0_operator.py, src/ai_video/production/shot_continuity_motion_tail.py and 9 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-088 | **KEEP** | orphan-file | `src/ai_video/production/_video_hero_routing.py` | medium | medium | 12 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/shot_router.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-089 | **KEEP** | orphan-file | `src/ai_video/production/_video_intent_validation.py` | medium | medium | 400 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/video_planner.py, src/ai_video/production/_h3_prompt.py, src/ai_video/production/_remote_video_native_prompt.py and 7 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-090 | **KEEP** | orphan-file | `src/ai_video/production/_video_project_reader.py` | medium | medium | 1569 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_commercial_project_reader.py, src/ai_video/production/_generation_feedback_reader.py, src/ai_video/production/_image_project_reader.py and 24 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-091 | **KEEP** | orphan-file | `src/ai_video/production/_video_requirement_routing.py` | medium | medium | 786 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_source_expression.py, src/ai_video/canvas_visual_style.py, src/ai_video/production/_shot_router_contracts.py and 8 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-092 | **KEEP** | orphan-file | `src/ai_video/production/_vidu_prompt.py` | medium | medium | 280 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_vidu_subjects.py, src/ai_video/production/vidu.py, tests/test_production_vidu_prompt.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-093 | **KEEP** | orphan-file | `src/ai_video/production/_vidu_subjects.py` | medium | medium | 66 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/generation_execution.py, src/ai_video/production/video_compiler.py, src/ai_video/production/vidu.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-094 | **KEEP** | orphan-file | `src/ai_video/production/_voice_project_reader.py` | medium | medium | 264 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_paid_provider.py, src/ai_video/production/_state_commit_voice_intent.py, src/ai_video/production/project.py and 3 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-095 | **KEEP** | orphan-file | `src/ai_video/production/ad_composition.py` | medium | medium | 84 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_composition_visual.py, src/ai_video/production/composition.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-096 | **KEEP** | orphan-file | `src/ai_video/production/ad_creative.py` | medium | medium | 345 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, tests/test_production_delivery_packager.py, tests/test_production_ecommerce_job.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-097 | **KEEP** | orphan-file | `src/ai_video/production/ad_creative_review.py` | medium | medium | 330 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-098 | **KEEP** | orphan-file | `src/ai_video/production/ad_creative_types.py` | medium | medium | 472 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/_ecommerce_quality_gate_p6.py, src/ai_video/production/ad_creative.py and 18 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-099 | **KEEP** | orphan-file | `src/ai_video/production/artifact_contracts.py` | medium | medium | 51 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/creative_goal_binding.py, scripts/visual_quality_report.py, src/ai_video/canvas_source_revision.py and 68 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-100 | **KEEP** | orphan-file | `src/ai_video/production/audio.py` | medium | medium | 1270 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/minimax_speech_batch.py, src/ai_video/production/__init__.py, src/ai_video/production/_generated_video_audio_contracts.py and 32 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-101 | **KEEP** | orphan-file | `src/ai_video/production/audio_retime_contracts.py` | medium | medium | 89 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_composition_native_audio.py, src/ai_video/production/_hyperframes_native_audio.py, src/ai_video/production/_render_source_validation.py and 4 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-102 | **KEEP** | orphan-file | `src/ai_video/production/authoring_input.py` | medium | medium | 35 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_authoring.py, src/ai_video/canvas_image_provenance.py, src/ai_video/canvas_project_data.py and 7 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-103 | **KEEP** | orphan-file | `src/ai_video/production/caption_quality.py` | medium | medium | 520 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_caption_quality_p6.py, src/ai_video/production/_review_project_reader.py, src/ai_video/production/_state_commit_repair.py and 5 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-104 | **KEEP** | orphan-file | `src/ai_video/production/caption_quality_contracts.py` | medium | medium | 314 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_caption_quality_p6.py, src/ai_video/production/_caption_review_models.py, src/ai_video/production/caption_quality.py and 7 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-105 | **KEEP** | orphan-file | `src/ai_video/production/captions.py` | medium | medium | 844 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_contracts.py, src/ai_video/production/_state_commit_voice_candidate.py, src/ai_video/production/caption_quality.py and 18 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-106 | **KEEP** | orphan-file | `src/ai_video/production/comfy_image.py` | medium | medium | 702 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/check_p7_1_comfy_compatibility.py, scripts/smoke_p7_1_local_image.py, src/ai_video/canvas_image_workflow.py and 16 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-107 | **KEEP** | orphan-file | `src/ai_video/production/comfy_image_workflow_contract.py` | medium | medium | 304 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/comfy_image.py, tests/test_production_comfy_masked_image.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-108 | **KEEP** | orphan-file | `src/ai_video/production/comfy_t8_native_turbo_profile.py` | medium | medium | 685 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/comfy_t8_native_turbo_video.py, tests/test_production_comfy_t8_native_long_video.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-109 | **KEEP** | orphan-file | `src/ai_video/production/comfy_t8_native_turbo_video.py` | medium | medium | 740 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/video_compiler.py, tests/test_generation_local_wiring.py and 4 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-110 | **KEEP** | orphan-file | `src/ai_video/production/comfy_t8_turbo_video.py` | medium | medium | 833 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, tests/test_production_comfy_t8_turbo_video.py, tests/test_production_local_h3_provider_family.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-111 | **KEEP** | orphan-file | `src/ai_video/production/comfy_t8_video.py` | medium | medium | 977 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/comfy_t8_native_turbo_video.py, src/ai_video/production/comfy_t8_turbo_video.py and 5 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-112 | **KEEP** | orphan-file | `src/ai_video/production/comfy_video.py` | medium | medium | 921 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/shot_continuity_source_qualification.py, src/ai_video/production/shot_continuity_source_stack.py and 5 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-113 | **KEEP** | orphan-file | `src/ai_video/production/commercial_dependency.py` | medium | medium | 231 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/_commercial_project_reader.py, src/ai_video/production/_state_commit_commercial_source.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-114 | **KEEP** | orphan-file | `src/ai_video/production/commercial_graphics.py` | medium | medium | 205 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/_composition_visual.py, src/ai_video/production/_hyperframes_source.py and 14 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-115 | **KEEP** | orphan-file | `src/ai_video/production/commercial_image_import.py` | medium | medium | 104 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-116 | **KEEP** | orphan-file | `src/ai_video/production/commercial_reference.py` | medium | medium | 112 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/_commercial_video_planning.py, src/ai_video/planning/_planner_models.py, src/ai_video/production/__init__.py and 7 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-117 | **KEEP** | orphan-file | `src/ai_video/production/commercial_source_preparation.py` | medium | medium | 341 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/_commercial_video_planning.py, src/ai_video/planning/_planner_models.py, src/ai_video/production/__init__.py and 8 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-118 | **KEEP** | orphan-file | `src/ai_video/production/commercial_video_contracts.py` | medium | medium | 114 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_shot_router_contracts.py, src/ai_video/production/commercial_video_validation.py, src/ai_video/production/video.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-119 | **KEEP** | orphan-file | `src/ai_video/production/commercial_visual_review.py` | medium | medium | 376 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/_commercial_project_reader.py, src/ai_video/production/_state_commit_commercial_source.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-120 | **KEEP** | orphan-file | `src/ai_video/production/composition.py` | medium | medium | 832 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_composition.py, src/ai_video/production/__init__.py, src/ai_video/production/_hyperframes_native_audio.py and 28 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-121 | **KEEP** | orphan-file | `src/ai_video/production/composition_contracts.py` | medium | medium | 672 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_composition.py, src/ai_video/canvas_dependencies.py, src/ai_video/canvas_image.py and 31 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-122 | **KEEP** | orphan-file | `src/ai_video/production/continuity_evaluator.py` | medium | medium | 1099 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/continuity_onnx_backend.py, src/ai_video/production/local_continuity_reviewer.py, src/ai_video/production/shot_continuity_source_operator.py and 4 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-123 | **KEEP** | orphan-file | `src/ai_video/production/continuity_onnx_backend.py` | medium | medium | 616 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/local_continuity_reviewer.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-124 | **KEEP** | orphan-file | `src/ai_video/production/continuity_review_coordinator.py` | medium | medium | 622 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/provider_console_continuity.py, tests/test_production_continuity_review_coordinator.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-125 | **KEEP** | orphan-file | `src/ai_video/production/delivery_packager.py` | medium | medium | 687 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/ecommerce_job_review.py, tests/test_production_delivery_packager.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-126 | **KEEP** | orphan-file | `src/ai_video/production/dependency.py` | medium | medium | 1704 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_dependencies.py, src/ai_video/production/_commercial_project_reader.py, src/ai_video/production/_dependency_authoring.py and 58 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-127 | **KEEP** | orphan-file | `src/ai_video/production/domain_acceptance.py` | medium | medium | 423 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/production_strategy.py, src/ai_video/production/_caption_review_models.py, src/ai_video/production/_state_commit_review.py and 32 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-128 | **KEEP** | orphan-file | `src/ai_video/production/ecommerce_ad_coordinator.py` | medium | medium | 1038 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/ecommerce_job.py, src/ai_video/production/ecommerce_job_execution.py and 8 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-129 | **KEEP** | orphan-file | `src/ai_video/production/ecommerce_job.py` | medium | medium | 813 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, tests/test_production_delivery_packager.py, tests/test_production_ecommerce_job.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-130 | **KEEP** | orphan-file | `src/ai_video/production/ecommerce_job_assembly.py` | medium | medium | 559 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/delivery_packager.py, src/ai_video/production/ecommerce_job.py and 6 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-131 | **KEEP** | orphan-file | `src/ai_video/production/ecommerce_job_compiler.py` | medium | medium | 378 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, tests/test_production_delivery_packager.py, tests/test_production_ecommerce_job.py and 3 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-132 | **KEEP** | orphan-file | `src/ai_video/production/ecommerce_job_contracts.py` | medium | medium | 574 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/delivery_packager.py, src/ai_video/production/ecommerce_ad_coordinator.py and 14 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-133 | **KEEP** | orphan-file | `src/ai_video/production/ecommerce_job_execution.py` | medium | medium | 261 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/ecommerce_job.py, src/ai_video/production/ecommerce_job_projection.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-134 | **KEEP** | orphan-file | `src/ai_video/production/ecommerce_job_projection.py` | medium | medium | 540 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/ecommerce_job.py, tests/test_production_ecommerce_job_projection.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-135 | **KEEP** | orphan-file | `src/ai_video/production/ecommerce_job_repair.py` | medium | medium | 690 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/ecommerce_job.py, src/ai_video/production/ecommerce_job_execution.py, src/ai_video/production/ecommerce_job_projection.py and 3 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-136 | **KEEP** | orphan-file | `src/ai_video/production/ecommerce_job_review.py` | medium | medium | 334 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/ecommerce_job.py, src/ai_video/production/ecommerce_job_projection.py and 5 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-137 | **KEEP** | orphan-file | `src/ai_video/production/ecommerce_media_acceptance.py` | medium | medium | 350 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_video_commercial.py, src/ai_video/production/_video_project_reader.py, src/ai_video/production/commercial_execution.py and 21 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-138 | **KEEP** | orphan-file | `src/ai_video/production/ecommerce_quality_gate.py` | medium | medium | 691 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/_ecommerce_quality_gate_p6.py, src/ai_video/production/delivery_packager.py and 8 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-139 | **KEEP** | orphan-file | `src/ai_video/production/elevenlabs.py` | medium | medium | 782 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_production_elevenlabs.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-140 | **KEEP** | orphan-file | `src/ai_video/production/execution_stack_materialization.py` | medium | medium | 89 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_p0_qualification.py, src/ai_video/production/_video_project_reader.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-141 | **KEEP** | orphan-file | `src/ai_video/production/final_output_contracts.py` | medium | medium | 106 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/creative_goal_binding.py, scripts/visual_quality_report.py, src/ai_video/canvas_review.py and 17 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-142 | **KEEP** | orphan-file | `src/ai_video/production/final_output_review.py` | medium | medium | 348 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/visual_quality_report.py, src/ai_video/canvas_review.py, src/ai_video/production/_ecommerce_quality_gate_p6.py and 12 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-143 | **KEEP** | orphan-file | `src/ai_video/production/generation_decision.py` | medium | medium | 793 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/generation_feedback_driver.py, src/ai_video/production/_generation_feedback_reader.py, src/ai_video/production/_state_commit_generation_feedback.py and 22 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-144 | **KEEP** | orphan-file | `src/ai_video/production/generation_diagnosis.py` | medium | medium | 422 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/s01_strategy_regression.py, src/ai_video/canvas_production.py, src/ai_video/production/_sequence_source.py and 26 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-145 | **KEEP** | orphan-file | `src/ai_video/production/generation_evaluation.py` | medium | medium | 377 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/generation_feedback_driver.py, src/ai_video/canvas_handoff.py, src/ai_video/canvas_review.py and 28 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-146 | **KEEP** | orphan-file | `src/ai_video/production/generation_evaluation_criteria.py` | medium | medium | 137 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/generation_evaluation.py, src/ai_video_mcp/generation_feedback.py, tests/test_current_shot_close_expression.py and 6 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-147 | **KEEP** | orphan-file | `src/ai_video/production/generation_execution.py` | medium | medium | 482 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/sequence_continuity.py, src/ai_video/production/_generation_feedback_reader.py, src/ai_video/production/_sequence_source.py and 16 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-148 | **KEEP** | orphan-file | `src/ai_video/production/generation_experience.py` | medium | medium | 197 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/generation_difficulty.py, src/ai_video/production/_generation_feedback_reader.py, src/ai_video/production/_state_commit_generation_feedback.py and 15 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-149 | **KEEP** | orphan-file | `src/ai_video/production/generation_feedback.py` | medium | medium | 630 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_production.py, scripts/generation_feedback_driver.py, scripts/s01_strategy_regression.py and 37 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-150 | **KEEP** | orphan-file | `src/ai_video/production/generation_history_import.py` | medium | medium | 484 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_generation_feedback_reader.py, src/ai_video/production/_state_commit_generation_history.py, tests/test_generation_history_import.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-151 | **KEEP** | orphan-file | `src/ai_video/production/generation_input_control.py` | medium | medium | 126 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/generation_recipe.py, src/ai_video/production/requirement_semantics.py, src/ai_video/production/video_reference_controls.py and 3 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-152 | **KEEP** | orphan-file | `src/ai_video/production/generation_recipe.py` | medium | medium | 231 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_shot_router_contracts.py, src/ai_video/production/generation_decision.py, src/ai_video/production/generation_diagnosis.py and 37 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-153 | **KEEP** | orphan-file | `src/ai_video/production/generation_runtime_repair.py` | medium | medium | 496 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_recovery.py, src/ai_video/production/_generation_feedback_reader.py, src/ai_video/production/_state_commit_video_runtime_repair.py and 5 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-154 | **KEEP** | orphan-file | `src/ai_video/production/grok.py` | medium | medium | 838 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_generation_provider_wiring.py, tests/test_grok_output_contract.py, tests/test_grok_video_operations.py and 4 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-155 | **KEEP** | orphan-file | `src/ai_video/production/grok_auth.py` | medium | medium | 682 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/grok_auth.py, src/ai_video/production/grok_image.py, tests/test_grok_auth.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-156 | **KEEP** | orphan-file | `src/ai_video/production/grok_billing.py` | medium | medium | 142 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/grok_auth.py, tests/test_grok_billing.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-157 | **KEEP** | orphan-file | `src/ai_video/production/grok_download.py` | medium | medium | 54 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/grok.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-158 | **KEEP** | orphan-file | `src/ai_video/production/grok_image.py` | medium | medium | 560 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_grok_remote_image_lifecycle.py, tests/test_production_grok_image.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-159 | **KEEP** | orphan-file | `src/ai_video/production/grok_image_bytes.py` | medium | medium | 33 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_remote_image_reader.py, src/ai_video/production/grok_image.py, tests/test_grok_remote_image_lifecycle.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-160 | **KEEP** | orphan-file | `src/ai_video/production/grok_profile.py` | medium | medium | 495 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/grok.py, src/ai_video/production/grok_image.py, src/ai_video/production/grok_video_request.py and 8 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-161 | **KEEP** | orphan-file | `src/ai_video/production/grok_subscription.py` | medium | medium | 131 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/grok.py, src/ai_video/production/grok_billing.py, src/ai_video/production/grok_image.py and 5 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-162 | **KEEP** | orphan-file | `src/ai_video/production/grok_video_controls.py` | medium | medium | 57 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/grok_profile.py, tests/test_grok_video_capabilities.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-163 | **KEEP** | orphan-file | `src/ai_video/production/grok_video_measurement.py` | medium | medium | 35 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_video_project_reader.py, src/ai_video/production/video_artifact.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-164 | **KEEP** | orphan-file | `src/ai_video/production/grok_video_request.py` | medium | medium | 546 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/grok.py, tests/test_generation_provider_wiring.py, tests/test_grok_video_operations.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-165 | **KEEP** | orphan-file | `src/ai_video/production/hashing.py` | medium | medium | 38 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/composition_shadow.py, scripts/generation_feedback_driver.py, scripts/prepare_shot_continuity_endpoint_repair.py and 298 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-166 | **KEEP** | orphan-file | `src/ai_video/production/hyperframes.py` | medium | medium | 2575 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py, src/ai_video/production/__init__.py, src/ai_video/production/ecommerce_job_assembly.py and 17 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-167 | **KEEP** | orphan-file | `src/ai_video/production/image.py` | medium | medium | 1245 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/smoke_p7_1_local_image.py, src/ai_video/canvas_assets.py, src/ai_video/canvas_handoff.py and 34 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-168 | **KEEP** | orphan-file | `src/ai_video/production/image_bytes.py` | medium | medium | 107 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/image.py, src/ai_video/production/image_edit_mask.py, src/ai_video/production/image_preparation.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-169 | **KEEP** | orphan-file | `src/ai_video/production/image_candidate.py` | medium | medium | 81 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_image.py, tests/test_seedream_remote_image.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-170 | **KEEP** | orphan-file | `src/ai_video/production/image_candidate_frontier.py` | medium | medium | 47 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/image.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-171 | **KEEP** | orphan-file | `src/ai_video/production/image_edit_mask.py` | medium | medium | 256 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_image_workflow.py, src/ai_video/production/_image_project_reader.py, src/ai_video/production/_state_commit_image_intent.py and 3 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-172 | **KEEP** | orphan-file | `src/ai_video/production/image_import.py` | medium | medium | 889 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/prepare_shot_continuity_endpoint_repair.py, scripts/prepare_shot_continuity_p0.py, src/ai_video/production/__init__.py and 8 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-173 | **KEEP** | orphan-file | `src/ai_video/production/image_import_video_frame.py` | medium | medium | 287 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_handoff.py, src/ai_video/production/_image_project_reader.py, src/ai_video/production/_state_commit_bootstrap.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-174 | **KEEP** | orphan-file | `src/ai_video/production/image_materialization_failure.py` | medium | medium | 350 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_image_project_reader.py, src/ai_video/production/_state_commit_image_recovery.py, src/ai_video/production/_state_commit_remote_image.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-175 | **KEEP** | orphan-file | `src/ai_video/production/image_preparation.py` | medium | medium | 489 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py, src/ai_video/production/_image_project_reader.py, tests/test_canvas_image_preparation.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-176 | **KEEP** | orphan-file | `src/ai_video/production/local_continuity_reviewer.py` | medium | medium | 92 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/continuity_review_coordinator.py, tests/test_production_continuity_review_coordinator.py, tests/test_production_local_continuity_reviewer.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-177 | **KEEP** | orphan-file | `src/ai_video/production/local_h3_provider_family.py` | medium | medium | 260 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, tests/test_generation_local_wiring.py, tests/test_production_comfy_t8_native_long_video.py and 4 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-178 | **KEEP** | orphan-file | `src/ai_video/production/local_video.py` | medium | medium | 364 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/_state_commit_video.py, src/ai_video/production/_video_project_reader.py and 21 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-179 | **KEEP** | orphan-file | `src/ai_video/production/manifest_schema.py` | medium | medium | 111 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_caption_review_models.py, src/ai_video/production/_commercial_project_reader.py, src/ai_video/production/_commercial_source_state.py and 38 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-180 | **KEEP** | orphan-file | `src/ai_video/production/metaso_h3.py` | medium | medium | 449 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/minimax_h3_max.py, tests/test_production_metaso_h3.py, tests/test_production_minimax_h3_max.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-181 | **KEEP** | orphan-file | `src/ai_video/production/minimax_h3.py` | medium | medium | 696 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/metaso_h3.py, tests/test_generation_provider_wiring.py, tests/test_production_metaso_h3.py and 3 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-182 | **KEEP** | orphan-file | `src/ai_video/production/minimax_h3_max.py` | medium | medium | 141 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_canvas_source_expression.py, tests/test_production_minimax_h3_max.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-183 | **KEEP** | orphan-file | `src/ai_video/production/minimax_hailuo.py` | medium | medium | 1054 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_generation_provider_wiring.py, tests/test_production_minimax_hailuo.py, tests/test_production_provider_neutral_adapters.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-184 | **KEEP** | orphan-file | `src/ai_video/production/minimax_speech.py` | medium | medium | 641 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/minimax_speech_batch.py, src/ai_video/production/minimax_speech_batch.py, tests/test_production_minimax_speech_batch.py and 5 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-185 | **KEEP** | orphan-file | `src/ai_video/production/minimax_speech_batch.py` | medium | medium | 277 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/minimax_speech_batch.py, tests/test_production_minimax_speech_batch.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-186 | **KEEP** | orphan-file | `src/ai_video/production/models.py` | medium | medium | 2417 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_production.py, scripts/minimax_speech_batch.py, scripts/prepare_shot_continuity_endpoint_repair.py and 383 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-187 | **KEEP** | orphan-file | `src/ai_video/production/paid_provider.py` | medium | medium | 734 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/generation_feedback_driver.py, src/ai_video/production/__init__.py, src/ai_video/production/_generated_video_audio_contracts.py and 69 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-188 | **KEEP** | orphan-file | `src/ai_video/production/paid_provider_budget_extension.py` | medium | medium | 51 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_paid_provider.py, src/ai_video/production/paid_provider.py, tests/test_production_paid_budget_extension.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-189 | **KEEP** | orphan-file | `src/ai_video/production/paid_provider_no_effect_reconciliation.py` | medium | medium | 512 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_paid_provider_project_reader.py, src/ai_video/production/_state_commit_generation_feedback.py, src/ai_video/production/_state_commit_paid_provider.py and 4 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-190 | **KEEP** | orphan-file | `src/ai_video/production/paid_provider_submit_quota.py` | medium | medium | 354 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_paid_provider.py, src/ai_video/production/_state_commit_video.py, src/ai_video/production/paid_provider.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-191 | **KEEP** | orphan-file | `src/ai_video/production/paths.py` | medium | medium | 1118 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_production.py, scripts/creative_goal_binding.py, scripts/materialize_shot_continuity_m0.py and 149 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-192 | **KEEP** | orphan-file | `src/ai_video/production/performance_authoring.py` | medium | medium | 98 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_preflight.py, src/ai_video/production/generation_execution.py, src/ai_video/production/generation_feedback.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-193 | **KEEP** | orphan-file | `src/ai_video/production/production_responsibility.py` | medium | medium | 123 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_preflight.py, src/ai_video/production/video_reference_controls.py, src/ai_video/production_planning.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-194 | **KEEP** | orphan-file | `src/ai_video/production/production_strategy_composition.py` | medium | medium | 60 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/production_strategy_reader.py, tests/test_production_strategy_materialization.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-195 | **KEEP** | orphan-file | `src/ai_video/production/production_strategy_contracts.py` | medium | medium | 253 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py, src/ai_video/planning/production_strategy.py, src/ai_video/production/models.py and 9 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-196 | **KEEP** | orphan-file | `src/ai_video/production/production_strategy_dependency.py` | medium | medium | 104 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py, src/ai_video/production/minimax_speech_batch.py, src/ai_video/production/production_strategy_materialization.py and 4 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-197 | **KEEP** | orphan-file | `src/ai_video/production/production_strategy_materialization.py` | medium | medium | 646 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_composition.py, src/ai_video/production_planning.py, tests/test_production_planning_service.py and 4 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-198 | **KEEP** | orphan-file | `src/ai_video/production/production_strategy_reader.py` | medium | medium | 571 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_production.py, src/ai_video/canvas_authoring.py, src/ai_video/canvas_composition.py and 29 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-199 | **KEEP** | orphan-file | `src/ai_video/production/project.py` | medium | medium | 1589 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_sequence_handoff.py, scripts/materialize_shot_continuity_m0.py, scripts/minimax_speech_batch.py and 174 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-200 | **KEEP** | orphan-file | `src/ai_video/production/quality_gate_coordinator.py` | medium | medium | 483 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_caption_quality_p6.py, src/ai_video/production/_ecommerce_quality_gate_p6.py, src/ai_video/production/ecommerce_ad_coordinator.py and 7 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-201 | **KEEP** | orphan-file | `src/ai_video/production/registry.py` | medium | medium | 233 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/prepare_shot_continuity_endpoint_repair.py, scripts/prepare_shot_continuity_p0.py, src/ai_video/canvas_assets.py and 62 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-202 | **KEEP** | orphan-file | `src/ai_video/production/remote_image.py` | medium | medium | 61 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_image_project_reader.py, src/ai_video/production/_state_commit_remote_image.py, src/ai_video/production/grok_image.py and 8 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-203 | **KEEP** | orphan-file | `src/ai_video/production/remote_media.py` | medium | medium | 188 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/grok.py, src/ai_video/production/seedance.py and 4 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-204 | **KEEP** | orphan-file | `src/ai_video/production/renderer_audio_contracts.py` | medium | medium | 56 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/models.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-205 | **KEEP** | orphan-file | `src/ai_video/production/repair_input_admission.py` | medium | medium | 517 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py, src/ai_video/production/_composition_native_audio.py, src/ai_video/production/_composition_visual.py and 8 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-206 | **KEEP** | orphan-file | `src/ai_video/production/requirement_semantics.py` | medium | medium | 243 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_review.py, src/ai_video/production/domain_acceptance.py, src/ai_video/production/generation_evaluation.py and 8 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-207 | **KEEP** | orphan-file | `src/ai_video/production/review.py` | medium | medium | 854 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_handoff.py, src/ai_video/canvas_review.py, src/ai_video/production/_caption_quality_p6.py and 27 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-208 | **KEEP** | orphan-file | `src/ai_video/production/seedance_asset.py` | medium | medium | 871 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/generation_feedback_driver.py, src/ai_video/production/__init__.py, src/ai_video/production/seedance.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-209 | **KEEP** | orphan-file | `src/ai_video/production/seedance_capabilities.py` | medium | medium | 829 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/seedance.py, src/ai_video/production/seedance_profile.py, tests/test_production_provider_neutral_adapters.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-210 | **KEEP** | orphan-file | `src/ai_video/production/seedance_local_video.py` | medium | medium | 878 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/seedance.py, src/ai_video/production/seedance_mixed_reference.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-211 | **KEEP** | orphan-file | `src/ai_video/production/seedance_mixed_reference.py` | medium | medium | 203 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/seedance.py, tests/test_production_seedance_mixed_reference.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-212 | **KEEP** | orphan-file | `src/ai_video/production/seedance_native_prompt.py` | medium | medium | 154 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/seedance.py, tests/test_production_seedance_mixed_reference.py, tests/test_seedance_source_prompt.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-213 | **KEEP** | orphan-file | `src/ai_video/production/seedance_profile.py` | medium | medium | 257 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/generation_feedback_driver.py, src/ai_video/production/seedance.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-214 | **KEEP** | orphan-file | `src/ai_video/production/seedance_reference_duration.py` | medium | medium | 54 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/seedance.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-215 | **KEEP** | orphan-file | `src/ai_video/production/seedance_reference_image.py` | medium | medium | 33 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/seedance_asset.py, tests/test_production_seedance_mixed_reference.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-216 | **KEEP** | orphan-file | `src/ai_video/production/seedance_rejection.py` | medium | medium | 51 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/seedance.py, tests/test_production_seedance_rejection.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-217 | **KEEP** | orphan-file | `src/ai_video/production/seedance_source_dialogue.py` | medium | medium | 32 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/seedance_source_expression.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-218 | **KEEP** | orphan-file | `src/ai_video/production/seedance_source_expression.py` | medium | medium | 682 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_handoff.py, src/ai_video/canvas_planning.py, src/ai_video/canvas_project_data.py and 23 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-219 | **KEEP** | orphan-file | `src/ai_video/production/seedream.py` | medium | medium | 265 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_image_candidate_frontier.py, tests/test_remote_image_materialization.py, tests/test_seedream_remote_image.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-220 | **KEEP** | orphan-file | `src/ai_video/production/seedream_reference.py` | medium | medium | 43 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/image.py, src/ai_video/production/seedream.py, tests/test_seedream_remote_image.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-221 | **KEEP** | orphan-file | `src/ai_video/production/shot_continuity_m0_caller.py` | medium | medium | 930 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/generation_execution.py, src/ai_video/production/shot_continuity_m0_operator.py, tests/test_shot_continuity_m0_caller.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-222 | **KEEP** | orphan-file | `src/ai_video/production/shot_continuity_m0_fast_validation.py` | medium | medium | 617 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/materialize_shot_continuity_m0.py, src/ai_video/production/shot_continuity_m0_caller.py, tests/test_shot_continuity_m0_caller.py and 3 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-223 | **KEEP** | orphan-file | `src/ai_video/production/shot_continuity_m0_feasibility.py` | medium | medium | 588 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/shot_continuity_m0_caller.py, src/ai_video/production/shot_continuity_m0_operator.py, tests/test_shot_continuity_m0_feasibility.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-224 | **KEEP** | orphan-file | `src/ai_video/production/shot_continuity_m0_motion_tail.py` | medium | medium | 61 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/shot_continuity_m0_feasibility.py, src/ai_video/production/shot_continuity_m0_operator.py, src/ai_video/production/shot_continuity_m0_reprepare.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-225 | **KEEP** | orphan-file | `src/ai_video/production/shot_continuity_m0_operator.py` | medium | medium | 761 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_shot_continuity_m0_operator.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-226 | **KEEP** | orphan-file | `src/ai_video/production/shot_continuity_m0_policy.py` | medium | medium | 184 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/materialize_shot_continuity_m0.py, scripts/prepare_shot_continuity_endpoint_repair.py, scripts/prepare_shot_continuity_p0.py and 9 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-227 | **KEEP** | orphan-file | `src/ai_video/production/shot_continuity_m0_qualification.py` | medium | medium | 857 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/materialize_shot_continuity_m0.py, src/ai_video/production/shot_continuity_m0_caller.py, src/ai_video/production/shot_continuity_m0_fast_validation.py and 13 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-228 | **KEEP** | orphan-file | `src/ai_video/production/shot_continuity_m0_reprepare.py` | medium | medium | 334 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_shot_continuity_m0_reprepare.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-229 | **KEEP** | orphan-file | `src/ai_video/production/shot_continuity_m0_runtime.py` | medium | medium | 122 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/shot_continuity_m0_caller.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-230 | **KEEP** | orphan-file | `src/ai_video/production/shot_continuity_m0_seed_reseal.py` | medium | medium | 149 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/materialize_shot_continuity_m0.py, src/ai_video/production/shot_continuity_m0_qualification.py, tests/test_shot_continuity_m0_seed_reseal.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-231 | **KEEP** | orphan-file | `src/ai_video/production/shot_continuity_motion_analysis.py` | medium | medium | 481 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/shot_continuity_motion_tail.py, src/ai_video/production/shot_continuity_terminal_motion_tail.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-232 | **KEEP** | orphan-file | `src/ai_video/production/shot_continuity_motion_tail.py` | medium | medium | 764 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/shot_continuity_motion_tail_runtime.py, src/ai_video/production/shot_continuity_terminal_motion_tail.py, tests/test_shot_continuity_motion_tail.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-233 | **KEEP** | orphan-file | `src/ai_video/production/shot_continuity_motion_tail_runtime.py` | medium | medium | 29 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_shot_continuity_motion_tail.py, tests/test_shot_continuity_terminal_motion_tail.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-234 | **KEEP** | orphan-file | `src/ai_video/production/shot_continuity_source_contracts.py` | medium | medium | 81 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/shot_continuity_source_operator.py, src/ai_video/production/shot_continuity_source_qualification.py, src/ai_video/production/shot_continuity_source_transport.py and 3 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-235 | **KEEP** | orphan-file | `src/ai_video/production/shot_continuity_source_operator.py` | medium | medium | 693 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/execute_shot_continuity_source.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-236 | **KEEP** | orphan-file | `src/ai_video/production/shot_continuity_source_qualification.py` | medium | medium | 950 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/generation_execution.py, src/ai_video/production/shot_continuity_source_operator.py, tests/test_shot_continuity_source_operator.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-237 | **KEEP** | orphan-file | `src/ai_video/production/shot_continuity_source_review.py` | medium | medium | 765 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_video_candidate.py, src/ai_video/production/_state_commit_video_recovery.py, src/ai_video/production/_state_commit_video_source_boundary.py and 4 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-238 | **KEEP** | orphan-file | `src/ai_video/production/shot_continuity_source_runtime.py` | medium | medium | 423 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/prepare_shot_continuity_endpoint_repair.py, scripts/prepare_shot_continuity_p0.py, src/ai_video/production/shot_continuity_m0_operator.py and 6 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-239 | **KEEP** | orphan-file | `src/ai_video/production/shot_continuity_source_schema.py` | medium | medium | 100 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/shot_continuity_source_qualification.py, tests/test_shot_continuity_source_qualification.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-240 | **KEEP** | orphan-file | `src/ai_video/production/shot_continuity_source_stack.py` | medium | medium | 347 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/materialize_shot_continuity_m0.py, scripts/prepare_shot_continuity_p0.py, src/ai_video/production/shot_continuity_source_qualification.py and 4 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-241 | **KEEP** | orphan-file | `src/ai_video/production/shot_continuity_source_transport.py` | medium | medium | 254 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/shot_continuity_m0_caller.py, src/ai_video/production/shot_continuity_m0_operator.py, src/ai_video/production/shot_continuity_source_operator.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-242 | **KEEP** | orphan-file | `src/ai_video/production/shot_continuity_terminal_motion_tail.py` | medium | medium | 704 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/shot_continuity_m0_motion_tail.py, src/ai_video/production/shot_continuity_motion_tail_runtime.py, tests/test_shot_continuity_m0_feasibility.py and 3 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-243 | **KEEP** | orphan-file | `src/ai_video/production/shot_router.py` | medium | medium | 762 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/generation_feedback_driver.py, src/ai_video/production/__init__.py, src/ai_video/production/comfy_t8_native_turbo_video.py and 46 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-244 | **KEEP** | orphan-file | `src/ai_video/production/source_use_evidence.py` | medium | medium | 281 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/production_strategy.py, src/ai_video/production/domain_acceptance.py, src/ai_video/production/production_strategy_reader.py and 6 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-245 | **KEEP** | orphan-file | `src/ai_video/production/state_commit.py` | medium | medium | 577 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_production.py, scripts/generation_feedback_driver.py, scripts/materialize_shot_continuity_m0.py and 126 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-246 | **KEEP** | orphan-file | `src/ai_video/production/state_commit_attempt_contracts.py` | medium | medium | 65 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/models.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-247 | **KEEP** | orphan-file | `src/ai_video/production/validation.py` | medium | medium | 366 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_creative_project_reader.py, src/ai_video/production/project.py, tests/test_production_validation.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-248 | **KEEP** | orphan-file | `src/ai_video/production/video_cleanup_admission.py` | medium | medium | 125 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_bootstrap.py, src/ai_video/production/repair_input_admission.py, src/ai_video/production/video_cleanup_viewing_admission.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-249 | **KEEP** | orphan-file | `src/ai_video/production/video_cleanup_contracts.py` | medium | medium | 79 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/production_responsibility.py, src/ai_video/production/video_cleanup_media.py, src/ai_video/production/video_cleanup_pixels.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-250 | **KEEP** | orphan-file | `src/ai_video/production/video_cleanup_media.py` | medium | medium | 292 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py, src/ai_video/production/video_cleanup_admission.py, src/ai_video/production/video_cleanup_viewing.py and 3 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-251 | **KEEP** | orphan-file | `src/ai_video/production/video_cleanup_pixels.py` | medium | medium | 281 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/video_cleanup_media.py, tests/test_video_cleanup_pixels.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-252 | **KEEP** | orphan-file | `src/ai_video/production/video_cleanup_viewing.py` | medium | medium | 305 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/video_cleanup_viewing_admission.py, tests/test_video_cleanup_admission.py, tests/test_video_cleanup_viewing.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-253 | **KEEP** | orphan-file | `src/ai_video/production/video_cleanup_viewing_admission.py` | medium | medium | 94 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/repair_input_admission.py, src/ai_video/production/video_cleanup_admission.py, tests/test_video_cleanup_admission.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-254 | **KEEP** | orphan-file | `src/ai_video/production/video_compiler.py` | medium | medium | 935 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/comfy_t8_native_turbo_video.py, src/ai_video/production/comfy_t8_turbo_video.py, src/ai_video/production/comfy_t8_video.py and 46 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-255 | **KEEP** | orphan-file | `src/ai_video/production/video_contracts.py` | medium | medium | 637 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/generation_feedback_driver.py, src/ai_video/production/__init__.py, src/ai_video/production/_shot_router_contracts.py and 35 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-256 | **KEEP** | orphan-file | `src/ai_video/production/video_execution_stack.py` | medium | medium | 270 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/materialize_shot_continuity_m0.py, scripts/prepare_shot_continuity_p0.py, src/ai_video/planning/sequence_continuity.py and 17 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-257 | **KEEP** | orphan-file | `src/ai_video/production/video_geometry.py` | medium | medium | 16 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_video_project_reader.py, src/ai_video/production/video_artifact.py, tests/test_grok_output_contract.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-258 | **KEEP** | orphan-file | `src/ai_video/production/video_reference_controls.py` | medium | medium | 399 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_production.py, tests/test_character_performance_workflow.py, tests/test_generation_reference_controls.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-259 | **KEEP** | orphan-file | `src/ai_video/production/video_requirement.py` | medium | medium | 1426 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_planning.py, src/ai_video/canvas_source_expression.py, src/ai_video/canvas_source_revision.py and 85 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-260 | **KEEP** | orphan-file | `src/ai_video/production/video_retime.py` | medium | medium | 93 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_composition.py, src/ai_video/production/__init__.py, src/ai_video/production/_composition_visual.py and 13 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-261 | **KEEP** | orphan-file | `src/ai_video/production/video_subjects.py` | medium | medium | 91 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_vidu_subjects.py, src/ai_video/production/video.py, src/ai_video/production/video_compiler.py and 3 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-262 | **KEEP** | orphan-file | `src/ai_video/production/video_timing_recovery.py` | medium | medium | 106 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/video_artifact.py, tests/test_video_nominal_endpoint_recovery.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-263 | **KEEP** | orphan-file | `src/ai_video/production/video_transition.py` | medium | medium | 667 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_sequence_handoff.py, scripts/canvas_sequence_packet.py, scripts/prepare_shot_continuity_p0.py and 32 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-264 | **KEEP** | orphan-file | `src/ai_video/production/vidu.py` | medium | medium | 577 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/s01_strategy_regression.py, src/ai_video/production/vidu_ad_provider.py, tests/test_generation_provider_wiring.py and 4 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-265 | **KEEP** | orphan-file | `src/ai_video/production/vidu_ad_contracts.py` | medium | medium | 129 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_ad.py, src/ai_video/production/models.py, src/ai_video/production/vidu_ad_provider.py and 3 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-266 | **KEEP** | orphan-file | `src/ai_video/production/vidu_ad_provider.py` | medium | medium | 117 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_paid_provider.py, src/ai_video/production/vidu.py, src/ai_video/production/vidu_ad_reader.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-267 | **KEEP** | orphan-file | `src/ai_video/production/vidu_ad_reader.py` | medium | medium | 117 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_paid_provider_project_reader.py, src/ai_video/production/_state_commit_ad.py, src/ai_video/production/_state_commit_paid_provider.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-268 | **KEEP** | orphan-file | `src/ai_video/production/vidu_ad_wire.py` | medium | medium | 143 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/vidu_ad_provider.py, tests/test_production_vidu_ad_wire.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-269 | **KEEP** | orphan-file | `src/ai_video/production/vidu_download.py` | medium | medium | 141 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_ad.py, src/ai_video/production/grok_download.py, src/ai_video/production/metaso_h3.py and 4 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-270 | **KEEP** | orphan-file | `src/ai_video/production/vidu_profile.py` | medium | medium | 203 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/s01_strategy_regression.py, src/ai_video/production/generation_decision.py, src/ai_video/production/generation_feedback.py and 9 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-271 | **KEEP** | orphan-file | `src/ai_video/production/vidu_source.py` | medium | medium | 53 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/vidu.py, tests/test_production_vidu.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-272 | **KEEP** | orphan-file | `src/ai_video/production/visual_media.py` | medium | medium | 207 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/production_strategy.py, src/ai_video/production/_composition_source_duration.py, src/ai_video/production/_composition_visual.py and 4 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-273 | **KEEP** | orphan-file | `src/ai_video/production/visual_quality.py` | medium | medium | 91 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/visual_quality_report.py, src/ai_video/production/final_output_contracts.py, src/ai_video/production/final_output_review.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-274 | **KEEP** | orphan-file | `src/ai_video/production/voice_routing.py` | medium | medium | 662 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_shot_router_contracts.py, src/ai_video/production/_state_commit_paid_provider.py, src/ai_video/production/_state_commit_voice_candidate.py and 13 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-275 | **KEEP** | orphan-file | `src/ai_video/production/voice_routing_contracts.py` | medium | medium | 118 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/generation_decision.py, src/ai_video/production/models.py, src/ai_video/production/video_requirement.py and 10 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-276 | **KEEP** | orphan-file | `src/ai_video/production/voice_routing_execution.py` | medium | medium | 58 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_voice_candidate.py, src/ai_video/production/_state_commit_voice_intent.py, src/ai_video/production/_voice_project_reader.py and 3 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-277 | **KEEP** | orphan-file | `src/ai_video/production_planning.py` | medium | medium | 140 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/s01_strategy_regression.py, src/ai_video/canvas_production.py, tests/test_canvas_production.py and 8 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-278 | **KEEP** | orphan-file | `src/ai_video/provider_console.py` | medium | medium | 880 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/provider_console_media_index.py, src/ai_video/provider_console_video_evidence.py, tests/test_provider_console.py and 1 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-279 | **KEEP** | orphan-file | `src/ai_video/provider_console_continuity.py` | medium | medium | 224 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/provider_console.py, src/ai_video/provider_console_render.py, tests/test_provider_console.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-280 | **KEEP** | orphan-file | `src/ai_video/provider_console_manifest.py` | medium | medium | 77 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/provider_console.py, src/ai_video/provider_console_video_evidence.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-281 | **KEEP** | orphan-file | `src/ai_video/provider_console_media_index.py` | medium | medium | 325 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_provider_console_media_index.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-282 | **KEEP** | orphan-file | `src/ai_video/provider_console_render.py` | medium | medium | 38 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/provider_console.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-283 | **KEEP** | orphan-file | `src/ai_video/provider_console_video_evidence.py` | medium | medium | 67 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/provider_console_media_index.py, tests/test_provider_console.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-284 | **KEEP** | orphan-file | `src/ai_video/quality_gates/_readiness_models.py` | medium | medium | 288 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/quality_gates/__init__.py, src/ai_video/quality_gates/shot_readiness_gate.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-285 | **KEEP** | orphan-file | `src/ai_video/quality_gates/shot_readiness_gate.py` | medium | medium | 326 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/quality_gates/__init__.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-286 | **KEEP** | orphan-file | `src/ai_video/quality_intelligence/_capture_contracts.py` | medium | medium | 127 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/quality_intelligence/_capture_human.py, src/ai_video/quality_intelligence/_capture_p6.py, src/ai_video/quality_intelligence/capture.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-287 | **KEEP** | orphan-file | `src/ai_video/quality_intelligence/_capture_p6.py` | medium | medium | 106 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/quality_intelligence/capture.py, tests/test_quality_experience_capture.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-288 | **KEEP** | orphan-file | `src/ai_video/quality_intelligence/capture.py` | medium | medium | 800 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/quality_intelligence/__init__.py, tests/test_quality_experience_capture.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-289 | **KEEP** | orphan-file | `src/ai_video/quality_intelligence/dataset.py` | medium | medium | 389 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/quality_intelligence/__init__.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-290 | **KEEP** | orphan-file | `src/ai_video/quality_intelligence/models.py` | medium | medium | 1561 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/quality_intelligence/__init__.py, src/ai_video/quality_intelligence/_capture_contracts.py, src/ai_video/quality_intelligence/_capture_human.py and 10 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-291 | **KEEP** | orphan-file | `src/ai_video/quality_intelligence/rag_projection.py` | medium | medium | 67 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/quality_intelligence/__init__.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-292 | **KEEP** | orphan-file | `src/ai_video/quality_intelligence/store.py` | medium | medium | 718 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/quality_intelligence/__init__.py, src/ai_video/quality_intelligence/_capture_contracts.py, src/ai_video/quality_intelligence/capture.py and 6 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-293 | **KEEP** | orphan-file | `src/ai_video/workflow_loader.py` | medium | medium | 545 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/check_p7_1_comfy_compatibility.py, src/ai_video/cli.py, src/ai_video/production/comfy_image.py and 12 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-294 | **KEEP** | orphan-file | `src/ai_video/workflow_renderer.py` | medium | medium | 264 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/check_p7_1_comfy_compatibility.py, src/ai_video/cli.py, src/ai_video/pipeline.py and 9 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-295 | **KEEP** | orphan-file | `src/ai_video_mcp/analysis_client.py` | medium | medium | 39 | KEEP: generation_feedback.py:131 launches this exact module with python -m; tests/test_generation_feedback_review.py:35 asserts the subprocess entry. |
| CRT-296 | **KEEP** | orphan-file | `src/ai_video_mcp/analysis_hook.py` | medium | medium | 756 | KEEP: .codex/hooks.json:34 and .claude/settings.json:31 register this hook; tests/test_mcp_analyze.py dynamically imports it. |
| CRT-297 | **KEEP** | orphan-file | `src/ai_video_mcp/audio_operator.py` | medium | medium | 523 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_mcp_audio_operator.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-298 | **KEEP** | orphan-file | `src/ai_video_mcp/audio_understanding.py` | medium | medium | 435 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/audio_operator.py, src/ai_video_mcp/server.py, src/ai_video_mcp/tools/audio_understand.py and 3 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-299 | **KEEP** | orphan-file | `src/ai_video_mcp/cache.py` | medium | medium | 45 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/analysis_hook.py, src/ai_video_mcp/server.py, src/ai_video_mcp/tools/analyze.py and 8 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-300 | **KEEP** | orphan-file | `src/ai_video_mcp/config.py` | medium | medium | 39 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/analysis_hook.py, src/ai_video_mcp/server.py, src/ai_video_mcp/tools/analyze.py and 10 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-301 | **KEEP** | orphan-file | `src/ai_video_mcp/errors.py` | medium | medium | 30 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/server.py, src/ai_video_mcp/tools/frames.py, src/ai_video_mcp/tools/probe.py and 9 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-302 | **KEEP** | orphan-file | `src/ai_video_mcp/generation_feedback.py` | medium | medium | 263 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/generation_feedback_driver.py, src/ai_video/canvas_production.py, tests/test_canvas_continuity.py and 5 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-303 | **KEEP** | orphan-file | `src/ai_video_mcp/serialization.py` | medium | medium | 119 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/analysis_hook.py, src/ai_video_mcp/server.py, tests/test_mcp_analyze.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-304 | **KEEP** | orphan-file | `src/ai_video_mcp/server.py` | medium | medium | 314 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/__main__.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-305 | **KEEP** | orphan-file | `src/ai_video_mcp/tools/analyze.py` | medium | medium | 88 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/analysis_hook.py, src/ai_video_mcp/server.py, src/ai_video_mcp/tools/review.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-306 | **KEEP** | orphan-file | `src/ai_video_mcp/tools/apply_optimization.py` | medium | medium | 176 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/server.py, tests/test_mcp_apply_optimization.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-307 | **KEEP** | orphan-file | `src/ai_video_mcp/tools/audio_understand.py` | medium | medium | 151 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/audio_operator.py, src/ai_video_mcp/server.py, src/ai_video_mcp/tools/analyze.py and 2 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-308 | **KEEP** | orphan-file | `src/ai_video_mcp/tools/frames.py` | medium | medium | 127 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/server.py, src/ai_video_mcp/tools/analyze.py, tests/test_mcp_frames.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-309 | **KEEP** | orphan-file | `src/ai_video_mcp/tools/optimize_plan.py` | medium | medium | 229 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/server.py, src/ai_video_mcp/tools/apply_optimization.py, tests/test_mcp_optimize_plan.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-310 | **KEEP** | orphan-file | `src/ai_video_mcp/tools/probe.py` | medium | medium | 129 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/server.py, src/ai_video_mcp/tools/analyze.py, src/ai_video_mcp/tools/frames.py and 5 more. See python-static.json; bundled import resolution is a false positive. |
| CRT-311 | **KEEP** | orphan-file | `src/ai_video_mcp/tools/review.py` | medium | medium | 382 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/server.py, src/ai_video_mcp/tools/optimize_plan.py, tests/test_mcp_review.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-312 | **KEEP** | orphan-file | `src/ai_video_mcp/tools/scene_detect.py` | medium | medium | 123 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/server.py, src/ai_video_mcp/tools/analyze.py, tests/test_mcp_scene_detect.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-313 | **KEEP** | orphan-file | `src/ai_video_mcp/tools/transcribe.py` | medium | medium | 136 | KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/server.py, src/ai_video_mcp/tools/analyze.py, tests/test_mcp_transcribe.py. See python-static.json; bundled import resolution is a false positive. |
| CRT-314 | **KEEP** | orphan-file | `tests/ecommerce_job_factory.py` | medium | medium | 430 | KEEP: pytest uses tests/ as an import root; real helper module imports occur in tests/test_production_delivery_packager.py, tests/test_production_ecommerce_job.py, tests/test_production_ecommerce_job_assembly.py. The generic resolver uses the repository root. |
| CRT-315 | **KEEP** | orphan-file | `tests/helpers/p2a_crash_worker.py` | medium | medium | 358 | KEEP: tests/test_production_state_recovery.py:443 executes this helper via its string path. |
| CRT-316 | **KEEP** | orphan-file | `tests/production_e2e_support.py` | medium | medium | 2143 | KEEP: pytest uses tests/ as an import root; real helper module imports occur in tests/production_project_factory.py, tests/test_canvas_continuity.py, tests/test_canvas_edit_first.py. The generic resolver uses the repository root. |
| CRT-317 | **KEEP** | orphan-file | `tests/production_ecommerce_job_render_support.py` | medium | medium | 142 | KEEP: pytest uses tests/ as an import root; real helper module imports occur in tests/test_agent_harness.py, tests/test_production_ecommerce_job_e2e.py. The generic resolver uses the repository root. |
| CRT-318 | **KEEP** | orphan-file | `tests/production_remote_generation_factory.py` | medium | medium | 254 | KEEP: pytest uses tests/ as an import root; real helper module imports occur in tests/test_agent_harness.py, tests/test_generation_feedback_driver.py, tests/test_production_grok.py. The generic resolver uses the repository root. |
| CRT-319 | **KEEP** | orphan-file | `tests/production_strategy_factory.py` | medium | medium | 385 | KEEP: pytest uses tests/ as an import root; real helper module imports occur in tests/test_canvas_edit_first.py, tests/test_canvas_production.py, tests/test_canvas_project_data.py. The generic resolver uses the repository root. |
| CRT-320 | **KEEP** | orphan-file | `tests/production_voice_e2e_support.py` | medium | medium | 220 | KEEP: pytest uses tests/ as an import root; real helper module imports occur in tests/production_e2e_support.py, tests/test_production_voice_captions_e2e.py. The generic resolver uses the repository root. |
| CRT-321 | **KEEP** | orphan-file | `tests/video_provider_contract.py` | medium | medium | 148 | KEEP: pytest uses tests/ as an import root; real helper module imports occur in tests/test_production_video_fake.py. The generic resolver uses the repository root. |
| CRT-322 | **KEEP** | unused-export | `downloadHumanReviewDecision from provider-console/src/continuity-review.js` | medium | medium | 0 | KEEP: continuity-review.js:79 invokes downloadHumanReviewDecision from the panel submit handler. No external export consumer does not mean the function is dead. |
| CRT-323 | **KEEP** | unused-export | `preferredRunBinding from provider-console/src/external-media-contract.js` | medium | medium | 0 | KEEP: external-media-contract.js:16 and :194 invoke preferredRunBinding, including externalDisplayMetadata. The implementation is live. |
| CRT-324 | **REVIEW** | unused-export | `_source_render_pairs from src/ai_video/production/dependency.py` | high | low | 14 | Private function; no in-repository consumer found. Rare dynamic/external use and regression safety are unproven. Proposed function-only patch is syntax-valid but has no execution proof. |
| CRT-325 | **REVIEW** | unused-export | `is_supported_manifest_version from src/ai_video/production/manifest_schema.py` | medium | medium | 2 | Public module function; external imports cannot be ruled out, and passing in-repository tests would not prove external API compatibility. Proposed function-only patch is syntax-valid but has no execution proof. |

## Evidence by candidate

### CRT-001 — KEEP

- Location: `provider-console/src/continuity-review-contract.js`
- Category: `orphan-file`
- Potential size: 64 LOC / 2.6 KB
- Status reason: KEEP: continuity-review.js:2-5 multiline-imports this module and re-exports it at lines 8-14; provider-console/tests/continuity-review-contract.test.mjs also imports it. Bundled regex misses multiline imports.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: continuity-review-contract, continuity-review-contract.js.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-002 — KEEP

- Location: `src/ai_video/agent_memory/chunking.py`
- Category: `orphan-file`
- Potential size: 94 LOC / 3.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/agent_memory/index.py, tests/test_agent_memory.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: chunking.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-003 — KEEP

- Location: `src/ai_video/agent_memory/config.py`
- Category: `orphan-file`
- Potential size: 79 LOC / 3.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/agent_memory.py, src/ai_video/agent_memory/__init__.py, src/ai_video/agent_memory/embeddings.py and 5 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: config, config.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-004 — KEEP

- Location: `src/ai_video/agent_memory/corpus.py`
- Category: `orphan-file`
- Potential size: 435 LOC / 15.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/agent_memory.py, src/ai_video/agent_memory/__init__.py, src/ai_video/agent_memory/index.py and 4 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: corpus, corpus.py, src/ai_video/agent_memory/corpus, src/ai_video/agent_memory/corpus.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-005 — KEEP

- Location: `src/ai_video/agent_memory/embeddings.py`
- Category: `orphan-file`
- Potential size: 235 LOC / 8.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/agent_memory.py, src/ai_video/agent_memory/__init__.py, src/ai_video/agent_memory/manifest.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: embeddings.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-006 — KEEP

- Location: `src/ai_video/agent_memory/hybrid.py`
- Category: `orphan-file`
- Potential size: 143 LOC / 4.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/agent_memory/retrieval.py, tests/test_agent_memory.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: hybrid.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-007 — KEEP

- Location: `src/ai_video/agent_memory/index.py`
- Category: `orphan-file`
- Potential size: 546 LOC / 19.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/agent_memory.py, src/ai_video/agent_memory/__init__.py, src/ai_video/agent_memory/layout.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: index, index.py, src/ai_video/agent_memory/index.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-008 — KEEP

- Location: `src/ai_video/agent_memory/layout.py`
- Category: `orphan-file`
- Potential size: 214 LOC / 6.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/agent_memory.py, src/ai_video/agent_memory/__init__.py, src/ai_video/agent_memory/retrieval.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: layout, layout.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-009 — KEEP

- Location: `src/ai_video/agent_memory/maintenance.py`
- Category: `orphan-file`
- Potential size: 327 LOC / 11.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/agent_memory.py, tests/test_agent_memory.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: maintenance.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-010 — KEEP

- Location: `src/ai_video/agent_memory/manifest.py`
- Category: `orphan-file`
- Potential size: 280 LOC / 9.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/agent_memory.py, src/ai_video/agent_memory/__init__.py, src/ai_video/agent_memory/index.py and 3 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: manifest, manifest.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-011 — KEEP

- Location: `src/ai_video/agent_memory/retrieval.py`
- Category: `orphan-file`
- Potential size: 954 LOC / 33.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/agent_memory.py, src/ai_video/agent_memory/__init__.py, tests/test_agent_memory.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: retrieval, retrieval.py, src/ai_video/agent_memory/retrieval, src/ai_video/agent_memory/retrieval.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-012 — KEEP

- Location: `src/ai_video/canvas_assets.py`
- Category: `orphan-file`
- Potential size: 81 LOC / 5.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py, src/ai_video/canvas_project_data.py, tests/test_canvas_assets.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: canvas_assets, canvas_assets.py, src/ai_video/canvas_assets, src/ai_video/canvas_assets.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-013 — KEEP

- Location: `src/ai_video/canvas_authoring.py`
- Category: `orphan-file`
- Potential size: 269 LOC / 16.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_assets.py, src/ai_video/canvas_preflight.py, src/ai_video/canvas_production.py and 11 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: canvas_authoring, canvas_authoring.py, src/ai_video/canvas_authoring, src/ai_video/canvas_authoring.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-014 — KEEP

- Location: `src/ai_video/canvas_composition.py`
- Category: `orphan-file`
- Potential size: 174 LOC / 10.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py, tests/test_canvas_edit_first.py, tests/test_canvas_native_audio_retime.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: canvas_composition, canvas_composition.py, src/ai_video/canvas_composition, src/ai_video/canvas_composition.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-015 — KEEP

- Location: `src/ai_video/canvas_dependencies.py`
- Category: `orphan-file`
- Potential size: 148 LOC / 9.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_image.py, src/ai_video/canvas_production.py, tests/test_canvas_masked_image_workflow.py and 5 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: canvas_dependencies.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-016 — KEEP

- Location: `src/ai_video/canvas_external_image.py`
- Category: `orphan-file`
- Potential size: 23 LOC / 1.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_production_source.py, scripts/canvas_sequence_packet.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: canvas_external_image, canvas_external_image.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-017 — KEEP

- Location: `src/ai_video/canvas_handoff.py`
- Category: `orphan-file`
- Potential size: 255 LOC / 17.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_planning.py, src/ai_video/canvas_production.py, src/ai_video/canvas_source_expression.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: canvas_handoff, canvas_handoff.py, src/ai_video/canvas_handoff, src/ai_video/canvas_handoff.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-018 — KEEP

- Location: `src/ai_video/canvas_image.py`
- Category: `orphan-file`
- Potential size: 23 LOC / 1.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_canvas_masked_image_workflow.py, tests/test_image_candidate_frontier.py, tests/test_seedream_remote_image.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: canvas_image, canvas_image.py, src/ai_video/canvas_image, src/ai_video/canvas_image.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-019 — KEEP

- Location: `src/ai_video/canvas_image_workflow.py`
- Category: `orphan-file`
- Potential size: 59 LOC / 3.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: canvas_image_workflow, canvas_image_workflow.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-020 — KEEP

- Location: `src/ai_video/canvas_planning.py`
- Category: `orphan-file`
- Potential size: 244 LOC / 16.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py, src/ai_video/canvas_visual_style.py, tests/test_canvas_continuity.py and 4 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: canvas_planning, canvas_planning.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-021 — KEEP

- Location: `src/ai_video/canvas_preflight.py`
- Category: `orphan-file`
- Potential size: 162 LOC / 9.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_production.py, tests/test_canvas_continuity.py, tests/test_canvas_project_data.py and 3 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: canvas_preflight, canvas_preflight.py, src/ai_video/canvas_preflight, src/ai_video/canvas_preflight.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-022 — KEEP

- Location: `src/ai_video/canvas_production.py`
- Category: `orphan-file`
- Potential size: 741 LOC / 44.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_project_data.py, tests/test_canvas_assets.py, tests/test_canvas_continuity.py and 12 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: canvas_production, canvas_production.py, src/ai_video/canvas_production, src/ai_video/canvas_production.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-023 — KEEP

- Location: `src/ai_video/canvas_project_data.py`
- Category: `orphan-file`
- Potential size: 191 LOC / 11.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_production.py, tests/test_canvas_external_image.py, tests/test_canvas_imported_audio_retime.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: canvas_project_data, canvas_project_data.py, src/ai_video/canvas_project_data, src/ai_video/canvas_project_data.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-024 — KEEP

- Location: `src/ai_video/canvas_recovery.py`
- Category: `orphan-file`
- Potential size: 239 LOC / 13.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py, tests/test_canvas_recovery.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: canvas_recovery, canvas_recovery.py, src/ai_video/canvas_recovery, src/ai_video/canvas_recovery.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-025 — KEEP

- Location: `src/ai_video/canvas_review.py`
- Category: `orphan-file`
- Potential size: 194 LOC / 13.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_authoring.py, src/ai_video/canvas_handoff.py, src/ai_video/canvas_production.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: canvas_review, canvas_review.py, src/ai_video/canvas_review, src/ai_video/canvas_review.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-026 — KEEP

- Location: `src/ai_video/canvas_source_expression.py`
- Category: `orphan-file`
- Potential size: 233 LOC / 15.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_authoring.py, src/ai_video/canvas_handoff.py, src/ai_video/canvas_project_data.py and 3 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: canvas_source_expression, canvas_source_expression.py, src/ai_video/canvas_source_expression, src/ai_video/canvas_source_expression.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-027 — KEEP

- Location: `src/ai_video/canvas_source_revision.py`
- Category: `orphan-file`
- Potential size: 188 LOC / 9.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_authoring.py, src/ai_video/canvas_production.py, tests/test_canvas_continuity.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: canvas_source_revision, canvas_source_revision.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-028 — KEEP

- Location: `src/ai_video/canvas_subject.py`
- Category: `orphan-file`
- Potential size: 36 LOC / 1.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_production_source.py, scripts/canvas_sequence_packet.py, src/ai_video/canvas_assets.py and 3 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: canvas_subject.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-029 — KEEP

- Location: `src/ai_video/canvas_target_gate.py`
- Category: `orphan-file`
- Potential size: 53 LOC / 3.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_planning.py, src/ai_video/canvas_production.py, tests/test_canvas_continuity.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: canvas_target_gate.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-030 — KEEP

- Location: `src/ai_video/canvas_visual_style.py`
- Category: `orphan-file`
- Potential size: 369 LOC / 17.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_authoring.py, src/ai_video/canvas_preflight.py, src/ai_video/canvas_production.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: canvas_visual_style, canvas_visual_style.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-031 — KEEP

- Location: `src/ai_video/cli.py`
- Category: `orphan-file`
- Potential size: 111 LOC / 4.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_cli.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: cli.py, src/ai_video/cli, src/ai_video/cli.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-032 — KEEP

- Location: `src/ai_video/comfy_client.py`
- Category: `orphan-file`
- Potential size: 281 LOC / 9.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/pipeline.py, src/ai_video/production/comfy_image.py, src/ai_video/production/comfy_t8_native_turbo_video.py and 16 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: comfy_client, comfy_client.py, src/ai_video/comfy_client, src/ai_video/comfy_client.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-033 — KEEP

- Location: `src/ai_video/config.py`
- Category: `orphan-file`
- Potential size: 131 LOC / 4.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/cli.py, src/ai_video/manifest.py, src/ai_video/pipeline.py and 10 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: config, config.py, src/ai_video/config, src/ai_video/config.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-034 — KEEP

- Location: `src/ai_video/errors.py`
- Category: `orphan-file`
- Potential size: 101 LOC / 4.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/agent_harness_canvas_data.py, scripts/canvas_production.py, scripts/execute_shot_continuity_source.py and 314 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: errors, errors.py, src/ai_video/errors, src/ai_video/errors.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-035 — KEEP

- Location: `src/ai_video/ffmpeg_tools.py`
- Category: `orphan-file`
- Potential size: 187 LOC / 4.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/pipeline.py, src/ai_video/production/video_artifact.py, tests/test_ffmpeg_tools.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: ffmpeg_tools, ffmpeg_tools.py, src/ai_video/ffmpeg_tools, src/ai_video/ffmpeg_tools.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-036 — KEEP

- Location: `src/ai_video/manifest.py`
- Category: `orphan-file`
- Potential size: 159 LOC / 4.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/cli.py, src/ai_video/pipeline.py, src/ai_video/provider_console.py and 7 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: manifest, manifest.py, src/ai_video/manifest, src/ai_video/manifest.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-037 — KEEP

- Location: `src/ai_video/models.py`
- Category: `orphan-file`
- Potential size: 140 LOC / 3.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/cli.py, src/ai_video/config.py, src/ai_video/pipeline.py and 6 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: models, models.py, src/ai_video/models, src/ai_video/models.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-038 — KEEP

- Location: `src/ai_video/pipeline.py`
- Category: `orphan-file`
- Potential size: 661 LOC / 25.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/cli.py, tests/test_pipeline.py, tests/test_resume_e2e.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: pipeline, pipeline.py, src/ai_video/pipeline, src/ai_video/pipeline.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-039 — KEEP

- Location: `src/ai_video/planning/_asset_readiness.py`
- Category: `orphan-file`
- Potential size: 314 LOC / 10.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/_current_plan_projection.py, src/ai_video/planning/video_planner.py, src/ai_video/quality_gates/shot_readiness_gate.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _asset_readiness, _asset_readiness.py, src/ai_video/planning/_asset_readiness, src/ai_video/planning/_asset_readiness.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-040 — KEEP

- Location: `src/ai_video/planning/_commercial_video_planning.py`
- Category: `orphan-file`
- Potential size: 217 LOC / 9.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/__init__.py, src/ai_video/planning/video_planner.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _commercial_video_planning, _commercial_video_planning.py, src/ai_video/planning/_commercial_video_planning, src/ai_video/planning/_commercial_video_planning.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-041 — KEEP

- Location: `src/ai_video/planning/_current_plan_projection.py`
- Category: `orphan-file`
- Potential size: 201 LOC / 7.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/video_planner.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _current_plan_projection, _current_plan_projection.py, src/ai_video/planning/_current_plan_projection, src/ai_video/planning/_current_plan_projection.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-042 — KEEP

- Location: `src/ai_video/planning/_planner_models.py`
- Category: `orphan-file`
- Potential size: 613 LOC / 24.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/composition_playbooks.py, scripts/composition_shadow.py, src/ai_video/planning/__init__.py and 7 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _planner_models, _planner_models.py, src/ai_video/planning/_planner_models, src/ai_video/planning/_planner_models.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-043 — KEEP

- Location: `src/ai_video/planning/generation_difficulty.py`
- Category: `orphan-file`
- Potential size: 39 LOC / 2.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/video_planner.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: generation_difficulty, generation_difficulty.py, src/ai_video/planning/generation_difficulty, src/ai_video/planning/generation_difficulty.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-044 — KEEP

- Location: `src/ai_video/planning/generation_feedback_context.py`
- Category: `orphan-file`
- Potential size: 41 LOC / 2.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/generation_feedback_driver.py, scripts/s01_strategy_regression.py, src/ai_video/canvas_planning.py and 3 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: generation_feedback_context, generation_feedback_context.py, src/ai_video/planning/generation_feedback_context, src/ai_video/planning/generation_feedback_context.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-045 — KEEP

- Location: `src/ai_video/planning/production_strategy.py`
- Category: `orphan-file`
- Potential size: 284 LOC / 16.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/s01_strategy_regression.py, src/ai_video/production_planning.py, tests/test_canvas_production.py and 6 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: production_strategy, production_strategy.py, src/ai_video/planning/production_strategy, src/ai_video/planning/production_strategy.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-046 — KEEP

- Location: `src/ai_video/planning/sequence_continuity.py`
- Category: `orphan-file`
- Potential size: 256 LOC / 17.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_sequence_handoff.py, src/ai_video/canvas_planning.py, src/ai_video/planning/__init__.py and 3 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: sequence_continuity, sequence_continuity.py, src/ai_video/planning/sequence_continuity, src/ai_video/planning/sequence_continuity.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-047 — KEEP

- Location: `src/ai_video/planning/video_planner.py`
- Category: `orphan-file`
- Potential size: 896 LOC / 34.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_sequence_handoff.py, src/ai_video/planning/__init__.py, src/ai_video/planning/sequence_continuity.py and 9 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/planning/video_planner, src/ai_video/planning/video_planner.py, video_planner, video_planner.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-048 — KEEP

- Location: `src/ai_video/production/_asset_registry_validation.py`
- Category: `orphan-file`
- Potential size: 211 LOC / 8.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/models.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _asset_registry_validation, _asset_registry_validation.py, src/ai_video/production/_asset_registry_validation, src/ai_video/production/_asset_registry_validation.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-049 — KEEP

- Location: `src/ai_video/production/_caption_quality_p6.py`
- Category: `orphan-file`
- Potential size: 378 LOC / 13.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/ecommerce_ad_coordinator.py, src/ai_video/production/ecommerce_job_review.py, tests/production_e2e_support.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _caption_quality_p6, _caption_quality_p6.py, src/ai_video/production/_caption_quality_p6, src/ai_video/production/_caption_quality_p6.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-050 — KEEP

- Location: `src/ai_video/production/_caption_review_models.py`
- Category: `orphan-file`
- Potential size: 157 LOC / 6.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/models.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _caption_review_models, _caption_review_models.py, src/ai_video/production/_caption_review_models, src/ai_video/production/_caption_review_models.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-051 — KEEP

- Location: `src/ai_video/production/_causal_prompt_context.py`
- Category: `orphan-file`
- Potential size: 97 LOC / 5.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_causal_state_expression.py, src/ai_video/production/_sequence_source.py, src/ai_video/production/seedance_source_expression.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _causal_prompt_context, _causal_prompt_context.py, src/ai_video/production/_causal_prompt_context, src/ai_video/production/_causal_prompt_context.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-052 — KEEP

- Location: `src/ai_video/production/_causal_state_expression.py`
- Category: `orphan-file`
- Potential size: 91 LOC / 4.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_h3_prompt.py, src/ai_video/production/_remote_video_native_prompt.py, src/ai_video/production/generation_evaluation.py and 5 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _causal_state_expression, _causal_state_expression.py, src/ai_video/production/_causal_state_expression, src/ai_video/production/_causal_state_expression.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-053 — KEEP

- Location: `src/ai_video/production/_commercial_project_reader.py`
- Category: `orphan-file`
- Potential size: 515 LOC / 21.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/_commercial_video_planning.py, src/ai_video/production/_state_commit_dependency.py, src/ai_video/production/commercial_video_validation.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _commercial_project_reader, _commercial_project_reader.py, src/ai_video/production/_commercial_project_reader, src/ai_video/production/_commercial_project_reader.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-054 — KEEP

- Location: `src/ai_video/production/_commercial_source_state.py`
- Category: `orphan-file`
- Potential size: 170 LOC / 6.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_provider_manifest_fields.py, src/ai_video/production/models.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _commercial_source_state, _commercial_source_state.py, src/ai_video/production/_commercial_source_state, src/ai_video/production/_commercial_source_state.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-055 — KEEP

- Location: `src/ai_video/production/_composition_native_audio.py`
- Category: `orphan-file`
- Potential size: 193 LOC / 8.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/composition.py, tests/test_canvas_imported_audio_retime.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _composition_native_audio, _composition_native_audio.py, src/ai_video/production/_composition_native_audio, src/ai_video/production/_composition_native_audio.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-056 — KEEP

- Location: `src/ai_video/production/_composition_source_duration.py`
- Category: `orphan-file`
- Potential size: 57 LOC / 2.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/composition.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _composition_source_duration, _composition_source_duration.py, src/ai_video/production/_composition_source_duration, src/ai_video/production/_composition_source_duration.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-057 — KEEP

- Location: `src/ai_video/production/_composition_visual.py`
- Category: `orphan-file`
- Potential size: 280 LOC / 11.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/composition.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _composition_visual, _composition_visual.py, src/ai_video/production/_composition_visual, src/ai_video/production/_composition_visual.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-058 — KEEP

- Location: `src/ai_video/production/_creative_project_reader.py`
- Category: `orphan-file`
- Potential size: 60 LOC / 2.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/project.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _creative_project_reader, _creative_project_reader.py, src/ai_video/production/_creative_project_reader, src/ai_video/production/_creative_project_reader.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-059 — KEEP

- Location: `src/ai_video/production/_dependency_authoring.py`
- Category: `orphan-file`
- Potential size: 334 LOC / 12.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_dependencies.py, src/ai_video/production/dependency.py, src/ai_video/production/minimax_speech_batch.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _dependency_authoring, _dependency_authoring.py, src/ai_video/production/_dependency_authoring, src/ai_video/production/_dependency_authoring.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-060 — KEEP

- Location: `src/ai_video/production/_dependency_primitives.py`
- Category: `orphan-file`
- Potential size: 27 LOC / 1.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_dependency_authoring.py, src/ai_video/production/dependency.py, src/ai_video/production/video_pre_generation.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _dependency_primitives, _dependency_primitives.py, src/ai_video/production/_dependency_primitives, src/ai_video/production/_dependency_primitives.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-061 — KEEP

- Location: `src/ai_video/production/_dependency_types.py`
- Category: `orphan-file`
- Potential size: 13 LOC / 398 B
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/models.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _dependency_types, _dependency_types.py, src/ai_video/production/_dependency_types, src/ai_video/production/_dependency_types.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-062 — KEEP

- Location: `src/ai_video/production/_ecommerce_quality_gate_p6.py`
- Category: `orphan-file`
- Potential size: 388 LOC / 14.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/ecommerce_ad_coordinator.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _ecommerce_quality_gate_p6, _ecommerce_quality_gate_p6.py, src/ai_video/production/_ecommerce_quality_gate_p6, src/ai_video/production/_ecommerce_quality_gate_p6.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-063 — KEEP

- Location: `src/ai_video/production/_generation_history_schema.py`
- Category: `orphan-file`
- Potential size: 38 LOC / 1.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/models.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _generation_history_schema, _generation_history_schema.py, src/ai_video/production/_generation_history_schema, src/ai_video/production/_generation_history_schema.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-064 — KEEP

- Location: `src/ai_video/production/_grok_auth_lock.py`
- Category: `orphan-file`
- Potential size: 46 LOC / 2.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/grok_auth.py, tests/test_grok_auth.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _grok_auth_lock, _grok_auth_lock.py, src/ai_video/production/_grok_auth_lock, src/ai_video/production/_grok_auth_lock.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-065 — KEEP

- Location: `src/ai_video/production/_h3_prompt.py`
- Category: `orphan-file`
- Potential size: 598 LOC / 24.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/comfy_t8_native_turbo_video.py, src/ai_video/production/comfy_t8_turbo_video.py, src/ai_video/production/comfy_t8_video.py and 6 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _h3_prompt, _h3_prompt.py, src/ai_video/production/_h3_prompt, src/ai_video/production/_h3_prompt.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-066 — KEEP

- Location: `src/ai_video/production/_hyperframes_audio.py`
- Category: `orphan-file`
- Potential size: 238 LOC / 8.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/hyperframes.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _hyperframes_audio, _hyperframes_audio.py, src/ai_video/production/_hyperframes_audio, src/ai_video/production/_hyperframes_audio.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-067 — KEEP

- Location: `src/ai_video/production/_hyperframes_native_audio.py`
- Category: `orphan-file`
- Potential size: 631 LOC / 21.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/hyperframes.py, tests/test_canvas_imported_audio_retime.py, tests/test_hyperframes_native_audio_retime.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _hyperframes_native_audio, _hyperframes_native_audio.py, src/ai_video/production/_hyperframes_native_audio, src/ai_video/production/_hyperframes_native_audio.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-068 — KEEP

- Location: `src/ai_video/production/_hyperframes_source.py`
- Category: `orphan-file`
- Potential size: 709 LOC / 27.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/hyperframes.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _hyperframes_source, _hyperframes_source.py, src/ai_video/production/_hyperframes_source, src/ai_video/production/_hyperframes_source.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-069 — KEEP

- Location: `src/ai_video/production/_image_project_reader.py`
- Category: `orphan-file`
- Potential size: 1,149 LOC / 45.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_image_activation.py, src/ai_video/production/_state_commit_image_recovery.py, src/ai_video/production/_state_commit_video.py and 8 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _image_project_reader, _image_project_reader.py, src/ai_video/production/_image_project_reader, src/ai_video/production/_image_project_reader.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-070 — KEEP

- Location: `src/ai_video/production/_image_video_lineage.py`
- Category: `orphan-file`
- Potential size: 173 LOC / 9.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_image_project_reader.py, tests/test_production_generated_video_e2e.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _image_video_lineage, _image_video_lineage.py, src/ai_video/production/_image_video_lineage, src/ai_video/production/_image_video_lineage.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-071 — KEEP

- Location: `src/ai_video/production/_immutable_models.py`
- Category: `orphan-file`
- Potential size: 15 LOC / 458 B
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/domain_acceptance.py, src/ai_video/production/models.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _immutable_models, _immutable_models.py, src/ai_video/production/_immutable_models, src/ai_video/production/_immutable_models.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-072 — KEEP

- Location: `src/ai_video/production/_lifecycle_schema.py`
- Category: `orphan-file`
- Potential size: 1,579 LOC / 62.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py, src/ai_video/production/_generation_feedback_reader.py, src/ai_video/production/_generation_history_schema.py and 15 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _lifecycle_schema, _lifecycle_schema.py, src/ai_video/production/_lifecycle_schema, src/ai_video/production/_lifecycle_schema.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-073 — KEEP

- Location: `src/ai_video/production/_paid_provider_project_reader.py`
- Category: `orphan-file`
- Potential size: 605 LOC / 28.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/_remote_image_reader.py, src/ai_video/production/_state_commit_paid_provider.py and 10 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _paid_provider_project_reader, _paid_provider_project_reader.py, src/ai_video/production/_paid_provider_project_reader, src/ai_video/production/_paid_provider_project_reader.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-074 — KEEP

- Location: `src/ai_video/production/_project_dependency_evidence.py`
- Category: `orphan-file`
- Potential size: 219 LOC / 8.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/project.py, tests/test_production_project.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _project_dependency_evidence, _project_dependency_evidence.py, src/ai_video/production/_project_dependency_evidence, src/ai_video/production/_project_dependency_evidence.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-075 — KEEP

- Location: `src/ai_video/production/_provider_manifest_fields.py`
- Category: `orphan-file`
- Potential size: 27 LOC / 1.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/models.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _provider_manifest_fields, _provider_manifest_fields.py, src/ai_video/production/_provider_manifest_fields, src/ai_video/production/_provider_manifest_fields.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-076 — KEEP

- Location: `src/ai_video/production/_remote_image_reader.py`
- Category: `orphan-file`
- Potential size: 120 LOC / 7.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_image_project_reader.py, src/ai_video/production/_state_commit_image_candidate.py, src/ai_video/production/_state_commit_paid_provider.py and 3 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _remote_image_reader, _remote_image_reader.py, src/ai_video/production/_remote_image_reader, src/ai_video/production/_remote_image_reader.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-077 — KEEP

- Location: `src/ai_video/production/_remote_video_native_prompt.py`
- Category: `orphan-file`
- Potential size: 371 LOC / 16.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_vidu_prompt.py, src/ai_video/production/grok.py, src/ai_video/production/metaso_h3.py and 11 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _remote_video_native_prompt, _remote_video_native_prompt.py, src/ai_video/production/_remote_video_native_prompt, src/ai_video/production/_remote_video_native_prompt.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-078 — KEEP

- Location: `src/ai_video/production/_remote_video_product_prompt.py`
- Category: `orphan-file`
- Potential size: 18 LOC / 1005 B
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_remote_video_native_prompt.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _remote_video_product_prompt, _remote_video_product_prompt.py, src/ai_video/production/_remote_video_product_prompt, src/ai_video/production/_remote_video_product_prompt.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-079 — KEEP

- Location: `src/ai_video/production/_render_source_validation.py`
- Category: `orphan-file`
- Potential size: 117 LOC / 5.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/project.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _render_source_validation, _render_source_validation.py, src/ai_video/production/_render_source_validation, src/ai_video/production/_render_source_validation.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-080 — KEEP

- Location: `src/ai_video/production/_repair_freshness.py`
- Category: `orphan-file`
- Potential size: 44 LOC / 1.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_transaction.py, src/ai_video/quality_intelligence/_capture_p6.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _repair_freshness, _repair_freshness.py, src/ai_video/production/_repair_freshness, src/ai_video/production/_repair_freshness.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-081 — KEEP

- Location: `src/ai_video/production/_review_project_reader.py`
- Category: `orphan-file`
- Potential size: 118 LOC / 4.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/project.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _review_project_reader, _review_project_reader.py, src/ai_video/production/_review_project_reader, src/ai_video/production/_review_project_reader.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-082 — KEEP

- Location: `src/ai_video/production/_sequence_source.py`
- Category: `orphan-file`
- Potential size: 316 LOC / 20.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_composition.py, src/ai_video/canvas_handoff.py, src/ai_video/canvas_planning.py and 11 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _sequence_source, _sequence_source.py, src/ai_video/production/_sequence_source, src/ai_video/production/_sequence_source.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-083 — KEEP

- Location: `src/ai_video/production/_shot_router_contracts.py`
- Category: `orphan-file`
- Potential size: 1,034 LOC / 42.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/generation_feedback_driver.py, src/ai_video/canvas_planning.py, src/ai_video/planning/sequence_continuity.py and 10 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _shot_router_contracts, _shot_router_contracts.py, src/ai_video/production/_shot_router_contracts, src/ai_video/production/_shot_router_contracts.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-084 — KEEP

- Location: `src/ai_video/production/_shot_visual_resolver.py`
- Category: `orphan-file`
- Potential size: 11 LOC / 436 B
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/shot_router.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _shot_visual_resolver, _shot_visual_resolver.py, src/ai_video/production/_shot_visual_resolver, src/ai_video/production/_shot_visual_resolver.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-085 — KEEP

- Location: `src/ai_video/production/_state_lifecycle.py`
- Category: `orphan-file`
- Potential size: 15 LOC / 325 B
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/models.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _state_lifecycle, _state_lifecycle.py, src/ai_video/production/_state_lifecycle, src/ai_video/production/_state_lifecycle.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-086 — KEEP

- Location: `src/ai_video/production/_video_capability_fingerprint.py`
- Category: `orphan-file`
- Potential size: 140 LOC / 4.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_video_requirement_routing.py, src/ai_video/production/shot_router.py, src/ai_video/production/video.py and 9 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _video_capability_fingerprint, _video_capability_fingerprint.py, src/ai_video/production/_video_capability_fingerprint, src/ai_video/production/_video_capability_fingerprint.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-087 — KEEP

- Location: `src/ai_video/production/_video_continuity.py`
- Category: `orphan-file`
- Potential size: 760 LOC / 33.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/sequence_continuity.py, src/ai_video/production/shot_continuity_m0_operator.py, src/ai_video/production/shot_continuity_motion_tail.py and 9 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _video_continuity, _video_continuity.py, src/ai_video/production/_video_continuity, src/ai_video/production/_video_continuity.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-088 — KEEP

- Location: `src/ai_video/production/_video_hero_routing.py`
- Category: `orphan-file`
- Potential size: 12 LOC / 657 B
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/shot_router.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _video_hero_routing, _video_hero_routing.py, src/ai_video/production/_video_hero_routing, src/ai_video/production/_video_hero_routing.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-089 — KEEP

- Location: `src/ai_video/production/_video_intent_validation.py`
- Category: `orphan-file`
- Potential size: 400 LOC / 16.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/video_planner.py, src/ai_video/production/_h3_prompt.py, src/ai_video/production/_remote_video_native_prompt.py and 7 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _video_intent_validation, _video_intent_validation.py, src/ai_video/production/_video_intent_validation, src/ai_video/production/_video_intent_validation.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-090 — KEEP

- Location: `src/ai_video/production/_video_project_reader.py`
- Category: `orphan-file`
- Potential size: 1,569 LOC / 66.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_commercial_project_reader.py, src/ai_video/production/_generation_feedback_reader.py, src/ai_video/production/_image_project_reader.py and 24 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _video_project_reader, _video_project_reader.py, src/ai_video/production/_video_project_reader, src/ai_video/production/_video_project_reader.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-091 — KEEP

- Location: `src/ai_video/production/_video_requirement_routing.py`
- Category: `orphan-file`
- Potential size: 786 LOC / 29.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_source_expression.py, src/ai_video/canvas_visual_style.py, src/ai_video/production/_shot_router_contracts.py and 8 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _video_requirement_routing, _video_requirement_routing.py, src/ai_video/production/_video_requirement_routing, src/ai_video/production/_video_requirement_routing.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-092 — KEEP

- Location: `src/ai_video/production/_vidu_prompt.py`
- Category: `orphan-file`
- Potential size: 280 LOC / 12.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_vidu_subjects.py, src/ai_video/production/vidu.py, tests/test_production_vidu_prompt.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _vidu_prompt, _vidu_prompt.py, src/ai_video/production/_vidu_prompt, src/ai_video/production/_vidu_prompt.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-093 — KEEP

- Location: `src/ai_video/production/_vidu_subjects.py`
- Category: `orphan-file`
- Potential size: 66 LOC / 4.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/generation_execution.py, src/ai_video/production/video_compiler.py, src/ai_video/production/vidu.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _vidu_subjects, _vidu_subjects.py, src/ai_video/production/_vidu_subjects, src/ai_video/production/_vidu_subjects.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-094 — KEEP

- Location: `src/ai_video/production/_voice_project_reader.py`
- Category: `orphan-file`
- Potential size: 264 LOC / 10.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_paid_provider.py, src/ai_video/production/_state_commit_voice_intent.py, src/ai_video/production/project.py and 3 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _voice_project_reader, _voice_project_reader.py, src/ai_video/production/_voice_project_reader, src/ai_video/production/_voice_project_reader.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-095 — KEEP

- Location: `src/ai_video/production/ad_composition.py`
- Category: `orphan-file`
- Potential size: 84 LOC / 3.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_composition_visual.py, src/ai_video/production/composition.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: ad_composition, ad_composition.py, src/ai_video/production/ad_composition, src/ai_video/production/ad_composition.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-096 — KEEP

- Location: `src/ai_video/production/ad_creative.py`
- Category: `orphan-file`
- Potential size: 345 LOC / 13.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, tests/test_production_delivery_packager.py, tests/test_production_ecommerce_job.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: ad_creative, ad_creative.py, src/ai_video/production/ad_creative, src/ai_video/production/ad_creative.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-097 — KEEP

- Location: `src/ai_video/production/ad_creative_review.py`
- Category: `orphan-file`
- Potential size: 330 LOC / 11.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: ad_creative_review, ad_creative_review.py, src/ai_video/production/ad_creative_review, src/ai_video/production/ad_creative_review.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-098 — KEEP

- Location: `src/ai_video/production/ad_creative_types.py`
- Category: `orphan-file`
- Potential size: 472 LOC / 20.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/_ecommerce_quality_gate_p6.py, src/ai_video/production/ad_creative.py and 18 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: ad_creative_types, ad_creative_types.py, src/ai_video/production/ad_creative_types, src/ai_video/production/ad_creative_types.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-099 — KEEP

- Location: `src/ai_video/production/artifact_contracts.py`
- Category: `orphan-file`
- Potential size: 51 LOC / 1.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/creative_goal_binding.py, scripts/visual_quality_report.py, src/ai_video/canvas_source_revision.py and 68 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: artifact_contracts, artifact_contracts.py, src/ai_video/production/artifact_contracts, src/ai_video/production/artifact_contracts.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-100 — KEEP

- Location: `src/ai_video/production/audio.py`
- Category: `orphan-file`
- Potential size: 1,270 LOC / 46.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/minimax_speech_batch.py, src/ai_video/production/__init__.py, src/ai_video/production/_generated_video_audio_contracts.py and 32 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: audio, audio.py, src/ai_video/production/audio, src/ai_video/production/audio.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-101 — KEEP

- Location: `src/ai_video/production/audio_retime_contracts.py`
- Category: `orphan-file`
- Potential size: 89 LOC / 3.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_composition_native_audio.py, src/ai_video/production/_hyperframes_native_audio.py, src/ai_video/production/_render_source_validation.py and 4 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: audio_retime_contracts, audio_retime_contracts.py, src/ai_video/production/audio_retime_contracts, src/ai_video/production/audio_retime_contracts.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-102 — KEEP

- Location: `src/ai_video/production/authoring_input.py`
- Category: `orphan-file`
- Potential size: 35 LOC / 1.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_authoring.py, src/ai_video/canvas_image_provenance.py, src/ai_video/canvas_project_data.py and 7 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: authoring_input, authoring_input.py, src/ai_video/production/authoring_input, src/ai_video/production/authoring_input.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-103 — KEEP

- Location: `src/ai_video/production/caption_quality.py`
- Category: `orphan-file`
- Potential size: 520 LOC / 20.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_caption_quality_p6.py, src/ai_video/production/_review_project_reader.py, src/ai_video/production/_state_commit_repair.py and 5 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: caption_quality, caption_quality.py, src/ai_video/production/caption_quality, src/ai_video/production/caption_quality.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-104 — KEEP

- Location: `src/ai_video/production/caption_quality_contracts.py`
- Category: `orphan-file`
- Potential size: 314 LOC / 13.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_caption_quality_p6.py, src/ai_video/production/_caption_review_models.py, src/ai_video/production/caption_quality.py and 7 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: caption_quality_contracts, caption_quality_contracts.py, src/ai_video/production/caption_quality_contracts, src/ai_video/production/caption_quality_contracts.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-105 — KEEP

- Location: `src/ai_video/production/captions.py`
- Category: `orphan-file`
- Potential size: 844 LOC / 31.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_contracts.py, src/ai_video/production/_state_commit_voice_candidate.py, src/ai_video/production/caption_quality.py and 18 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: captions, captions.py, src/ai_video/production/captions, src/ai_video/production/captions.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-106 — KEEP

- Location: `src/ai_video/production/comfy_image.py`
- Category: `orphan-file`
- Potential size: 702 LOC / 28.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/check_p7_1_comfy_compatibility.py, scripts/smoke_p7_1_local_image.py, src/ai_video/canvas_image_workflow.py and 16 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: comfy_image, comfy_image.py, src/ai_video/production/comfy_image, src/ai_video/production/comfy_image.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-107 — KEEP

- Location: `src/ai_video/production/comfy_image_workflow_contract.py`
- Category: `orphan-file`
- Potential size: 304 LOC / 11.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/comfy_image.py, tests/test_production_comfy_masked_image.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: comfy_image_workflow_contract, comfy_image_workflow_contract.py, src/ai_video/production/comfy_image_workflow_contract, src/ai_video/production/comfy_image_workflow_contract.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-108 — KEEP

- Location: `src/ai_video/production/comfy_t8_native_turbo_profile.py`
- Category: `orphan-file`
- Potential size: 685 LOC / 26.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/comfy_t8_native_turbo_video.py, tests/test_production_comfy_t8_native_long_video.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: comfy_t8_native_turbo_profile, comfy_t8_native_turbo_profile.py, src/ai_video/production/comfy_t8_native_turbo_profile, src/ai_video/production/comfy_t8_native_turbo_profile.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-109 — KEEP

- Location: `src/ai_video/production/comfy_t8_native_turbo_video.py`
- Category: `orphan-file`
- Potential size: 740 LOC / 29.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/video_compiler.py, tests/test_generation_local_wiring.py and 4 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: comfy_t8_native_turbo_video, comfy_t8_native_turbo_video.py, src/ai_video/production/comfy_t8_native_turbo_video, src/ai_video/production/comfy_t8_native_turbo_video.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-110 — KEEP

- Location: `src/ai_video/production/comfy_t8_turbo_video.py`
- Category: `orphan-file`
- Potential size: 833 LOC / 32.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, tests/test_production_comfy_t8_turbo_video.py, tests/test_production_local_h3_provider_family.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: comfy_t8_turbo_video, comfy_t8_turbo_video.py, src/ai_video/production/comfy_t8_turbo_video, src/ai_video/production/comfy_t8_turbo_video.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-111 — KEEP

- Location: `src/ai_video/production/comfy_t8_video.py`
- Category: `orphan-file`
- Potential size: 977 LOC / 38.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/comfy_t8_native_turbo_video.py, src/ai_video/production/comfy_t8_turbo_video.py and 5 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: comfy_t8_video, comfy_t8_video.py, src/ai_video/production/comfy_t8_video, src/ai_video/production/comfy_t8_video.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-112 — KEEP

- Location: `src/ai_video/production/comfy_video.py`
- Category: `orphan-file`
- Potential size: 921 LOC / 36.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/shot_continuity_source_qualification.py, src/ai_video/production/shot_continuity_source_stack.py and 5 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: comfy_video, comfy_video.py, src/ai_video/production/comfy_video, src/ai_video/production/comfy_video.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-113 — KEEP

- Location: `src/ai_video/production/commercial_dependency.py`
- Category: `orphan-file`
- Potential size: 231 LOC / 8.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/_commercial_project_reader.py, src/ai_video/production/_state_commit_commercial_source.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: commercial_dependency, commercial_dependency.py, src/ai_video/production/commercial_dependency, src/ai_video/production/commercial_dependency.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-114 — KEEP

- Location: `src/ai_video/production/commercial_graphics.py`
- Category: `orphan-file`
- Potential size: 205 LOC / 8.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/_composition_visual.py, src/ai_video/production/_hyperframes_source.py and 14 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: commercial_graphics, commercial_graphics.py, src/ai_video/production/commercial_graphics, src/ai_video/production/commercial_graphics.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-115 — KEEP

- Location: `src/ai_video/production/commercial_image_import.py`
- Category: `orphan-file`
- Potential size: 104 LOC / 4.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: commercial_image_import, commercial_image_import.py, src/ai_video/production/commercial_image_import, src/ai_video/production/commercial_image_import.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-116 — KEEP

- Location: `src/ai_video/production/commercial_reference.py`
- Category: `orphan-file`
- Potential size: 112 LOC / 4.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/_commercial_video_planning.py, src/ai_video/planning/_planner_models.py, src/ai_video/production/__init__.py and 7 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: commercial_reference, commercial_reference.py, src/ai_video/production/commercial_reference, src/ai_video/production/commercial_reference.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-117 — KEEP

- Location: `src/ai_video/production/commercial_source_preparation.py`
- Category: `orphan-file`
- Potential size: 341 LOC / 16.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/_commercial_video_planning.py, src/ai_video/planning/_planner_models.py, src/ai_video/production/__init__.py and 8 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: commercial_source_preparation, commercial_source_preparation.py, src/ai_video/production/commercial_source_preparation, src/ai_video/production/commercial_source_preparation.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-118 — KEEP

- Location: `src/ai_video/production/commercial_video_contracts.py`
- Category: `orphan-file`
- Potential size: 114 LOC / 4.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_shot_router_contracts.py, src/ai_video/production/commercial_video_validation.py, src/ai_video/production/video.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: commercial_video_contracts, commercial_video_contracts.py, src/ai_video/production/commercial_video_contracts, src/ai_video/production/commercial_video_contracts.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-119 — KEEP

- Location: `src/ai_video/production/commercial_visual_review.py`
- Category: `orphan-file`
- Potential size: 376 LOC / 15.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/_commercial_project_reader.py, src/ai_video/production/_state_commit_commercial_source.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: commercial_visual_review, commercial_visual_review.py, src/ai_video/production/commercial_visual_review, src/ai_video/production/commercial_visual_review.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-120 — KEEP

- Location: `src/ai_video/production/composition.py`
- Category: `orphan-file`
- Potential size: 832 LOC / 29.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_composition.py, src/ai_video/production/__init__.py, src/ai_video/production/_hyperframes_native_audio.py and 28 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: composition, composition.py, src/ai_video/production/composition, src/ai_video/production/composition.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-121 — KEEP

- Location: `src/ai_video/production/composition_contracts.py`
- Category: `orphan-file`
- Potential size: 672 LOC / 28.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_composition.py, src/ai_video/canvas_dependencies.py, src/ai_video/canvas_image.py and 31 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: composition_contracts, composition_contracts.py, src/ai_video/production/composition_contracts, src/ai_video/production/composition_contracts.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-122 — KEEP

- Location: `src/ai_video/production/continuity_evaluator.py`
- Category: `orphan-file`
- Potential size: 1,099 LOC / 43.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/continuity_onnx_backend.py, src/ai_video/production/local_continuity_reviewer.py, src/ai_video/production/shot_continuity_source_operator.py and 4 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: continuity_evaluator, continuity_evaluator.py, src/ai_video/production/continuity_evaluator, src/ai_video/production/continuity_evaluator.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-123 — KEEP

- Location: `src/ai_video/production/continuity_onnx_backend.py`
- Category: `orphan-file`
- Potential size: 616 LOC / 24.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/local_continuity_reviewer.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: continuity_onnx_backend, continuity_onnx_backend.py, src/ai_video/production/continuity_onnx_backend, src/ai_video/production/continuity_onnx_backend.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-124 — KEEP

- Location: `src/ai_video/production/continuity_review_coordinator.py`
- Category: `orphan-file`
- Potential size: 622 LOC / 24.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/provider_console_continuity.py, tests/test_production_continuity_review_coordinator.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: continuity_review_coordinator, continuity_review_coordinator.py, src/ai_video/production/continuity_review_coordinator, src/ai_video/production/continuity_review_coordinator.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-125 — KEEP

- Location: `src/ai_video/production/delivery_packager.py`
- Category: `orphan-file`
- Potential size: 687 LOC / 25.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/ecommerce_job_review.py, tests/test_production_delivery_packager.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: delivery_packager, delivery_packager.py, src/ai_video/production/delivery_packager, src/ai_video/production/delivery_packager.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-126 — KEEP

- Location: `src/ai_video/production/dependency.py`
- Category: `orphan-file`
- Potential size: 1,704 LOC / 68.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_dependencies.py, src/ai_video/production/_commercial_project_reader.py, src/ai_video/production/_dependency_authoring.py and 58 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: dependency, dependency.py, src/ai_video/production/dependency, src/ai_video/production/dependency.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-127 — KEEP

- Location: `src/ai_video/production/domain_acceptance.py`
- Category: `orphan-file`
- Potential size: 423 LOC / 20.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/production_strategy.py, src/ai_video/production/_caption_review_models.py, src/ai_video/production/_state_commit_review.py and 32 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: domain_acceptance, domain_acceptance.py, src/ai_video/production/domain_acceptance, src/ai_video/production/domain_acceptance.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-128 — KEEP

- Location: `src/ai_video/production/ecommerce_ad_coordinator.py`
- Category: `orphan-file`
- Potential size: 1,038 LOC / 38.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/ecommerce_job.py, src/ai_video/production/ecommerce_job_execution.py and 8 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: ecommerce_ad_coordinator, ecommerce_ad_coordinator.py, src/ai_video/production/ecommerce_ad_coordinator, src/ai_video/production/ecommerce_ad_coordinator.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-129 — KEEP

- Location: `src/ai_video/production/ecommerce_job.py`
- Category: `orphan-file`
- Potential size: 813 LOC / 36.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, tests/test_production_delivery_packager.py, tests/test_production_ecommerce_job.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: ecommerce_job, ecommerce_job.py, src/ai_video/production/ecommerce_job, src/ai_video/production/ecommerce_job.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-130 — KEEP

- Location: `src/ai_video/production/ecommerce_job_assembly.py`
- Category: `orphan-file`
- Potential size: 559 LOC / 21.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/delivery_packager.py, src/ai_video/production/ecommerce_job.py and 6 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: ecommerce_job_assembly, ecommerce_job_assembly.py, src/ai_video/production/ecommerce_job_assembly, src/ai_video/production/ecommerce_job_assembly.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-131 — KEEP

- Location: `src/ai_video/production/ecommerce_job_compiler.py`
- Category: `orphan-file`
- Potential size: 378 LOC / 13.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, tests/test_production_delivery_packager.py, tests/test_production_ecommerce_job.py and 3 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: ecommerce_job_compiler, ecommerce_job_compiler.py, src/ai_video/production/ecommerce_job_compiler, src/ai_video/production/ecommerce_job_compiler.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-132 — KEEP

- Location: `src/ai_video/production/ecommerce_job_contracts.py`
- Category: `orphan-file`
- Potential size: 574 LOC / 21.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/delivery_packager.py, src/ai_video/production/ecommerce_ad_coordinator.py and 14 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: ecommerce_job_contracts, ecommerce_job_contracts.py, src/ai_video/production/ecommerce_job_contracts, src/ai_video/production/ecommerce_job_contracts.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-133 — KEEP

- Location: `src/ai_video/production/ecommerce_job_execution.py`
- Category: `orphan-file`
- Potential size: 261 LOC / 10.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/ecommerce_job.py, src/ai_video/production/ecommerce_job_projection.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: ecommerce_job_execution, ecommerce_job_execution.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-134 — KEEP

- Location: `src/ai_video/production/ecommerce_job_projection.py`
- Category: `orphan-file`
- Potential size: 540 LOC / 22.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/ecommerce_job.py, tests/test_production_ecommerce_job_projection.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: ecommerce_job_projection, ecommerce_job_projection.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-135 — KEEP

- Location: `src/ai_video/production/ecommerce_job_repair.py`
- Category: `orphan-file`
- Potential size: 690 LOC / 23.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/ecommerce_job.py, src/ai_video/production/ecommerce_job_execution.py, src/ai_video/production/ecommerce_job_projection.py and 3 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: ecommerce_job_repair, ecommerce_job_repair.py, src/ai_video/production/ecommerce_job_repair, src/ai_video/production/ecommerce_job_repair.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-136 — KEEP

- Location: `src/ai_video/production/ecommerce_job_review.py`
- Category: `orphan-file`
- Potential size: 334 LOC / 12.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/ecommerce_job.py, src/ai_video/production/ecommerce_job_projection.py and 5 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: ecommerce_job_review, ecommerce_job_review.py, src/ai_video/production/ecommerce_job_review, src/ai_video/production/ecommerce_job_review.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-137 — KEEP

- Location: `src/ai_video/production/ecommerce_media_acceptance.py`
- Category: `orphan-file`
- Potential size: 350 LOC / 13.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_video_commercial.py, src/ai_video/production/_video_project_reader.py, src/ai_video/production/commercial_execution.py and 21 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: ecommerce_media_acceptance, ecommerce_media_acceptance.py, src/ai_video/production/ecommerce_media_acceptance, src/ai_video/production/ecommerce_media_acceptance.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-138 — KEEP

- Location: `src/ai_video/production/ecommerce_quality_gate.py`
- Category: `orphan-file`
- Potential size: 691 LOC / 28.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/_ecommerce_quality_gate_p6.py, src/ai_video/production/delivery_packager.py and 8 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: ecommerce_quality_gate, ecommerce_quality_gate.py, src/ai_video/production/ecommerce_quality_gate, src/ai_video/production/ecommerce_quality_gate.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-139 — KEEP

- Location: `src/ai_video/production/elevenlabs.py`
- Category: `orphan-file`
- Potential size: 782 LOC / 27.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_production_elevenlabs.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: elevenlabs, elevenlabs.py, src/ai_video/production/elevenlabs, src/ai_video/production/elevenlabs.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-140 — KEEP

- Location: `src/ai_video/production/execution_stack_materialization.py`
- Category: `orphan-file`
- Potential size: 89 LOC / 3.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_p0_qualification.py, src/ai_video/production/_video_project_reader.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: execution_stack_materialization, execution_stack_materialization.py, src/ai_video/production/execution_stack_materialization, src/ai_video/production/execution_stack_materialization.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-141 — KEEP

- Location: `src/ai_video/production/final_output_contracts.py`
- Category: `orphan-file`
- Potential size: 106 LOC / 3.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/creative_goal_binding.py, scripts/visual_quality_report.py, src/ai_video/canvas_review.py and 17 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: final_output_contracts, final_output_contracts.py, src/ai_video/production/final_output_contracts, src/ai_video/production/final_output_contracts.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-142 — KEEP

- Location: `src/ai_video/production/final_output_review.py`
- Category: `orphan-file`
- Potential size: 348 LOC / 17.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/visual_quality_report.py, src/ai_video/canvas_review.py, src/ai_video/production/_ecommerce_quality_gate_p6.py and 12 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: final_output_review, final_output_review.py, src/ai_video/production/final_output_review, src/ai_video/production/final_output_review.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-143 — KEEP

- Location: `src/ai_video/production/generation_decision.py`
- Category: `orphan-file`
- Potential size: 793 LOC / 48.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/generation_feedback_driver.py, src/ai_video/production/_generation_feedback_reader.py, src/ai_video/production/_state_commit_generation_feedback.py and 22 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: generation_decision, generation_decision.py, src/ai_video/production/generation_decision, src/ai_video/production/generation_decision.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-144 — KEEP

- Location: `src/ai_video/production/generation_diagnosis.py`
- Category: `orphan-file`
- Potential size: 422 LOC / 22.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/s01_strategy_regression.py, src/ai_video/canvas_production.py, src/ai_video/production/_sequence_source.py and 26 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: generation_diagnosis, generation_diagnosis.py, src/ai_video/production/generation_diagnosis, src/ai_video/production/generation_diagnosis.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-145 — KEEP

- Location: `src/ai_video/production/generation_evaluation.py`
- Category: `orphan-file`
- Potential size: 377 LOC / 20.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/generation_feedback_driver.py, src/ai_video/canvas_handoff.py, src/ai_video/canvas_review.py and 28 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: generation_evaluation, generation_evaluation.py, src/ai_video/production/generation_evaluation, src/ai_video/production/generation_evaluation.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-146 — KEEP

- Location: `src/ai_video/production/generation_evaluation_criteria.py`
- Category: `orphan-file`
- Potential size: 137 LOC / 6.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/generation_evaluation.py, src/ai_video_mcp/generation_feedback.py, tests/test_current_shot_close_expression.py and 6 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: generation_evaluation_criteria, generation_evaluation_criteria.py, src/ai_video/production/generation_evaluation_criteria, src/ai_video/production/generation_evaluation_criteria.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-147 — KEEP

- Location: `src/ai_video/production/generation_execution.py`
- Category: `orphan-file`
- Potential size: 482 LOC / 23.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/sequence_continuity.py, src/ai_video/production/_generation_feedback_reader.py, src/ai_video/production/_sequence_source.py and 16 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: generation_execution, generation_execution.py, src/ai_video/production/generation_execution, src/ai_video/production/generation_execution.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-148 — KEEP

- Location: `src/ai_video/production/generation_experience.py`
- Category: `orphan-file`
- Potential size: 197 LOC / 9.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/generation_difficulty.py, src/ai_video/production/_generation_feedback_reader.py, src/ai_video/production/_state_commit_generation_feedback.py and 15 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: generation_experience, generation_experience.py, src/ai_video/production/generation_experience, src/ai_video/production/generation_experience.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-149 — KEEP

- Location: `src/ai_video/production/generation_feedback.py`
- Category: `orphan-file`
- Potential size: 630 LOC / 36.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_production.py, scripts/generation_feedback_driver.py, scripts/s01_strategy_regression.py and 37 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: generation_feedback, generation_feedback.py, src/ai_video/production/generation_feedback, src/ai_video/production/generation_feedback.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-150 — KEEP

- Location: `src/ai_video/production/generation_history_import.py`
- Category: `orphan-file`
- Potential size: 484 LOC / 23.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_generation_feedback_reader.py, src/ai_video/production/_state_commit_generation_history.py, tests/test_generation_history_import.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: generation_history_import, generation_history_import.py, src/ai_video/production/generation_history_import, src/ai_video/production/generation_history_import.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-151 — KEEP

- Location: `src/ai_video/production/generation_input_control.py`
- Category: `orphan-file`
- Potential size: 126 LOC / 6.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/generation_recipe.py, src/ai_video/production/requirement_semantics.py, src/ai_video/production/video_reference_controls.py and 3 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: generation_input_control, generation_input_control.py, src/ai_video/production/generation_input_control, src/ai_video/production/generation_input_control.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-152 — KEEP

- Location: `src/ai_video/production/generation_recipe.py`
- Category: `orphan-file`
- Potential size: 231 LOC / 11.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_shot_router_contracts.py, src/ai_video/production/generation_decision.py, src/ai_video/production/generation_diagnosis.py and 37 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: generation_recipe, generation_recipe.py, src/ai_video/production/generation_recipe, src/ai_video/production/generation_recipe.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-153 — KEEP

- Location: `src/ai_video/production/generation_runtime_repair.py`
- Category: `orphan-file`
- Potential size: 496 LOC / 23.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_recovery.py, src/ai_video/production/_generation_feedback_reader.py, src/ai_video/production/_state_commit_video_runtime_repair.py and 5 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: generation_runtime_repair, generation_runtime_repair.py, src/ai_video/production/generation_runtime_repair, src/ai_video/production/generation_runtime_repair.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-154 — KEEP

- Location: `src/ai_video/production/grok.py`
- Category: `orphan-file`
- Potential size: 838 LOC / 32.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_generation_provider_wiring.py, tests/test_grok_output_contract.py, tests/test_grok_video_operations.py and 4 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: grok, grok.py, src/ai_video/production/grok.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-155 — KEEP

- Location: `src/ai_video/production/grok_auth.py`
- Category: `orphan-file`
- Potential size: 682 LOC / 27.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/grok_auth.py, src/ai_video/production/grok_image.py, tests/test_grok_auth.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: grok_auth, grok_auth.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-156 — KEEP

- Location: `src/ai_video/production/grok_billing.py`
- Category: `orphan-file`
- Potential size: 142 LOC / 8.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/grok_auth.py, tests/test_grok_billing.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: grok_billing, grok_billing.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-157 — KEEP

- Location: `src/ai_video/production/grok_download.py`
- Category: `orphan-file`
- Potential size: 54 LOC / 1.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/grok.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: grok_download, grok_download.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-158 — KEEP

- Location: `src/ai_video/production/grok_image.py`
- Category: `orphan-file`
- Potential size: 560 LOC / 22.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_grok_remote_image_lifecycle.py, tests/test_production_grok_image.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: grok_image, grok_image.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-159 — KEEP

- Location: `src/ai_video/production/grok_image_bytes.py`
- Category: `orphan-file`
- Potential size: 33 LOC / 1.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_remote_image_reader.py, src/ai_video/production/grok_image.py, tests/test_grok_remote_image_lifecycle.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: grok_image_bytes.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-160 — KEEP

- Location: `src/ai_video/production/grok_profile.py`
- Category: `orphan-file`
- Potential size: 495 LOC / 17.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/grok.py, src/ai_video/production/grok_image.py, src/ai_video/production/grok_video_request.py and 8 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: grok_profile, grok_profile.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-161 — KEEP

- Location: `src/ai_video/production/grok_subscription.py`
- Category: `orphan-file`
- Potential size: 131 LOC / 6.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/grok.py, src/ai_video/production/grok_billing.py, src/ai_video/production/grok_image.py and 5 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: grok_subscription, grok_subscription.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-162 — KEEP

- Location: `src/ai_video/production/grok_video_controls.py`
- Category: `orphan-file`
- Potential size: 57 LOC / 2.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/grok_profile.py, tests/test_grok_video_capabilities.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: grok_video_controls, grok_video_controls.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-163 — KEEP

- Location: `src/ai_video/production/grok_video_measurement.py`
- Category: `orphan-file`
- Potential size: 35 LOC / 1.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_video_project_reader.py, src/ai_video/production/video_artifact.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: grok_video_measurement.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-164 — KEEP

- Location: `src/ai_video/production/grok_video_request.py`
- Category: `orphan-file`
- Potential size: 546 LOC / 21.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/grok.py, tests/test_generation_provider_wiring.py, tests/test_grok_video_operations.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: grok_video_request, grok_video_request.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-165 — KEEP

- Location: `src/ai_video/production/hashing.py`
- Category: `orphan-file`
- Potential size: 38 LOC / 1.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/composition_shadow.py, scripts/generation_feedback_driver.py, scripts/prepare_shot_continuity_endpoint_repair.py and 298 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: hashing, hashing.py, src/ai_video/production/hashing, src/ai_video/production/hashing.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-166 — KEEP

- Location: `src/ai_video/production/hyperframes.py`
- Category: `orphan-file`
- Potential size: 2,575 LOC / 100.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py, src/ai_video/production/__init__.py, src/ai_video/production/ecommerce_job_assembly.py and 17 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: hyperframes, hyperframes.py, src/ai_video/production/hyperframes, src/ai_video/production/hyperframes.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-167 — KEEP

- Location: `src/ai_video/production/image.py`
- Category: `orphan-file`
- Potential size: 1,245 LOC / 51.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/smoke_p7_1_local_image.py, src/ai_video/canvas_assets.py, src/ai_video/canvas_handoff.py and 34 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: image, image.py, src/ai_video/production/image, src/ai_video/production/image.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-168 — KEEP

- Location: `src/ai_video/production/image_bytes.py`
- Category: `orphan-file`
- Potential size: 107 LOC / 3.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/image.py, src/ai_video/production/image_edit_mask.py, src/ai_video/production/image_preparation.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: image_bytes, image_bytes.py, src/ai_video/production/image_bytes, src/ai_video/production/image_bytes.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-169 — KEEP

- Location: `src/ai_video/production/image_candidate.py`
- Category: `orphan-file`
- Potential size: 81 LOC / 5.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_image.py, tests/test_seedream_remote_image.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: image_candidate, image_candidate.py, src/ai_video/production/image_candidate, src/ai_video/production/image_candidate.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-170 — KEEP

- Location: `src/ai_video/production/image_candidate_frontier.py`
- Category: `orphan-file`
- Potential size: 47 LOC / 2.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/image.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: image_candidate_frontier, image_candidate_frontier.py, src/ai_video/production/image_candidate_frontier, src/ai_video/production/image_candidate_frontier.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-171 — KEEP

- Location: `src/ai_video/production/image_edit_mask.py`
- Category: `orphan-file`
- Potential size: 256 LOC / 9.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_image_workflow.py, src/ai_video/production/_image_project_reader.py, src/ai_video/production/_state_commit_image_intent.py and 3 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: image_edit_mask, image_edit_mask.py, src/ai_video/production/image_edit_mask, src/ai_video/production/image_edit_mask.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-172 — KEEP

- Location: `src/ai_video/production/image_import.py`
- Category: `orphan-file`
- Potential size: 889 LOC / 36.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/prepare_shot_continuity_endpoint_repair.py, scripts/prepare_shot_continuity_p0.py, src/ai_video/production/__init__.py and 8 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: image_import, image_import.py, src/ai_video/production/image_import, src/ai_video/production/image_import.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-173 — KEEP

- Location: `src/ai_video/production/image_import_video_frame.py`
- Category: `orphan-file`
- Potential size: 287 LOC / 11.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_handoff.py, src/ai_video/production/_image_project_reader.py, src/ai_video/production/_state_commit_bootstrap.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: image_import_video_frame, image_import_video_frame.py, src/ai_video/production/image_import_video_frame, src/ai_video/production/image_import_video_frame.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-174 — KEEP

- Location: `src/ai_video/production/image_materialization_failure.py`
- Category: `orphan-file`
- Potential size: 350 LOC / 15.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_image_project_reader.py, src/ai_video/production/_state_commit_image_recovery.py, src/ai_video/production/_state_commit_remote_image.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: image_materialization_failure, image_materialization_failure.py, src/ai_video/production/image_materialization_failure, src/ai_video/production/image_materialization_failure.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-175 — KEEP

- Location: `src/ai_video/production/image_preparation.py`
- Category: `orphan-file`
- Potential size: 489 LOC / 24.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py, src/ai_video/production/_image_project_reader.py, tests/test_canvas_image_preparation.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: image_preparation, image_preparation.py, src/ai_video/production/image_preparation, src/ai_video/production/image_preparation.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-176 — KEEP

- Location: `src/ai_video/production/local_continuity_reviewer.py`
- Category: `orphan-file`
- Potential size: 92 LOC / 3.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/continuity_review_coordinator.py, tests/test_production_continuity_review_coordinator.py, tests/test_production_local_continuity_reviewer.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: local_continuity_reviewer, local_continuity_reviewer.py, src/ai_video/production/local_continuity_reviewer, src/ai_video/production/local_continuity_reviewer.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-177 — KEEP

- Location: `src/ai_video/production/local_h3_provider_family.py`
- Category: `orphan-file`
- Potential size: 260 LOC / 9.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, tests/test_generation_local_wiring.py, tests/test_production_comfy_t8_native_long_video.py and 4 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: local_h3_provider_family, local_h3_provider_family.py, src/ai_video/production/local_h3_provider_family, src/ai_video/production/local_h3_provider_family.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-178 — KEEP

- Location: `src/ai_video/production/local_video.py`
- Category: `orphan-file`
- Potential size: 364 LOC / 12.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/_state_commit_video.py, src/ai_video/production/_video_project_reader.py and 21 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: local_video, local_video.py, src/ai_video/production/local_video, src/ai_video/production/local_video.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-179 — KEEP

- Location: `src/ai_video/production/manifest_schema.py`
- Category: `orphan-file`
- Potential size: 111 LOC / 2.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_caption_review_models.py, src/ai_video/production/_commercial_project_reader.py, src/ai_video/production/_commercial_source_state.py and 38 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: manifest_schema, manifest_schema.py, src/ai_video/production/manifest_schema, src/ai_video/production/manifest_schema.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-180 — KEEP

- Location: `src/ai_video/production/metaso_h3.py`
- Category: `orphan-file`
- Potential size: 449 LOC / 24.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/minimax_h3_max.py, tests/test_production_metaso_h3.py, tests/test_production_minimax_h3_max.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: metaso_h3, metaso_h3.py, src/ai_video/production/metaso_h3, src/ai_video/production/metaso_h3.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-181 — KEEP

- Location: `src/ai_video/production/minimax_h3.py`
- Category: `orphan-file`
- Potential size: 696 LOC / 25.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/metaso_h3.py, tests/test_generation_provider_wiring.py, tests/test_production_metaso_h3.py and 3 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: minimax_h3, minimax_h3.py, src/ai_video/production/minimax_h3, src/ai_video/production/minimax_h3.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-182 — KEEP

- Location: `src/ai_video/production/minimax_h3_max.py`
- Category: `orphan-file`
- Potential size: 141 LOC / 5.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_canvas_source_expression.py, tests/test_production_minimax_h3_max.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: minimax_h3_max, minimax_h3_max.py, src/ai_video/production/minimax_h3_max, src/ai_video/production/minimax_h3_max.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-183 — KEEP

- Location: `src/ai_video/production/minimax_hailuo.py`
- Category: `orphan-file`
- Potential size: 1,054 LOC / 38.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_generation_provider_wiring.py, tests/test_production_minimax_hailuo.py, tests/test_production_provider_neutral_adapters.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: minimax_hailuo, minimax_hailuo.py, src/ai_video/production/minimax_hailuo, src/ai_video/production/minimax_hailuo.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-184 — KEEP

- Location: `src/ai_video/production/minimax_speech.py`
- Category: `orphan-file`
- Potential size: 641 LOC / 22.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/minimax_speech_batch.py, src/ai_video/production/minimax_speech_batch.py, tests/test_production_minimax_speech_batch.py and 5 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: minimax_speech, minimax_speech.py, src/ai_video/production/minimax_speech, src/ai_video/production/minimax_speech.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-185 — KEEP

- Location: `src/ai_video/production/minimax_speech_batch.py`
- Category: `orphan-file`
- Potential size: 277 LOC / 16.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/minimax_speech_batch.py, tests/test_production_minimax_speech_batch.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: minimax_speech_batch, minimax_speech_batch.py, src/ai_video/production/minimax_speech_batch, src/ai_video/production/minimax_speech_batch.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-186 — KEEP

- Location: `src/ai_video/production/models.py`
- Category: `orphan-file`
- Potential size: 2,417 LOC / 93.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_production.py, scripts/minimax_speech_batch.py, scripts/prepare_shot_continuity_endpoint_repair.py and 383 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: models, models.py, src/ai_video/production/models, src/ai_video/production/models.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-187 — KEEP

- Location: `src/ai_video/production/paid_provider.py`
- Category: `orphan-file`
- Potential size: 734 LOC / 33.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/generation_feedback_driver.py, src/ai_video/production/__init__.py, src/ai_video/production/_generated_video_audio_contracts.py and 69 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: paid_provider, paid_provider.py, src/ai_video/production/paid_provider, src/ai_video/production/paid_provider.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-188 — KEEP

- Location: `src/ai_video/production/paid_provider_budget_extension.py`
- Category: `orphan-file`
- Potential size: 51 LOC / 2.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_paid_provider.py, src/ai_video/production/paid_provider.py, tests/test_production_paid_budget_extension.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: paid_provider_budget_extension, paid_provider_budget_extension.py, src/ai_video/production/paid_provider_budget_extension, src/ai_video/production/paid_provider_budget_extension.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-189 — KEEP

- Location: `src/ai_video/production/paid_provider_no_effect_reconciliation.py`
- Category: `orphan-file`
- Potential size: 512 LOC / 21.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_paid_provider_project_reader.py, src/ai_video/production/_state_commit_generation_feedback.py, src/ai_video/production/_state_commit_paid_provider.py and 4 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: paid_provider_no_effect_reconciliation, paid_provider_no_effect_reconciliation.py, src/ai_video/production/paid_provider_no_effect_reconciliation, src/ai_video/production/paid_provider_no_effect_reconciliation.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-190 — KEEP

- Location: `src/ai_video/production/paid_provider_submit_quota.py`
- Category: `orphan-file`
- Potential size: 354 LOC / 16.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_paid_provider.py, src/ai_video/production/_state_commit_video.py, src/ai_video/production/paid_provider.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: paid_provider_submit_quota, paid_provider_submit_quota.py, src/ai_video/production/paid_provider_submit_quota, src/ai_video/production/paid_provider_submit_quota.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-191 — KEEP

- Location: `src/ai_video/production/paths.py`
- Category: `orphan-file`
- Potential size: 1,118 LOC / 38.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_production.py, scripts/creative_goal_binding.py, scripts/materialize_shot_continuity_m0.py and 149 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: paths, paths.py, src/ai_video/production/paths, src/ai_video/production/paths.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-192 — KEEP

- Location: `src/ai_video/production/performance_authoring.py`
- Category: `orphan-file`
- Potential size: 98 LOC / 5.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_preflight.py, src/ai_video/production/generation_execution.py, src/ai_video/production/generation_feedback.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: performance_authoring, performance_authoring.py, src/ai_video/production/performance_authoring, src/ai_video/production/performance_authoring.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-193 — KEEP

- Location: `src/ai_video/production/production_responsibility.py`
- Category: `orphan-file`
- Potential size: 123 LOC / 7.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_preflight.py, src/ai_video/production/video_reference_controls.py, src/ai_video/production_planning.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: production_responsibility, production_responsibility.py, src/ai_video/production/production_responsibility, src/ai_video/production/production_responsibility.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-194 — KEEP

- Location: `src/ai_video/production/production_strategy_composition.py`
- Category: `orphan-file`
- Potential size: 60 LOC / 3.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/production_strategy_reader.py, tests/test_production_strategy_materialization.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: production_strategy_composition, production_strategy_composition.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-195 — KEEP

- Location: `src/ai_video/production/production_strategy_contracts.py`
- Category: `orphan-file`
- Potential size: 253 LOC / 10.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py, src/ai_video/planning/production_strategy.py, src/ai_video/production/models.py and 9 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: production_strategy_contracts, production_strategy_contracts.py, src/ai_video/production/production_strategy_contracts, src/ai_video/production/production_strategy_contracts.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-196 — KEEP

- Location: `src/ai_video/production/production_strategy_dependency.py`
- Category: `orphan-file`
- Potential size: 104 LOC / 4.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py, src/ai_video/production/minimax_speech_batch.py, src/ai_video/production/production_strategy_materialization.py and 4 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: production_strategy_dependency, production_strategy_dependency.py, src/ai_video/production/production_strategy_dependency, src/ai_video/production/production_strategy_dependency.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-197 — KEEP

- Location: `src/ai_video/production/production_strategy_materialization.py`
- Category: `orphan-file`
- Potential size: 646 LOC / 29.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_composition.py, src/ai_video/production_planning.py, tests/test_production_planning_service.py and 4 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: production_strategy_materialization, production_strategy_materialization.py, src/ai_video/production/production_strategy_materialization, src/ai_video/production/production_strategy_materialization.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-198 — KEEP

- Location: `src/ai_video/production/production_strategy_reader.py`
- Category: `orphan-file`
- Potential size: 571 LOC / 25.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_production.py, src/ai_video/canvas_authoring.py, src/ai_video/canvas_composition.py and 29 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: production_strategy_reader, production_strategy_reader.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-199 — KEEP

- Location: `src/ai_video/production/project.py`
- Category: `orphan-file`
- Potential size: 1,589 LOC / 64.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_sequence_handoff.py, scripts/materialize_shot_continuity_m0.py, scripts/minimax_speech_batch.py and 174 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: project, project.py, src/ai_video/production/project, src/ai_video/production/project.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-200 — KEEP

- Location: `src/ai_video/production/quality_gate_coordinator.py`
- Category: `orphan-file`
- Potential size: 483 LOC / 18.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_caption_quality_p6.py, src/ai_video/production/_ecommerce_quality_gate_p6.py, src/ai_video/production/ecommerce_ad_coordinator.py and 7 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: quality_gate_coordinator, quality_gate_coordinator.py, src/ai_video/production/quality_gate_coordinator, src/ai_video/production/quality_gate_coordinator.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-201 — KEEP

- Location: `src/ai_video/production/registry.py`
- Category: `orphan-file`
- Potential size: 233 LOC / 8.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/prepare_shot_continuity_endpoint_repair.py, scripts/prepare_shot_continuity_p0.py, src/ai_video/canvas_assets.py and 62 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: registry, registry.py, src/ai_video/production/registry, src/ai_video/production/registry.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-202 — KEEP

- Location: `src/ai_video/production/remote_image.py`
- Category: `orphan-file`
- Potential size: 61 LOC / 3.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_image_project_reader.py, src/ai_video/production/_state_commit_remote_image.py, src/ai_video/production/grok_image.py and 8 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: remote_image, remote_image.py, src/ai_video/production/remote_image, src/ai_video/production/remote_image.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-203 — KEEP

- Location: `src/ai_video/production/remote_media.py`
- Category: `orphan-file`
- Potential size: 188 LOC / 6.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/grok.py, src/ai_video/production/seedance.py and 4 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: remote_media, remote_media.py, src/ai_video/production/remote_media, src/ai_video/production/remote_media.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-204 — KEEP

- Location: `src/ai_video/production/renderer_audio_contracts.py`
- Category: `orphan-file`
- Potential size: 56 LOC / 2.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/models.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: renderer_audio_contracts, renderer_audio_contracts.py, src/ai_video/production/renderer_audio_contracts, src/ai_video/production/renderer_audio_contracts.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-205 — KEEP

- Location: `src/ai_video/production/repair_input_admission.py`
- Category: `orphan-file`
- Potential size: 517 LOC / 28.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py, src/ai_video/production/_composition_native_audio.py, src/ai_video/production/_composition_visual.py and 8 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: repair_input_admission, repair_input_admission.py, src/ai_video/production/repair_input_admission, src/ai_video/production/repair_input_admission.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-206 — KEEP

- Location: `src/ai_video/production/requirement_semantics.py`
- Category: `orphan-file`
- Potential size: 243 LOC / 11.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_review.py, src/ai_video/production/domain_acceptance.py, src/ai_video/production/generation_evaluation.py and 8 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: requirement_semantics, requirement_semantics.py, src/ai_video/production/requirement_semantics, src/ai_video/production/requirement_semantics.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-207 — KEEP

- Location: `src/ai_video/production/review.py`
- Category: `orphan-file`
- Potential size: 854 LOC / 34.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_handoff.py, src/ai_video/canvas_review.py, src/ai_video/production/_caption_quality_p6.py and 27 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: review, review.py, src/ai_video/production/review, src/ai_video/production/review.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-208 — KEEP

- Location: `src/ai_video/production/seedance_asset.py`
- Category: `orphan-file`
- Potential size: 871 LOC / 36.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/generation_feedback_driver.py, src/ai_video/production/__init__.py, src/ai_video/production/seedance.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: seedance_asset, seedance_asset.py, src/ai_video/production/seedance_asset, src/ai_video/production/seedance_asset.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-209 — KEEP

- Location: `src/ai_video/production/seedance_capabilities.py`
- Category: `orphan-file`
- Potential size: 829 LOC / 31.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/seedance.py, src/ai_video/production/seedance_profile.py, tests/test_production_provider_neutral_adapters.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: seedance_capabilities, seedance_capabilities.py, src/ai_video/production/seedance_capabilities, src/ai_video/production/seedance_capabilities.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-210 — KEEP

- Location: `src/ai_video/production/seedance_local_video.py`
- Category: `orphan-file`
- Potential size: 878 LOC / 33.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/__init__.py, src/ai_video/production/seedance.py, src/ai_video/production/seedance_mixed_reference.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: seedance_local_video, seedance_local_video.py, src/ai_video/production/seedance_local_video, src/ai_video/production/seedance_local_video.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-211 — KEEP

- Location: `src/ai_video/production/seedance_mixed_reference.py`
- Category: `orphan-file`
- Potential size: 203 LOC / 10.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/seedance.py, tests/test_production_seedance_mixed_reference.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: seedance_mixed_reference, seedance_mixed_reference.py, src/ai_video/production/seedance_mixed_reference, src/ai_video/production/seedance_mixed_reference.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-212 — KEEP

- Location: `src/ai_video/production/seedance_native_prompt.py`
- Category: `orphan-file`
- Potential size: 154 LOC / 9.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/seedance.py, tests/test_production_seedance_mixed_reference.py, tests/test_seedance_source_prompt.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: seedance_native_prompt, seedance_native_prompt.py, src/ai_video/production/seedance_native_prompt, src/ai_video/production/seedance_native_prompt.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-213 — KEEP

- Location: `src/ai_video/production/seedance_profile.py`
- Category: `orphan-file`
- Potential size: 257 LOC / 9.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/generation_feedback_driver.py, src/ai_video/production/seedance.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: seedance_profile, seedance_profile.py, src/ai_video/production/seedance_profile, src/ai_video/production/seedance_profile.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-214 — KEEP

- Location: `src/ai_video/production/seedance_reference_duration.py`
- Category: `orphan-file`
- Potential size: 54 LOC / 1.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/seedance.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: seedance_reference_duration, seedance_reference_duration.py, src/ai_video/production/seedance_reference_duration, src/ai_video/production/seedance_reference_duration.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-215 — KEEP

- Location: `src/ai_video/production/seedance_reference_image.py`
- Category: `orphan-file`
- Potential size: 33 LOC / 992 B
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/seedance_asset.py, tests/test_production_seedance_mixed_reference.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: seedance_reference_image, seedance_reference_image.py, src/ai_video/production/seedance_reference_image, src/ai_video/production/seedance_reference_image.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-216 — KEEP

- Location: `src/ai_video/production/seedance_rejection.py`
- Category: `orphan-file`
- Potential size: 51 LOC / 2.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/seedance.py, tests/test_production_seedance_rejection.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: seedance_rejection, seedance_rejection.py, src/ai_video/production/seedance_rejection, src/ai_video/production/seedance_rejection.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-217 — KEEP

- Location: `src/ai_video/production/seedance_source_dialogue.py`
- Category: `orphan-file`
- Potential size: 32 LOC / 1.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/seedance_source_expression.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: seedance_source_dialogue, seedance_source_dialogue.py, src/ai_video/production/seedance_source_dialogue, src/ai_video/production/seedance_source_dialogue.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-218 — KEEP

- Location: `src/ai_video/production/seedance_source_expression.py`
- Category: `orphan-file`
- Potential size: 682 LOC / 30.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_handoff.py, src/ai_video/canvas_planning.py, src/ai_video/canvas_project_data.py and 23 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: seedance_source_expression, seedance_source_expression.py, src/ai_video/production/seedance_source_expression, src/ai_video/production/seedance_source_expression.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-219 — KEEP

- Location: `src/ai_video/production/seedream.py`
- Category: `orphan-file`
- Potential size: 265 LOC / 13.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_image_candidate_frontier.py, tests/test_remote_image_materialization.py, tests/test_seedream_remote_image.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: seedream, seedream.py, src/ai_video/production/seedream, src/ai_video/production/seedream.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-220 — KEEP

- Location: `src/ai_video/production/seedream_reference.py`
- Category: `orphan-file`
- Potential size: 43 LOC / 2.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/image.py, src/ai_video/production/seedream.py, tests/test_seedream_remote_image.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: seedream_reference, seedream_reference.py, src/ai_video/production/seedream_reference, src/ai_video/production/seedream_reference.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-221 — KEEP

- Location: `src/ai_video/production/shot_continuity_m0_caller.py`
- Category: `orphan-file`
- Potential size: 930 LOC / 34.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/generation_execution.py, src/ai_video/production/shot_continuity_m0_operator.py, tests/test_shot_continuity_m0_caller.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_continuity_m0_caller, shot_continuity_m0_caller.py, src/ai_video/production/shot_continuity_m0_caller, src/ai_video/production/shot_continuity_m0_caller.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-222 — KEEP

- Location: `src/ai_video/production/shot_continuity_m0_fast_validation.py`
- Category: `orphan-file`
- Potential size: 617 LOC / 22.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/materialize_shot_continuity_m0.py, src/ai_video/production/shot_continuity_m0_caller.py, tests/test_shot_continuity_m0_caller.py and 3 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_continuity_m0_fast_validation, shot_continuity_m0_fast_validation.py, src/ai_video/production/shot_continuity_m0_fast_validation, src/ai_video/production/shot_continuity_m0_fast_validation.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-223 — KEEP

- Location: `src/ai_video/production/shot_continuity_m0_feasibility.py`
- Category: `orphan-file`
- Potential size: 588 LOC / 23.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/shot_continuity_m0_caller.py, src/ai_video/production/shot_continuity_m0_operator.py, tests/test_shot_continuity_m0_feasibility.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_continuity_m0_feasibility, shot_continuity_m0_feasibility.py, src/ai_video/production/shot_continuity_m0_feasibility, src/ai_video/production/shot_continuity_m0_feasibility.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-224 — KEEP

- Location: `src/ai_video/production/shot_continuity_m0_motion_tail.py`
- Category: `orphan-file`
- Potential size: 61 LOC / 2.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/shot_continuity_m0_feasibility.py, src/ai_video/production/shot_continuity_m0_operator.py, src/ai_video/production/shot_continuity_m0_reprepare.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_continuity_m0_motion_tail, shot_continuity_m0_motion_tail.py, src/ai_video/production/shot_continuity_m0_motion_tail, src/ai_video/production/shot_continuity_m0_motion_tail.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-225 — KEEP

- Location: `src/ai_video/production/shot_continuity_m0_operator.py`
- Category: `orphan-file`
- Potential size: 761 LOC / 29.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_shot_continuity_m0_operator.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_continuity_m0_operator, shot_continuity_m0_operator.py, src/ai_video/production/shot_continuity_m0_operator, src/ai_video/production/shot_continuity_m0_operator.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-226 — KEEP

- Location: `src/ai_video/production/shot_continuity_m0_policy.py`
- Category: `orphan-file`
- Potential size: 184 LOC / 6.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/materialize_shot_continuity_m0.py, scripts/prepare_shot_continuity_endpoint_repair.py, scripts/prepare_shot_continuity_p0.py and 9 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_continuity_m0_policy, shot_continuity_m0_policy.py, src/ai_video/production/shot_continuity_m0_policy, src/ai_video/production/shot_continuity_m0_policy.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-227 — KEEP

- Location: `src/ai_video/production/shot_continuity_m0_qualification.py`
- Category: `orphan-file`
- Potential size: 857 LOC / 31.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/materialize_shot_continuity_m0.py, src/ai_video/production/shot_continuity_m0_caller.py, src/ai_video/production/shot_continuity_m0_fast_validation.py and 13 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_continuity_m0_qualification, shot_continuity_m0_qualification.py, src/ai_video/production/shot_continuity_m0_qualification, src/ai_video/production/shot_continuity_m0_qualification.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-228 — KEEP

- Location: `src/ai_video/production/shot_continuity_m0_reprepare.py`
- Category: `orphan-file`
- Potential size: 334 LOC / 12.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_shot_continuity_m0_reprepare.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_continuity_m0_reprepare, shot_continuity_m0_reprepare.py, src/ai_video/production/shot_continuity_m0_reprepare, src/ai_video/production/shot_continuity_m0_reprepare.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-229 — KEEP

- Location: `src/ai_video/production/shot_continuity_m0_runtime.py`
- Category: `orphan-file`
- Potential size: 122 LOC / 4.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/shot_continuity_m0_caller.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_continuity_m0_runtime, shot_continuity_m0_runtime.py, src/ai_video/production/shot_continuity_m0_runtime, src/ai_video/production/shot_continuity_m0_runtime.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-230 — KEEP

- Location: `src/ai_video/production/shot_continuity_m0_seed_reseal.py`
- Category: `orphan-file`
- Potential size: 149 LOC / 5.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/materialize_shot_continuity_m0.py, src/ai_video/production/shot_continuity_m0_qualification.py, tests/test_shot_continuity_m0_seed_reseal.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_continuity_m0_seed_reseal, shot_continuity_m0_seed_reseal.py, src/ai_video/production/shot_continuity_m0_seed_reseal, src/ai_video/production/shot_continuity_m0_seed_reseal.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-231 — KEEP

- Location: `src/ai_video/production/shot_continuity_motion_analysis.py`
- Category: `orphan-file`
- Potential size: 481 LOC / 18.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/shot_continuity_motion_tail.py, src/ai_video/production/shot_continuity_terminal_motion_tail.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_continuity_motion_analysis, shot_continuity_motion_analysis.py, src/ai_video/production/shot_continuity_motion_analysis, src/ai_video/production/shot_continuity_motion_analysis.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-232 — KEEP

- Location: `src/ai_video/production/shot_continuity_motion_tail.py`
- Category: `orphan-file`
- Potential size: 764 LOC / 31.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/shot_continuity_motion_tail_runtime.py, src/ai_video/production/shot_continuity_terminal_motion_tail.py, tests/test_shot_continuity_motion_tail.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_continuity_motion_tail, shot_continuity_motion_tail.py, src/ai_video/production/shot_continuity_motion_tail, src/ai_video/production/shot_continuity_motion_tail.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-233 — KEEP

- Location: `src/ai_video/production/shot_continuity_motion_tail_runtime.py`
- Category: `orphan-file`
- Potential size: 29 LOC / 1014 B
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_shot_continuity_motion_tail.py, tests/test_shot_continuity_terminal_motion_tail.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_continuity_motion_tail_runtime, shot_continuity_motion_tail_runtime.py, src/ai_video/production/shot_continuity_motion_tail_runtime, src/ai_video/production/shot_continuity_motion_tail_runtime.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-234 — KEEP

- Location: `src/ai_video/production/shot_continuity_source_contracts.py`
- Category: `orphan-file`
- Potential size: 81 LOC / 2.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/shot_continuity_source_operator.py, src/ai_video/production/shot_continuity_source_qualification.py, src/ai_video/production/shot_continuity_source_transport.py and 3 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_continuity_source_contracts, shot_continuity_source_contracts.py, src/ai_video/production/shot_continuity_source_contracts, src/ai_video/production/shot_continuity_source_contracts.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-235 — KEEP

- Location: `src/ai_video/production/shot_continuity_source_operator.py`
- Category: `orphan-file`
- Potential size: 693 LOC / 26.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/execute_shot_continuity_source.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_continuity_source_operator, shot_continuity_source_operator.py, src/ai_video/production/shot_continuity_source_operator, src/ai_video/production/shot_continuity_source_operator.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-236 — KEEP

- Location: `src/ai_video/production/shot_continuity_source_qualification.py`
- Category: `orphan-file`
- Potential size: 950 LOC / 38.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/generation_execution.py, src/ai_video/production/shot_continuity_source_operator.py, tests/test_shot_continuity_source_operator.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_continuity_source_qualification, shot_continuity_source_qualification.py, src/ai_video/production/shot_continuity_source_qualification, src/ai_video/production/shot_continuity_source_qualification.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-237 — KEEP

- Location: `src/ai_video/production/shot_continuity_source_review.py`
- Category: `orphan-file`
- Potential size: 765 LOC / 29.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_video_candidate.py, src/ai_video/production/_state_commit_video_recovery.py, src/ai_video/production/_state_commit_video_source_boundary.py and 4 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_continuity_source_review, shot_continuity_source_review.py, src/ai_video/production/shot_continuity_source_review, src/ai_video/production/shot_continuity_source_review.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-238 — KEEP

- Location: `src/ai_video/production/shot_continuity_source_runtime.py`
- Category: `orphan-file`
- Potential size: 423 LOC / 14.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/prepare_shot_continuity_endpoint_repair.py, scripts/prepare_shot_continuity_p0.py, src/ai_video/production/shot_continuity_m0_operator.py and 6 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_continuity_source_runtime, shot_continuity_source_runtime.py, src/ai_video/production/shot_continuity_source_runtime, src/ai_video/production/shot_continuity_source_runtime.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-239 — KEEP

- Location: `src/ai_video/production/shot_continuity_source_schema.py`
- Category: `orphan-file`
- Potential size: 100 LOC / 3.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/shot_continuity_source_qualification.py, tests/test_shot_continuity_source_qualification.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_continuity_source_schema, shot_continuity_source_schema.py, src/ai_video/production/shot_continuity_source_schema, src/ai_video/production/shot_continuity_source_schema.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-240 — KEEP

- Location: `src/ai_video/production/shot_continuity_source_stack.py`
- Category: `orphan-file`
- Potential size: 347 LOC / 12.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/materialize_shot_continuity_m0.py, scripts/prepare_shot_continuity_p0.py, src/ai_video/production/shot_continuity_source_qualification.py and 4 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_continuity_source_stack, shot_continuity_source_stack.py, src/ai_video/production/shot_continuity_source_stack, src/ai_video/production/shot_continuity_source_stack.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-241 — KEEP

- Location: `src/ai_video/production/shot_continuity_source_transport.py`
- Category: `orphan-file`
- Potential size: 254 LOC / 8.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/shot_continuity_m0_caller.py, src/ai_video/production/shot_continuity_m0_operator.py, src/ai_video/production/shot_continuity_source_operator.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_continuity_source_transport, shot_continuity_source_transport.py, src/ai_video/production/shot_continuity_source_transport, src/ai_video/production/shot_continuity_source_transport.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-242 — KEEP

- Location: `src/ai_video/production/shot_continuity_terminal_motion_tail.py`
- Category: `orphan-file`
- Potential size: 704 LOC / 36.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/shot_continuity_m0_motion_tail.py, src/ai_video/production/shot_continuity_motion_tail_runtime.py, tests/test_shot_continuity_m0_feasibility.py and 3 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_continuity_terminal_motion_tail, shot_continuity_terminal_motion_tail.py, src/ai_video/production/shot_continuity_terminal_motion_tail, src/ai_video/production/shot_continuity_terminal_motion_tail.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-243 — KEEP

- Location: `src/ai_video/production/shot_router.py`
- Category: `orphan-file`
- Potential size: 762 LOC / 33.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/generation_feedback_driver.py, src/ai_video/production/__init__.py, src/ai_video/production/comfy_t8_native_turbo_video.py and 46 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_router, shot_router.py, src/ai_video/production/shot_router, src/ai_video/production/shot_router.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-244 — KEEP

- Location: `src/ai_video/production/source_use_evidence.py`
- Category: `orphan-file`
- Potential size: 281 LOC / 12.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/production_strategy.py, src/ai_video/production/domain_acceptance.py, src/ai_video/production/production_strategy_reader.py and 6 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: source_use_evidence, source_use_evidence.py, src/ai_video/production/source_use_evidence, src/ai_video/production/source_use_evidence.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-245 — KEEP

- Location: `src/ai_video/production/state_commit.py`
- Category: `orphan-file`
- Potential size: 577 LOC / 17.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_production.py, scripts/generation_feedback_driver.py, scripts/materialize_shot_continuity_m0.py and 126 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/state_commit, src/ai_video/production/state_commit.py, state_commit, state_commit.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-246 — KEEP

- Location: `src/ai_video/production/state_commit_attempt_contracts.py`
- Category: `orphan-file`
- Potential size: 65 LOC / 2.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/models.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/state_commit_attempt_contracts, src/ai_video/production/state_commit_attempt_contracts.py, state_commit_attempt_contracts, state_commit_attempt_contracts.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-247 — KEEP

- Location: `src/ai_video/production/validation.py`
- Category: `orphan-file`
- Potential size: 366 LOC / 16.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_creative_project_reader.py, src/ai_video/production/project.py, tests/test_production_validation.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/validation, src/ai_video/production/validation.py, validation, validation.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-248 — KEEP

- Location: `src/ai_video/production/video_cleanup_admission.py`
- Category: `orphan-file`
- Potential size: 125 LOC / 7.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_bootstrap.py, src/ai_video/production/repair_input_admission.py, src/ai_video/production/video_cleanup_viewing_admission.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/video_cleanup_admission, src/ai_video/production/video_cleanup_admission.py, video_cleanup_admission, video_cleanup_admission.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-249 — KEEP

- Location: `src/ai_video/production/video_cleanup_contracts.py`
- Category: `orphan-file`
- Potential size: 79 LOC / 3.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/production_responsibility.py, src/ai_video/production/video_cleanup_media.py, src/ai_video/production/video_cleanup_pixels.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/video_cleanup_contracts, src/ai_video/production/video_cleanup_contracts.py, video_cleanup_contracts, video_cleanup_contracts.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-250 — KEEP

- Location: `src/ai_video/production/video_cleanup_media.py`
- Category: `orphan-file`
- Potential size: 292 LOC / 16.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_production.py, src/ai_video/production/video_cleanup_admission.py, src/ai_video/production/video_cleanup_viewing.py and 3 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/video_cleanup_media, src/ai_video/production/video_cleanup_media.py, video_cleanup_media, video_cleanup_media.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-251 — KEEP

- Location: `src/ai_video/production/video_cleanup_pixels.py`
- Category: `orphan-file`
- Potential size: 281 LOC / 10.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/video_cleanup_media.py, tests/test_video_cleanup_pixels.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/video_cleanup_pixels, src/ai_video/production/video_cleanup_pixels.py, video_cleanup_pixels, video_cleanup_pixels.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-252 — KEEP

- Location: `src/ai_video/production/video_cleanup_viewing.py`
- Category: `orphan-file`
- Potential size: 305 LOC / 10.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/video_cleanup_viewing_admission.py, tests/test_video_cleanup_admission.py, tests/test_video_cleanup_viewing.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: video_cleanup_viewing, video_cleanup_viewing.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-253 — KEEP

- Location: `src/ai_video/production/video_cleanup_viewing_admission.py`
- Category: `orphan-file`
- Potential size: 94 LOC / 5.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/repair_input_admission.py, src/ai_video/production/video_cleanup_admission.py, tests/test_video_cleanup_admission.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: video_cleanup_viewing_admission, video_cleanup_viewing_admission.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-254 — KEEP

- Location: `src/ai_video/production/video_compiler.py`
- Category: `orphan-file`
- Potential size: 935 LOC / 40.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/comfy_t8_native_turbo_video.py, src/ai_video/production/comfy_t8_turbo_video.py, src/ai_video/production/comfy_t8_video.py and 46 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/video_compiler, src/ai_video/production/video_compiler.py, video_compiler, video_compiler.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-255 — KEEP

- Location: `src/ai_video/production/video_contracts.py`
- Category: `orphan-file`
- Potential size: 637 LOC / 24.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/generation_feedback_driver.py, src/ai_video/production/__init__.py, src/ai_video/production/_shot_router_contracts.py and 35 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/video_contracts, src/ai_video/production/video_contracts.py, video_contracts, video_contracts.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-256 — KEEP

- Location: `src/ai_video/production/video_execution_stack.py`
- Category: `orphan-file`
- Potential size: 270 LOC / 11.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/materialize_shot_continuity_m0.py, scripts/prepare_shot_continuity_p0.py, src/ai_video/planning/sequence_continuity.py and 17 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/video_execution_stack, src/ai_video/production/video_execution_stack.py, video_execution_stack, video_execution_stack.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-257 — KEEP

- Location: `src/ai_video/production/video_geometry.py`
- Category: `orphan-file`
- Potential size: 16 LOC / 732 B
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_video_project_reader.py, src/ai_video/production/video_artifact.py, tests/test_grok_output_contract.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/video_geometry, src/ai_video/production/video_geometry.py, video_geometry, video_geometry.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-258 — KEEP

- Location: `src/ai_video/production/video_reference_controls.py`
- Category: `orphan-file`
- Potential size: 399 LOC / 20.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_production.py, tests/test_character_performance_workflow.py, tests/test_generation_reference_controls.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/video_reference_controls, src/ai_video/production/video_reference_controls.py, video_reference_controls, video_reference_controls.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-259 — KEEP

- Location: `src/ai_video/production/video_requirement.py`
- Category: `orphan-file`
- Potential size: 1,426 LOC / 54.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_planning.py, src/ai_video/canvas_source_expression.py, src/ai_video/canvas_source_revision.py and 85 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/video_requirement, src/ai_video/production/video_requirement.py, video_requirement, video_requirement.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-260 — KEEP

- Location: `src/ai_video/production/video_retime.py`
- Category: `orphan-file`
- Potential size: 93 LOC / 3.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/canvas_composition.py, src/ai_video/production/__init__.py, src/ai_video/production/_composition_visual.py and 13 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/video_retime, src/ai_video/production/video_retime.py, video_retime, video_retime.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-261 — KEEP

- Location: `src/ai_video/production/video_subjects.py`
- Category: `orphan-file`
- Potential size: 91 LOC / 4.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_vidu_subjects.py, src/ai_video/production/video.py, src/ai_video/production/video_compiler.py and 3 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/video_subjects, src/ai_video/production/video_subjects.py, video_subjects, video_subjects.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-262 — KEEP

- Location: `src/ai_video/production/video_timing_recovery.py`
- Category: `orphan-file`
- Potential size: 106 LOC / 4.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/video_artifact.py, tests/test_video_nominal_endpoint_recovery.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/video_timing_recovery, src/ai_video/production/video_timing_recovery.py, video_timing_recovery, video_timing_recovery.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-263 — KEEP

- Location: `src/ai_video/production/video_transition.py`
- Category: `orphan-file`
- Potential size: 667 LOC / 28.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/canvas_sequence_handoff.py, scripts/canvas_sequence_packet.py, scripts/prepare_shot_continuity_p0.py and 32 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/video_transition, src/ai_video/production/video_transition.py, video_transition, video_transition.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-264 — KEEP

- Location: `src/ai_video/production/vidu.py`
- Category: `orphan-file`
- Potential size: 577 LOC / 32.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/s01_strategy_regression.py, src/ai_video/production/vidu_ad_provider.py, tests/test_generation_provider_wiring.py and 4 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/vidu, src/ai_video/production/vidu.py, vidu, vidu.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-265 — KEEP

- Location: `src/ai_video/production/vidu_ad_contracts.py`
- Category: `orphan-file`
- Potential size: 129 LOC / 5.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_ad.py, src/ai_video/production/models.py, src/ai_video/production/vidu_ad_provider.py and 3 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: vidu_ad_contracts, vidu_ad_contracts.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-266 — KEEP

- Location: `src/ai_video/production/vidu_ad_provider.py`
- Category: `orphan-file`
- Potential size: 117 LOC / 6.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_paid_provider.py, src/ai_video/production/vidu.py, src/ai_video/production/vidu_ad_reader.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: vidu_ad_provider, vidu_ad_provider.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-267 — KEEP

- Location: `src/ai_video/production/vidu_ad_reader.py`
- Category: `orphan-file`
- Potential size: 117 LOC / 6.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_paid_provider_project_reader.py, src/ai_video/production/_state_commit_ad.py, src/ai_video/production/_state_commit_paid_provider.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: vidu_ad_reader, vidu_ad_reader.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-268 — KEEP

- Location: `src/ai_video/production/vidu_ad_wire.py`
- Category: `orphan-file`
- Potential size: 143 LOC / 5.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/vidu_ad_provider.py, tests/test_production_vidu_ad_wire.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: vidu_ad_wire, vidu_ad_wire.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-269 — KEEP

- Location: `src/ai_video/production/vidu_download.py`
- Category: `orphan-file`
- Potential size: 141 LOC / 5.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_ad.py, src/ai_video/production/grok_download.py, src/ai_video/production/metaso_h3.py and 4 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/vidu_download, src/ai_video/production/vidu_download.py, vidu_download, vidu_download.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-270 — KEEP

- Location: `src/ai_video/production/vidu_profile.py`
- Category: `orphan-file`
- Potential size: 203 LOC / 10.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/s01_strategy_regression.py, src/ai_video/production/generation_decision.py, src/ai_video/production/generation_feedback.py and 9 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/vidu_profile, src/ai_video/production/vidu_profile.py, vidu_profile, vidu_profile.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-271 — KEEP

- Location: `src/ai_video/production/vidu_source.py`
- Category: `orphan-file`
- Potential size: 53 LOC / 2.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/vidu.py, tests/test_production_vidu.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/vidu_source, src/ai_video/production/vidu_source.py, vidu_source, vidu_source.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-272 — KEEP

- Location: `src/ai_video/production/visual_media.py`
- Category: `orphan-file`
- Potential size: 207 LOC / 7.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/planning/production_strategy.py, src/ai_video/production/_composition_source_duration.py, src/ai_video/production/_composition_visual.py and 4 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/visual_media, src/ai_video/production/visual_media.py, visual_media, visual_media.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-273 — KEEP

- Location: `src/ai_video/production/visual_quality.py`
- Category: `orphan-file`
- Potential size: 91 LOC / 3.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/visual_quality_report.py, src/ai_video/production/final_output_contracts.py, src/ai_video/production/final_output_review.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/visual_quality, src/ai_video/production/visual_quality.py, visual_quality, visual_quality.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-274 — KEEP

- Location: `src/ai_video/production/voice_routing.py`
- Category: `orphan-file`
- Potential size: 662 LOC / 36.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_shot_router_contracts.py, src/ai_video/production/_state_commit_paid_provider.py, src/ai_video/production/_state_commit_voice_candidate.py and 13 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/production/voice_routing, src/ai_video/production/voice_routing.py, voice_routing, voice_routing.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-275 — KEEP

- Location: `src/ai_video/production/voice_routing_contracts.py`
- Category: `orphan-file`
- Potential size: 118 LOC / 4.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/generation_decision.py, src/ai_video/production/models.py, src/ai_video/production/video_requirement.py and 10 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: voice_routing_contracts, voice_routing_contracts.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-276 — KEEP

- Location: `src/ai_video/production/voice_routing_execution.py`
- Category: `orphan-file`
- Potential size: 58 LOC / 2.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/production/_state_commit_voice_candidate.py, src/ai_video/production/_state_commit_voice_intent.py, src/ai_video/production/_voice_project_reader.py and 3 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: voice_routing_execution, voice_routing_execution.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-277 — KEEP

- Location: `src/ai_video/production_planning.py`
- Category: `orphan-file`
- Potential size: 140 LOC / 7.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/s01_strategy_regression.py, src/ai_video/canvas_production.py, tests/test_canvas_production.py and 8 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: production_planning, production_planning.py, src/ai_video/production_planning, src/ai_video/production_planning.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-278 — KEEP

- Location: `src/ai_video/provider_console.py`
- Category: `orphan-file`
- Potential size: 880 LOC / 34.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/provider_console_media_index.py, src/ai_video/provider_console_video_evidence.py, tests/test_provider_console.py and 1 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: provider_console, provider_console.py, src/ai_video/provider_console, src/ai_video/provider_console.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-279 — KEEP

- Location: `src/ai_video/provider_console_continuity.py`
- Category: `orphan-file`
- Potential size: 224 LOC / 9.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/provider_console.py, src/ai_video/provider_console_render.py, tests/test_provider_console.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: provider_console_continuity, provider_console_continuity.py, src/ai_video/provider_console_continuity, src/ai_video/provider_console_continuity.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-280 — KEEP

- Location: `src/ai_video/provider_console_manifest.py`
- Category: `orphan-file`
- Potential size: 77 LOC / 2.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/provider_console.py, src/ai_video/provider_console_video_evidence.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: provider_console_manifest, provider_console_manifest.py, src/ai_video/provider_console_manifest, src/ai_video/provider_console_manifest.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-281 — KEEP

- Location: `src/ai_video/provider_console_media_index.py`
- Category: `orphan-file`
- Potential size: 325 LOC / 12.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_provider_console_media_index.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: provider_console_media_index, provider_console_media_index.py, src/ai_video/provider_console_media_index, src/ai_video/provider_console_media_index.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-282 — KEEP

- Location: `src/ai_video/provider_console_render.py`
- Category: `orphan-file`
- Potential size: 38 LOC / 1.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/provider_console.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: provider_console_render, provider_console_render.py, src/ai_video/provider_console_render, src/ai_video/provider_console_render.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-283 — KEEP

- Location: `src/ai_video/provider_console_video_evidence.py`
- Category: `orphan-file`
- Potential size: 67 LOC / 2.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/provider_console_media_index.py, tests/test_provider_console.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: provider_console_video_evidence, provider_console_video_evidence.py, src/ai_video/provider_console_video_evidence, src/ai_video/provider_console_video_evidence.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-284 — KEEP

- Location: `src/ai_video/quality_gates/_readiness_models.py`
- Category: `orphan-file`
- Potential size: 288 LOC / 10.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/quality_gates/__init__.py, src/ai_video/quality_gates/shot_readiness_gate.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _readiness_models, _readiness_models.py, src/ai_video/quality_gates/_readiness_models, src/ai_video/quality_gates/_readiness_models.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-285 — KEEP

- Location: `src/ai_video/quality_gates/shot_readiness_gate.py`
- Category: `orphan-file`
- Potential size: 326 LOC / 12.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/quality_gates/__init__.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: shot_readiness_gate, shot_readiness_gate.py, src/ai_video/quality_gates/shot_readiness_gate, src/ai_video/quality_gates/shot_readiness_gate.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-286 — KEEP

- Location: `src/ai_video/quality_intelligence/_capture_contracts.py`
- Category: `orphan-file`
- Potential size: 127 LOC / 4.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/quality_intelligence/_capture_human.py, src/ai_video/quality_intelligence/_capture_p6.py, src/ai_video/quality_intelligence/capture.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _capture_contracts, _capture_contracts.py, src/ai_video/quality_intelligence/_capture_contracts, src/ai_video/quality_intelligence/_capture_contracts.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-287 — KEEP

- Location: `src/ai_video/quality_intelligence/_capture_p6.py`
- Category: `orphan-file`
- Potential size: 106 LOC / 3.6 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/quality_intelligence/capture.py, tests/test_quality_experience_capture.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: _capture_p6, _capture_p6.py, src/ai_video/quality_intelligence/_capture_p6, src/ai_video/quality_intelligence/_capture_p6.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-288 — KEEP

- Location: `src/ai_video/quality_intelligence/capture.py`
- Category: `orphan-file`
- Potential size: 800 LOC / 29.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/quality_intelligence/__init__.py, tests/test_quality_experience_capture.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: capture, capture.py, src/ai_video/quality_intelligence/capture, src/ai_video/quality_intelligence/capture.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-289 — KEEP

- Location: `src/ai_video/quality_intelligence/dataset.py`
- Category: `orphan-file`
- Potential size: 389 LOC / 14.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/quality_intelligence/__init__.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: dataset, dataset.py, src/ai_video/quality_intelligence/dataset, src/ai_video/quality_intelligence/dataset.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-290 — KEEP

- Location: `src/ai_video/quality_intelligence/models.py`
- Category: `orphan-file`
- Potential size: 1,561 LOC / 57.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/quality_intelligence/__init__.py, src/ai_video/quality_intelligence/_capture_contracts.py, src/ai_video/quality_intelligence/_capture_human.py and 10 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: models, models.py, src/ai_video/quality_intelligence/models, src/ai_video/quality_intelligence/models.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-291 — KEEP

- Location: `src/ai_video/quality_intelligence/rag_projection.py`
- Category: `orphan-file`
- Potential size: 67 LOC / 2.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/quality_intelligence/__init__.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: rag_projection, rag_projection.py, src/ai_video/quality_intelligence/rag_projection, src/ai_video/quality_intelligence/rag_projection.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-292 — KEEP

- Location: `src/ai_video/quality_intelligence/store.py`
- Category: `orphan-file`
- Potential size: 718 LOC / 29.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video/quality_intelligence/__init__.py, src/ai_video/quality_intelligence/_capture_contracts.py, src/ai_video/quality_intelligence/capture.py and 6 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/quality_intelligence/store, src/ai_video/quality_intelligence/store.py, store, store.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-293 — KEEP

- Location: `src/ai_video/workflow_loader.py`
- Category: `orphan-file`
- Potential size: 545 LOC / 19.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/check_p7_1_comfy_compatibility.py, src/ai_video/cli.py, src/ai_video/production/comfy_image.py and 12 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/workflow_loader, src/ai_video/workflow_loader.py, workflow_loader, workflow_loader.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-294 — KEEP

- Location: `src/ai_video/workflow_renderer.py`
- Category: `orphan-file`
- Potential size: 264 LOC / 10.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/check_p7_1_comfy_compatibility.py, src/ai_video/cli.py, src/ai_video/pipeline.py and 9 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video/workflow_renderer, src/ai_video/workflow_renderer.py, workflow_renderer, workflow_renderer.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-295 — KEEP

- Location: `src/ai_video_mcp/analysis_client.py`
- Category: `orphan-file`
- Potential size: 39 LOC / 1.8 KB
- Status reason: KEEP: generation_feedback.py:131 launches this exact module with python -m; tests/test_generation_feedback_review.py:35 asserts the subprocess entry.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: analysis_client, analysis_client.py, src/ai_video_mcp/analysis_client, src/ai_video_mcp/analysis_client.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-296 — KEEP

- Location: `src/ai_video_mcp/analysis_hook.py`
- Category: `orphan-file`
- Potential size: 756 LOC / 23.7 KB
- Status reason: KEEP: .codex/hooks.json:34 and .claude/settings.json:31 register this hook; tests/test_mcp_analyze.py dynamically imports it.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: analysis_hook, analysis_hook.py, src/ai_video_mcp/analysis_hook, src/ai_video_mcp/analysis_hook.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-297 — KEEP

- Location: `src/ai_video_mcp/audio_operator.py`
- Category: `orphan-file`
- Potential size: 523 LOC / 24.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from tests/test_mcp_audio_operator.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: audio_operator, audio_operator.py, src/ai_video_mcp/audio_operator, src/ai_video_mcp/audio_operator.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-298 — KEEP

- Location: `src/ai_video_mcp/audio_understanding.py`
- Category: `orphan-file`
- Potential size: 435 LOC / 20.2 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/audio_operator.py, src/ai_video_mcp/server.py, src/ai_video_mcp/tools/audio_understand.py and 3 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: audio_understanding, audio_understanding.py, src/ai_video_mcp/audio_understanding, src/ai_video_mcp/audio_understanding.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-299 — KEEP

- Location: `src/ai_video_mcp/cache.py`
- Category: `orphan-file`
- Potential size: 45 LOC / 1.5 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/analysis_hook.py, src/ai_video_mcp/server.py, src/ai_video_mcp/tools/analyze.py and 8 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: cache, cache.py, src/ai_video_mcp/cache, src/ai_video_mcp/cache.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-300 — KEEP

- Location: `src/ai_video_mcp/config.py`
- Category: `orphan-file`
- Potential size: 39 LOC / 961 B
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/analysis_hook.py, src/ai_video_mcp/server.py, src/ai_video_mcp/tools/analyze.py and 10 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: config, config.py, src/ai_video_mcp/config, src/ai_video_mcp/config.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-301 — KEEP

- Location: `src/ai_video_mcp/errors.py`
- Category: `orphan-file`
- Potential size: 30 LOC / 794 B
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/server.py, src/ai_video_mcp/tools/frames.py, src/ai_video_mcp/tools/probe.py and 9 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: errors, errors.py, src/ai_video_mcp/errors, src/ai_video_mcp/errors.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-302 — KEEP

- Location: `src/ai_video_mcp/generation_feedback.py`
- Category: `orphan-file`
- Potential size: 263 LOC / 14.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from scripts/generation_feedback_driver.py, src/ai_video/canvas_production.py, tests/test_canvas_continuity.py and 5 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: generation_feedback, generation_feedback.py, src/ai_video_mcp/generation_feedback, src/ai_video_mcp/generation_feedback.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-303 — KEEP

- Location: `src/ai_video_mcp/serialization.py`
- Category: `orphan-file`
- Potential size: 119 LOC / 3.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/analysis_hook.py, src/ai_video_mcp/server.py, tests/test_mcp_analyze.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: serialization, serialization.py, src/ai_video_mcp/serialization, src/ai_video_mcp/serialization.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-304 — KEEP

- Location: `src/ai_video_mcp/server.py`
- Category: `orphan-file`
- Potential size: 314 LOC / 11.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/__main__.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: server, server.py, src/ai_video_mcp/server, src/ai_video_mcp/server.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-305 — KEEP

- Location: `src/ai_video_mcp/tools/analyze.py`
- Category: `orphan-file`
- Potential size: 88 LOC / 2.9 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/analysis_hook.py, src/ai_video_mcp/server.py, src/ai_video_mcp/tools/review.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: analyze, analyze.py, src/ai_video_mcp/tools/analyze, src/ai_video_mcp/tools/analyze.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-306 — KEEP

- Location: `src/ai_video_mcp/tools/apply_optimization.py`
- Category: `orphan-file`
- Potential size: 176 LOC / 5.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/server.py, tests/test_mcp_apply_optimization.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: apply_optimization, apply_optimization.py, src/ai_video_mcp/tools/apply_optimization, src/ai_video_mcp/tools/apply_optimization.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-307 — KEEP

- Location: `src/ai_video_mcp/tools/audio_understand.py`
- Category: `orphan-file`
- Potential size: 151 LOC / 7.3 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/audio_operator.py, src/ai_video_mcp/server.py, src/ai_video_mcp/tools/analyze.py and 2 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: audio_understand, audio_understand.py, src/ai_video_mcp/tools/audio_understand, src/ai_video_mcp/tools/audio_understand.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-308 — KEEP

- Location: `src/ai_video_mcp/tools/frames.py`
- Category: `orphan-file`
- Potential size: 127 LOC / 4.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/server.py, src/ai_video_mcp/tools/analyze.py, tests/test_mcp_frames.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: frames, frames.py, src/ai_video_mcp/tools/frames, src/ai_video_mcp/tools/frames.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-309 — KEEP

- Location: `src/ai_video_mcp/tools/optimize_plan.py`
- Category: `orphan-file`
- Potential size: 229 LOC / 8.4 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/server.py, src/ai_video_mcp/tools/apply_optimization.py, tests/test_mcp_optimize_plan.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: optimize_plan, optimize_plan.py, src/ai_video_mcp/tools/optimize_plan, src/ai_video_mcp/tools/optimize_plan.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-310 — KEEP

- Location: `src/ai_video_mcp/tools/probe.py`
- Category: `orphan-file`
- Potential size: 129 LOC / 4.7 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/server.py, src/ai_video_mcp/tools/analyze.py, src/ai_video_mcp/tools/frames.py and 5 more. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: probe, probe.py, src/ai_video_mcp/tools/probe, src/ai_video_mcp/tools/probe.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-311 — KEEP

- Location: `src/ai_video_mcp/tools/review.py`
- Category: `orphan-file`
- Potential size: 382 LOC / 13.8 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/server.py, src/ai_video_mcp/tools/optimize_plan.py, tests/test_mcp_review.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: review, review.py, src/ai_video_mcp/tools/review, src/ai_video_mcp/tools/review.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-312 — KEEP

- Location: `src/ai_video_mcp/tools/scene_detect.py`
- Category: `orphan-file`
- Potential size: 123 LOC / 4.0 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/server.py, src/ai_video_mcp/tools/analyze.py, tests/test_mcp_scene_detect.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: scene_detect, scene_detect.py, src/ai_video_mcp/tools/scene_detect, src/ai_video_mcp/tools/scene_detect.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-313 — KEEP

- Location: `src/ai_video_mcp/tools/transcribe.py`
- Category: `orphan-file`
- Potential size: 136 LOC / 4.1 KB
- Status reason: KEEP: src-layout-aware AST resolves actual Python inbound import(s) from src/ai_video_mcp/server.py, src/ai_video_mcp/tools/analyze.py, tests/test_mcp_transcribe.py. See python-static.json; bundled import resolution is a false positive.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: src/ai_video_mcp/tools/transcribe, src/ai_video_mcp/tools/transcribe.py, transcribe, transcribe.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-314 — KEEP

- Location: `tests/ecommerce_job_factory.py`
- Category: `orphan-file`
- Potential size: 430 LOC / 14.5 KB
- Status reason: KEEP: pytest uses tests/ as an import root; real helper module imports occur in tests/test_production_delivery_packager.py, tests/test_production_ecommerce_job.py, tests/test_production_ecommerce_job_assembly.py. The generic resolver uses the repository root.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: ecommerce_job_factory, ecommerce_job_factory.py, tests/ecommerce_job_factory, tests/ecommerce_job_factory.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-315 — KEEP

- Location: `tests/helpers/p2a_crash_worker.py`
- Category: `orphan-file`
- Potential size: 358 LOC / 14.1 KB
- Status reason: KEEP: tests/test_production_state_recovery.py:443 executes this helper via its string path.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: p2a_crash_worker, p2a_crash_worker.py, tests/helpers/p2a_crash_worker, tests/helpers/p2a_crash_worker.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-316 — KEEP

- Location: `tests/production_e2e_support.py`
- Category: `orphan-file`
- Potential size: 2,143 LOC / 83.5 KB
- Status reason: KEEP: pytest uses tests/ as an import root; real helper module imports occur in tests/production_project_factory.py, tests/test_canvas_continuity.py, tests/test_canvas_edit_first.py. The generic resolver uses the repository root.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: production_e2e_support, production_e2e_support.py, tests/production_e2e_support, tests/production_e2e_support.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-317 — KEEP

- Location: `tests/production_ecommerce_job_render_support.py`
- Category: `orphan-file`
- Potential size: 142 LOC / 4.9 KB
- Status reason: KEEP: pytest uses tests/ as an import root; real helper module imports occur in tests/test_agent_harness.py, tests/test_production_ecommerce_job_e2e.py. The generic resolver uses the repository root.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: production_ecommerce_job_render_support, production_ecommerce_job_render_support.py, tests/production_ecommerce_job_render_support, tests/production_ecommerce_job_render_support.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-318 — KEEP

- Location: `tests/production_remote_generation_factory.py`
- Category: `orphan-file`
- Potential size: 254 LOC / 13.5 KB
- Status reason: KEEP: pytest uses tests/ as an import root; real helper module imports occur in tests/test_agent_harness.py, tests/test_generation_feedback_driver.py, tests/test_production_grok.py. The generic resolver uses the repository root.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: production_remote_generation_factory, production_remote_generation_factory.py, tests/production_remote_generation_factory, tests/production_remote_generation_factory.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-319 — KEEP

- Location: `tests/production_strategy_factory.py`
- Category: `orphan-file`
- Potential size: 385 LOC / 16.0 KB
- Status reason: KEEP: pytest uses tests/ as an import root; real helper module imports occur in tests/test_canvas_edit_first.py, tests/test_canvas_production.py, tests/test_canvas_project_data.py. The generic resolver uses the repository root.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: production_strategy_factory, production_strategy_factory.py, tests/production_strategy_factory, tests/production_strategy_factory.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-320 — KEEP

- Location: `tests/production_voice_e2e_support.py`
- Category: `orphan-file`
- Potential size: 220 LOC / 8.6 KB
- Status reason: KEEP: pytest uses tests/ as an import root; real helper module imports occur in tests/production_e2e_support.py, tests/test_production_voice_captions_e2e.py. The generic resolver uses the repository root.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: production_voice_e2e_support, production_voice_e2e_support.py, tests/production_voice_e2e_support, tests/production_voice_e2e_support.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-321 — KEEP

- Location: `tests/video_provider_contract.py`
- Category: `orphan-file`
- Potential size: 148 LOC / 5.0 KB
- Status reason: KEEP: pytest uses tests/ as an import root; real helper module imports occur in tests/test_production_video_fake.py. The generic resolver uses the repository root.
- Evidence: No resolved static inbound import was found. The file is not a detected package or conventional entry point. Repository text contains possible string/name references: tests/video_provider_contract, tests/video_provider_contract.py, video_provider_contract, video_provider_contract.py.
- Caveats: Dynamic loading, reflection, external consumers, or incomplete framework detection can hide reachability. Possible string reachability prevents high-confidence deletion.

### CRT-322 — KEEP

- Location: `provider-console/src/continuity-review.js:19`
- Category: `unused-export`
- Potential size: 0 LOC / 0 B
- Status reason: KEEP: continuity-review.js:79 invokes downloadHumanReviewDecision from the panel submit handler. No external export consumer does not mean the function is dead.
- Evidence: No reference to the exported symbol was found outside its defining file.
- Caveats: Public APIs, re-export patterns, generated declarations, templates, or external consumers may use it.

### CRT-323 — KEEP

- Location: `provider-console/src/external-media-contract.js:187`
- Category: `unused-export`
- Potential size: 0 LOC / 0 B
- Status reason: KEEP: external-media-contract.js:16 and :194 invoke preferredRunBinding, including externalDisplayMetadata. The implementation is live.
- Evidence: No reference to the exported symbol was found outside its defining file.
- Caveats: Public APIs, re-export patterns, generated declarations, templates, or external consumers may use it.

### CRT-324 — REVIEW

- Location: `src/ai_video/production/dependency.py:838`
- Category: `unused-export`
- Potential size: 14 LOC / 593 B
- Status reason: Private function; no in-repository consumer found. Rare dynamic/external use and regression safety are unproven. Proposed function-only patch is syntax-valid but has no execution proof.
- Evidence: Supplementary AST module-symbol check, including import aliases, found no inbound symbol reference. Bounded repository search found only the definition; generated CodeGraph index, artifacts, runs, output reports and third-party skills were excluded. CodeGraph relationship query returned an empty list; advisory only.
- Caveats: Private function; no in-repository consumer found. Rare dynamic/external use and regression safety are unproven. The bundled proof script deletes whole files, so it must not be used to delete this live module. Proof must target only the proposed function block in fresh disposable copies. No approved commands have been run.

### CRT-325 — REVIEW

- Location: `src/ai_video/production/manifest_schema.py:110`
- Category: `unused-export`
- Potential size: 2 LOC / 89 B
- Status reason: Public module function; external imports cannot be ruled out, and passing in-repository tests would not prove external API compatibility. Proposed function-only patch is syntax-valid but has no execution proof.
- Evidence: Supplementary AST module-symbol check, including import aliases, found no inbound symbol reference. Bounded repository search found only the definition; generated CodeGraph index, artifacts, runs, output reports and third-party skills were excluded.
- Caveats: Public module function; external imports cannot be ruled out, and passing in-repository tests would not prove external API compatibility. The bundled proof script deletes whole files, so it must not be used to delete this live module. Proof must target only the proposed function block in fresh disposable copies. No approved commands have been run.

## Cleanup approval checklist

No cleanup has been applied. To continue, select exact candidate IDs and review their paths, evidence, proof, and residual risk. Manifest or lockfile changes require separate explicit approval.

```text
Approved candidate IDs: ____________________
Approved files / manifest entries: __________
Approved verification commands: _____________
```

## Scope and limitations

- Scanned 755 source files, 361,734 LOC, 14.2 MB.
- Static analysis cannot prove absence of dynamic, reflective, operational, platform-specific, or external use.
- JavaScript/TypeScript and Python import resolution is intentionally conservative and does not implement every alias or framework convention.
- Unused dependencies and exports are leads only until project-native tooling and focused proof support removal.
- No project code, package command, or dependency was executed by this scanner.
- Uses the bundled scanner through a scope-only adapter; the first unscoped scan was stopped without producing an analysis.
- Source scope: src/, scripts/, tests/, provider-console/ and root source files. References also include non-excluded documentation and configuration.
- Excluded: media and historical artifacts, runs, external skills, generated output, dependency/cache directories, all symlinks. No media or credential files were opened.
- Bundled Python resolver does not handle src-layout absolute imports or from-package imports reliably; manual AST/reference checks are required.
- LOC means physical lines; candidate sizes are not semantic code counts. No project-controlled command has been executed.
- Root index.json is a derived CodeGraph index and was excluded from text evidence.
- Raw scanner file-size estimate is NOT an approved or proven deletion amount. All original 323 candidates were rejected after import/internal-use/entry-point verification.
- CRT-324 and CRT-325 are supplemental function-block candidates, not whole-file deletions. They stay REVIEW without focused execution proof.
