# 13 — Function và Module Index

Tài liệu này là checklist triển khai. Signature chi tiết và semantics nằm trong tài liệu tương ứng.

## 1. Core/domain

| File | Symbols bắt buộc |
|---|---|
| `domain/common.py` | `new_id`, `parse_id`, `utc_now`, `canonical_json_hash` |
| `domain/timebase.py` | `ms_to_start_frame`, `ms_to_end_frame`, `quantize_partition`, `frames_to_ms`, `validate_frame_range` |
| `domain/geometry.py` | `resolve_slot`, `fit_asset`, `normalized_to_pixels`, `validate_safe_area` |
| `domain/validation/schema_validator.py` | `validate_schema` |
| `domain/validation/script_validator.py` | `validate_script` |
| `domain/validation/timing_validator.py` | `validate_timing` |
| `domain/validation/scene_validator.py` | `validate_scene_plan` |
| `domain/validation/timeline_validator.py` | `validate_timeline` |
| `domain/validation/render_readiness.py` | `validate_render_readiness` |

## 2. Project/artifacts

| File | Symbols bắt buộc |
|---|---|
| `application/projects/service.py` | `create_project`, `get_project`, `update_project`, `archive_project`, `restore_project`, `clone_project` |
| `application/projects/readiness.py` | `compute_readiness` |
| `application/artifacts/service.py` | `get_artifact`, `commit_artifact`, `compare_artifacts`, `list_artifact_history`, `restore_artifact` |
| `application/artifacts/invalidation.py` | `compute_input_fingerprint`, `find_descendants`, `mark_descendants_stale`, `is_artifact_current`, `reuse_or_create_artifact` |

## 3. Script/voice

| File | Symbols bắt buộc |
|---|---|
| `application/script/service.py` | `submit_script_generation`, `execute_script_generation`, `import_script`, `patch_script`, `approve_script` |
| `application/script/normalization.py` | `normalize_unicode`, `segment_sentences`, `normalize_entity_instances`, `resolve_emphasis_ranges`, `estimate_sentence_duration`, `recalculate_total_duration` |
| `application/voice/service.py` | `submit_voice_job`, `execute_voice_job`, `build_voice_segments`, `merge_audio_segments` |
| `application/voice/alignment.py` | `needs_alignment`, `align_audio`, `map_provider_tokens`, `score_alignment` |
| `application/voice/reconciliation.py` | `reconcile_sentence_spans`, `fill_missing_boundaries`, `enforce_monotonic_spans`, `compare_estimated_to_actual` |
| `providers/llm/base.py` | `generate_structured`, `capabilities`, `estimate_cost` |
| `providers/tts/base.py` | `synthesize`, `list_voices`, `capabilities` |
| `providers/alignment/base.py` | `align`, `capabilities` |

## 4. Assets

| File | Symbols bắt buộc |
|---|---|
| `application/assets/ingest.py` | `create_upload_session`, `complete_upload`, `register_generated_blob`, `reject_asset` |
| `application/assets/inspect.py` | `sniff_media_type`, `probe_media`, `verify_declared_size_checksum`, `scan_malware`, `inspect_svg`, `inspect_rights_metadata`, `enforce_media_limits` |
| `application/assets/process.py` | `sanitize_svg`, `rasterize_svg`, `normalize_orientation`, `convert_color_profile`, `remove_background`, `trim_transparent_bounds`, `transcode_video`, `validate_lottie` |
| `application/assets/derivatives.py` | `create_thumbnail`, `create_render_derivative`, `find_or_create_derivative` |
| `application/assets/playback.py` | `analyze_loop_points`, `validate_playback_config`, `extract_poster_frame` |
| `application/assets/generation.py` | `submit_generation_job`, `execute_generation_job`, `resolve_reference_assets`, `build_generation_prompt` |
| `application/assets/assignment.py` | `assign_asset`, `auto_assign`, `validate_asset_map`, `find_unassigned_requirements` |
| `application/assets/remote_import.py` | `submit_remote_import`, `execute_remote_import` |
| `providers/image/base.py` | `generate`, `moderate`, `capabilities` |

## 5. Scene/timeline

| File | Symbols bắt buộc |
|---|---|
| `application/scenes/service.py` | `submit_scene_plan_job`, `execute_scene_plan_job`, `generate_scene_plan`, `validate_scene_plan`, `commit_scene_plan` |
| `application/scenes/segmentation.py` | `build_sentence_states`, `detect_scene_boundaries`, `group_sentences`, `assign_scene_spans` |
| `application/scenes/state_machine.py` | `apply_instruction`, `resolve_active_instances`, `validate_transition`, `compute_scene_end_state` |
| `application/scenes/layout.py` | `select_template`, `instantiate_slots`, `assign_instances_to_slots`, `solve_layout`, `score_layout` |
| `application/scenes/transitions.py` | `derive_instance_changes`, `choose_transition`, `validate_transition_intent` |
| `application/timeline/service.py` | `submit_timeline_job`, `execute_timeline_job`, `compile_timeline`, `validate_and_commit_timeline` |
| `application/timeline/compiler.py` | `build_timebase`, `quantize_scene_spans`, `compile_background_track`, `compile_object_tracks`, `compile_text_track`, `compile_camera_track`, `compile_audio_tracks`, `finalize_total_frames` |
| `application/timeline/presets.py` | `register_preset`, `resolve_preset`, `validate_preset_params`, `fit_preset_duration` |
| `application/timeline/continuity.py` | `compute_meaningful_coverage`, `find_unintended_gaps`, `repair_gap`, `validate_instance_overlap` |
| `application/timeline/text.py` | `resolve_text_trigger`, `shape_text`, `fit_text`, `detect_text_collisions` |
| `application/timeline/camera.py` | `plan_camera`, `validate_camera_safe_area`, `limit_camera_velocity` |

## 6. Render/publish

| File | Symbols bắt buộc |
|---|---|
| `application/render/snapshot.py` | `build_render_snapshot`, `validate_snapshot`, `persist_snapshot` |
| `application/render/service.py` | `submit_render_job`, `execute_render_job`, `cancel_render_job`, `register_render_output` |
| `application/publish/service.py` | `create_export`, `execute_export`, `create_share_link`, `revoke_share_link`, `build_attribution_manifest` |
| `packages/video/.../W5DComposition.tsx` | `W5DComposition`, `calculateW5DMetadata`, `CompositionRoot` |
| `packages/video/.../AssetResolver.ts` | `createAssetResolver`, `resolve`, `preflightAll`, `verifyChecksum` |
| `packages/video/.../render-job.ts` | `runRenderJob`, `bundleComposition`, `selectComposition`, `renderMediaWithProgress`, `cancelRender`, `probeAndValidateOutput` |

## 7. Persistence/jobs

| File | Symbols bắt buộc |
|---|---|
| `infrastructure/db/session.py` | `create_engine`, `session_factory`, `get_session` |
| `application/uow.py` | `UnitOfWork`, `commit`, `rollback` |
| `repositories/project_repository.py` | `get`, `create`, `update_with_revision`, `set_current_artifact`, `list` |
| `repositories/artifact_repository.py` | `insert`, `get`, `get_current`, `find_by_fingerprint`, `mark_status`, `list_inputs`, `list_descendants` |
| `repositories/job_repository.py` | `create`, `claim`, `heartbeat`, `schedule_retry`, `mark_orphaned`, `request_cancel`, `finish_success`, `finish_failure`, `find_orphaned` |
| `repositories/outbox_repository.py` | `insert`, `claim_batch`, `mark_sent`, `mark_retry`, `append_domain_event` |
| `repositories/membership_repository.py` | `list_members`, `create_invitation`, `accept_invitation`, `update_role`, `remove_member` |
| `repositories/provider_credential_repository.py` | `get_metadata`, `upsert_encrypted`, `rotate`, `revoke` |
| `repositories/quota_repository.py` | `reserve`, `settle`, `release`, `get_usage` |
| `repositories/webhook_repository.py` | `insert_delivery`, `claim_deliveries`, `finish_delivery` |
| `repositories/share_repository.py` | `create_share_link`, `revoke_share_link`, `register_publish_result` |
| `application/jobs/service.py` | `submit_job`, `cancel_job`, `get_job`, `retry_job` |
| `workers/tasks.py` | `execute_job`, `dispatch_job`, `with_job_lease`, `reconcile_orphaned_jobs`, `cleanup_expired_temp_objects` |
| `workers/reconciliation.py` | `dispatch_unsent_outbox`, `reconcile_orphaned_jobs`, `reconcile_pending_uploads`, `reconcile_unregistered_outputs`, `mark_missing_blobs`, `purge_expired_temp_objects`, `recalculate_project_readiness` |

## 8. API/events/webhooks

| File | Symbols bắt buộc |
|---|---|
| `api/dependencies.py` | `get_current_actor`, `require_workspace_role`, `get_uow`, `get_services`, `parse_if_match`, `require_idempotency_key` |
| `api/errors.py` | `map_domain_error`, `validation_exception_handler` |
| `api/v1/identity.py` | `get_me_route` |
| `api/v1/workspaces.py` | `list_workspaces_route`, `get_workspace_route`, `patch_workspace_route`, `list_members_route`, `create_invitation_route`, `patch_member_route`, `delete_member_route`, `get_usage_route`, `get_provider_config_route`, `put_provider_config_route` |
| `api/v1/projects.py` | `list_projects_route`, `create_project_route`, `get_project_route`, `patch_project_route`, `clone_project_route`, `archive_project_route`, `restore_project_route` |
| `api/v1/scripts.py` | `create_script_job_route`, `put_script_route`, `approve_script_route` |
| `api/v1/voice.py` | `create_voice_job_route`, `get_voice_config_route` |
| `api/v1/assets.py` | `create_upload_route`, `complete_upload_route`, `create_remote_import_job_route`, `list_assets_route`, `get_asset_route`, `patch_asset_route`, `archive_asset_route`, `create_processing_job_route`, `get_asset_content_route` |
| `api/v1/scenes.py` | `create_scene_plan_job_route`, `get_scene_plan_route` |
| `api/v1/timelines.py` | `create_timeline_job_route`, `get_timeline_route`, `put_postprocess_config_route` |
| `api/v1/renders.py` | `create_render_job_route`, `list_render_outputs_route` |
| `api/v1/jobs.py` | `get_job_route`, `cancel_job_route`, `retry_job_route` |
| `api/v1/events.py` | `stream_events_route` |
| `api/v1/webhooks.py` | `list_webhooks_route`, `create_webhook_route`, `patch_webhook_route`, `delete_webhook_route`, `rotate_webhook_secret_route`, `test_webhook_route` |
| `api/v1/publish.py` | `create_export_job_route`, `get_publish_result_route` |
| `api/v1/share_links.py` | `create_share_link_route`, `revoke_share_link_route` |
| `application/workspaces/service.py` | `get_me`, `list_workspaces`, `get_workspace`, `update_workspace`, `invite_member`, `update_member_role`, `remove_member`, `get_workspace_usage`, `update_provider_config` |
| `application/events/service.py` | `subscribe`, `publish_after_commit`, `authorize_event` |
| `application/webhooks/service.py` | `list_webhooks`, `create_webhook`, `update_webhook`, `delete_webhook`, `rotate_webhook_secret`, `test_webhook`, `enqueue_deliveries`, `sign_payload`, `deliver_webhook` |

## 9. Security/telemetry

| File | Symbols bắt buộc |
|---|---|
| `security/jwt.py` | `verify_access_token` |
| `security/permissions.py` | `resolve_actor`, `authorize`, `require_permission` |
| `security/rate_limit.py` | `compute_quota_usage`, `enforce_rate_limit` |
| `security/content_policy.py` | `validate_upload_intent`, `validate_detected_media`, `classify_generated_content`, `sanitize_display_filename` |
| `security/url_policy.py` | `parse_https_url`, `resolve_public_addresses`, `validate_address_set`, `fetch_with_redirect_policy` |
| `security/audit.py` | `record_audit_event`, `redact_audit_metadata`, `query_audit_events` |
| `telemetry/logging.py` | `configure_logging`, `redact_log_record` |
| `telemetry/context.py` | `bind_context` |
| `telemetry/metrics.py` | `record_operation_metric` |
| `telemetry/tracing.py` | `start_span` |

## 10. Frontend

| File | Symbols bắt buộc |
|---|---|
| `editor/store/editor-store.ts` | `selectObjects`, `setPlayhead`, `setPlaying`, `beginTransform`, `previewTransform`, `commitTransform`, `pushCommand`, `undo`, `redo`, `clearProjectSession` |
| `editor/store/save-coordinator.ts` | `queuePatch`, `flush`, `handleConflict`, `resolveConflict`, `beforeUnloadGuard` |
| `editor/commands/types.ts` | `apply`, `invert`, `toPatch`, `mergeWith` |
| `editor/player/ProjectPlayer.tsx` | `ProjectPlayer`, `usePlayerController`, `buildPlayerProps`, `preloadVisibleAssets` |
| `editor/canvas/coordinates.ts` | `screenToCompositionPoint`, `compositionToScreenBox` |
| `editor/canvas/transform.ts` | `hitTest`, `computeTransform`, `snapTransform` |
| `editor/timeline/scale.ts` | `useTimelineScale`, `frameToX`, `xToFrame` |
| `editor/timeline/commands.ts` | `buildVisibleRows`, `moveItem`, `resizeItem` |
| `editor/player/buffer.ts` | `handleBufferState` |
| `api/events.ts` | `useProjectEvents` |
| `features/projects/api.ts` | `useProject`, `useUpdateProject`, `useArtifact`, `useArtifactHistory` |
| `features/jobs/api.ts` | `useSubmitJob`, `useJob`, `useCancelJob`, `useRetryJob` |

## 11. Contract/database migrations

| File | Symbols bắt buộc |
|---|---|
| `application/migrations/contracts.py` | `find_migration`, `migrate_document`, `validate_migration_result` |

## 12. Implementation order

1. Contracts/generated types/time/geometry.
2. DB/UoW/repositories/artifact invalidation.
3. API/auth/idempotency/jobs/storage.
4. Script/voice/assets.
5. Scene/timeline compiler.
6. Shared video package/render worker.
7. Frontend editor.
8. Publish, observability, hardening và production E2E.

Không triển khai UI dựa trên schema tạm trước bước 1; nếu không sẽ tạo ba nguồn types cạnh tranh.
