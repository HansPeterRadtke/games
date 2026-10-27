#!/usr/bin/env python3
"""FINAL PRSE owner research checkpoint, READ-ONLY by default.

A new scientific consistency audit across previously versioned, author-source
and actual native Rapier research receipts. This NEVER re-executes or retries
past denied operations, research model inference, user game, production GPU,
trading or long observer experiments. All data source checks are SHA and
schema based; bounded test labels are not promoted into full-world gold.
Use --write-once only to record the checked NONPRIVATE aggregate after checks;
subsequent default invocations are strictly read only.

This manifest is NEW integration evidence, not proof of a new 3D model result.
"""
from pathlib import Path
from hashlib import sha256
from collections import Counter
from stat import S_IMODE
import json,sys,re,datetime,math

HERE=Path(__file__).resolve().parent
RESEARCH=HERE.parent
VAR=Path('/data/var/games/prse_semantic_research/runs')
INFRA=Path('/data/infra')
FILES={
 'original_games_policy':INFRA/'AGENTS.md',
 'original_games_semantic_policy':INFRA/'docs/guidlines/games/semantic_physics_text_loop.md',
 'owner_aug_17_37':INFRA/'docs/guidlines/original-recordings/games/Recording 2026-08-13 17-37-45-601.txt',
 'owner_aug_18_11':INFRA/'docs/guidlines/original-recordings/games/Recording 2026-08-13 18-11-36-235.txt',
 'owner_oct_12_16':INFRA/'docs/guidlines/original-recordings/games/Recording 2026-10-09 12-16-12-908.txt',
 'owner_oct_18_04':INFRA/'docs/guidlines/original-recordings/games/Recording 2026-10-09 18-04-17-301.txt',
 'round3_causal':RESEARCH/'2026-10-26-round3/prse_round3_hard_human_native_causal_observer_aggregate_v1.json',
 'round3_human_errors':RESEARCH/'2026-10-26-round3/round3_independent_human_source_hard_negative_gold_aggregate_v1.json',
 'round4_user_actual_browser':RESEARCH/'2026-10-26-round4/canonical_current_browser_acceptance_aggregate_v4.json',
 'round5_human_full_input':RESEARCH/'2026-10-26-round5/prse_round5_corrected_source_deployment_accuracy_cost_latency_aggregate_v3.json',
 'round6_human_room_negative':RESEARCH/'2026-10-26-round6/prse_round6_human_explicit_negative_room_reference_native_aggregate_v1.json',
 'round7_3d_human_kind_transfer':RESEARCH/'2026-10-26-round7/prse_round7_nr3d_independent_real3d_reference_aggregate_v1.json',
 'round7_actual_matched_rapier':RESEARCH/'2026-10-26-round7/prse_round7_nr3d_actual_native_rapier_feasibility_aggregate_v1.json',
 'round7_independent_3d_role_gold':RESEARCH/'2026-10-26-round7/prse_round7_independent_physical_roles_actual_gold_aggregate_v1.json',
 'round7_preregistered_original':RESEARCH/'2026-10-26-round7/PREREG_FROZEN_EXTERNAL_NR3D_CROSSGENRE_2026-10-26.md',
 'round8_posthoc_compound':RESEARCH/'2026-10-26-round8/prse_round8_compound_source_posthoc_diagnostic_aggregate_v1.json',
 'round9_saved_physical_room':RESEARCH/'2026-10-27-round9/prse_round9_actual_native_author_room_source_roundtrip_aggregate_v2.json',
 'round9_independent_author_gold':RESEARCH/'2026-10-27-round9/prse_round9_native_human_source_room_semantic_score_aggregate_v1.json',
 'round11_postsave_continuation':RESEARCH/'2026-10-27-round11/prse_round11_native_postsave_replay_and_room_guard_aggregate_v1.json',
 'previous_source_only_principle':RESEARCH/'2026-10-25/PRSE_DECISIVE_FINAL_RESEARCH_CONCLUSION_2026-10-25.md'
}
def digest(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
for name,p in FILES.items():
 assert p.is_file() and p.stat().st_size>100,('missing_original_artifact',name,p)
ORIGINAL={
 'owner_aug_17_37':'371af8a051aa51d6688cc33d5f40a2180be2311545866d39bad7b7b673c0aa44',
 'owner_aug_18_11':'c60b999c6f31dd9721b09dd08eaae9ac73d9500240eacde4b090c32161842a77',
 'owner_oct_12_16':'425cfc8b8587d7b44c5112d94cac5f8348c6eb0294eb19ace5a635565e80aee6',
 'owner_oct_18_04':'2d762aaf65d1dda21943a0d8c1612cc424f8df9c2b679f0e2e2409f958238cf0',
 'round7_preregistered_original':'688fc6d8199b30617a481460386de87a329f8ceeea1f255d2774b7416d06076f'
}
for name,expected in ORIGINAL.items():assert digest(FILES[name])==expected,(name,'SOURCE_CHANGED')
for name in ('owner_aug_17_37','owner_aug_18_11','owner_oct_12_16','owner_oct_18_04'):
 assert 'semantic' in FILES[name].read_text().lower()
assert 'truthful' in FILES['original_games_semantic_policy'].read_text().lower() or 'narrative' in FILES['original_games_semantic_policy'].read_text().lower()
prior=FILES['previous_source_only_principle'].read_text()
for phrase in ('565 of 1,237','3 of 354','11 for pretrained','first hundred fully human-authored','denied'):
 assert phrase in prior,('prior_claim_not_supported',phrase)
data={key:read(FILES[key]) for key in FILES if FILES[key].suffix=='.json'}
p=data['round3_causal']['summary']
assert p['humanOriginalSourceCases']==7 and p['realNativePhysicalWorldsAndSemanticPersistenceCompleted']==7
assert p['physicallyMovedImpulseSubjects']==6 and p['originalSourceAndBodyIDsAllRestored']==7
assert p['originalIndependentAssetGeometryStillUnproven']
hard=data['round3_human_errors']['measured']
assert hard['old16_machine_claims']==16
assert hard['original_machine_gold_direct_vertical']==4
assert hard['original_machine_gold_nonvertical']==11
assert hard['original_machine_gold_composite_unknown']==1
assert hard['nonvertical_source_new_contact_unsupported']==1
assert hard['posthoc_six_direct_human_positive_added']==6
# The six source positives were selected AFTER observed physical contacts.
assert hard['conditional_selected_explicit_vertical_gold']==10
assert hard['conditional_selected_explicit_vertical_supported_candidate']==9
browser=data['round4_user_actual_browser']['summary']
assert browser['canonicalBrowserPass']
assert browser['projectorSceneNotCreated']
assert browser['studyPhysicsPassed'] and browser['studyResultReceivedAsRealWorkerPhysics']
assert browser['privateBackendAndUIProcessesStopped']
assert browser['canonicalSourceFilesUnchangedDuringTest']
assert browser['productionPortUnused']
assert browser['privateContextNoProductionTabsModified']
assert browser['productionLLMDisabledByInvalidLocalEndpoint']
full=data['round5_human_full_input']['serverVersions']
assert len(full)==2
humanInput={}
for name,m in full.items():
 c=m['classification']
 assert c['all']==1380 and c['full']==130 and c['clause']==1250
 assert c['full_rejected']==128 and c['full_help']==2
 assert c['clause_rejected']==19 and c['clause_help']==1229
 assert c['clause_invalid_game_action']==2
 assert c['unsupported_bench_not_in_user_input']==133
 assert m['originalSceneSuccessfulMaterializations']==0
 assert m['noGpuOrModelInference']
 humanInput[name]={'all':c['all'],'full':c['full'],
  'full_rejected':c['full_rejected'],'full_not_created':130,
  'annotation_rejected':c['clause_rejected'],'annotation_help':c['clause_help'],
  'bad_action_dispatch':c['clause_invalid_game_action'],
  'median_WebSocket_ms':m['medianResponseMs'],
  'p95_WebSocket_ms':m['p95ResponseMs'],
  'all_wall_seconds':m['allRequestWallSeconds']}
assert full['committed_research_viewer_server']['classification']==full['current_canonical_uncommitted_server']['classification']
roomNegative=data['round6_human_room_negative']
assert roomNegative['referenceSourceIDLinkAudit']['explicitIndependentHumanForbiddenRoomObjectCases']==4
assert roomNegative['referenceSourceIDLinkAudit']['strictParentIdUnresolved']==89
assert roomNegative['referenceSourceIDLinkAudit']['allParentReferenceLinks']==2938
assert roomNegative['pairedRequiredOppositeRoomPositivesMissingGlobally']==2
nr3d=data['round7_3d_human_kind_transfer']['metrics']
assert nr3d['independent3DScanScenes']==480
assert nr3d['baselineAllSourceExactTargetKind']==231
assert nr3d['pretrainedAllSourceExactTargetKind']==309
assert nr3d['pairedBySceneGain']==104 and nr3d['pairedBySceneLoss']==26
assert math.isclose(nr3d['pretrainedMinusLexiconAllInputExactTargetGain'],78/480,abs_tol=1e-8)
assert nr3d['preregisteredSourceTransferAccepted'] is False
assert nr3d['preregisteredFullPRSELiteraryWorldGeneralizationAccepted'] is False
assert nr3d['pairedBootstrap95Gain']==[.116667,.208333]
assert nr3d['naturalNontopCaseCount']==71 and nr3d['naturalNontopFalseTopPromotionCount']==0
assert nr3d['actualUnique3DInstanceIDsPredictedByEitherSourceOnlyMethod']==0
phys=data['round7_actual_matched_rapier']['summary']
assert phys['sources']==31 and phys['actualWorldsWithExactNativeSave']==62
assert phys['realNativeSourceSupportContactCount']==15
assert phys['negativeControlNativeContactDifference']==0
assert phys['allBodiesProvisionalGeometry'] and phys['human3DScanNetMeshGroundTruthUnavailable']
roles=data['round7_independent_3d_role_gold']['summary']
assert roles['sourceOnCandidates']==15
assert roles['sourceOnTargetKindCorrect']==11
assert roles['sourceOnBothChildTargetAndAnchorKindCorrect']==4
posthoc=data['round8_posthoc_compound']
assert posthoc['summary']['priorCorrect']==309 and posthoc['summary']['newCorrect']==336
assert posthoc['summary']['changes']==27 and posthoc['summary']['losses']==0
assert posthoc['metadata']['posthocDiagnosticOnly']
assert posthoc['metadata']['preregisteredOutcomeStillFailed']
bounded=data['round9_saved_physical_room']['summary']
assert bounded['inputHumanAuthoredSourceScenes']==3
assert bounded['originalRooms']==8 and bounded['sourcePositiveObjectInstances']==17
assert bounded['sourceNegativeRoomFacts']==4
assert bounded['casesNativeSuccessful']==3
assert bounded['validFullSourceScenes']==0
assert bounded['independentHumanTargetNarrationValidated']==0
assert bounded['allAssetDimensionsProvisional']
human=data['round9_independent_author_gold']['summary']
assert human['humanLabelMatchedPhysicalInstances']==17
assert human['officialHumanConstraintsInTheseScenes']==37
assert human['sourceGoldComputerSupportClausesUnfulfilled']==1
assert human['authorExplicitComputerOnDeskSupportsUnfulfilled']==2
assert human['sourceGoldRoomAdjacencyClausesViolated']==1
assert human['measuredActualPlatformGapCm']==800
assert human['completeLiteraryScenesAccepted']==0
follow=data['round11_postsave_continuation']['summary']
assert follow['previousRound9NativeRigidBodiesReproduced']==65
assert follow['newNoActionNativeControlsExact']==3
assert follow['newPositiveStrongImpulseScenarios']==3
assert follow['newStrongImpulseNativeReplayNotExact']==2
assert follow['newImpulseMagnitudeFollowupCases']==6
assert follow['lowMediumHighNewImpulseReplayDiscrepancyAbove1cm']==4
assert math.isclose(follow['nativeBinaryMaxAfterFutureActionDifferenceMetres'],.2177102,abs_tol=1e-7)
assert math.isclose(follow['jsonReconstructionMaxAfterFutureActionDifferenceMetres'],.6587755,abs_tol=1e-7)
assert follow['initialNativeRestoresExactIncludingOriginalContactIDs']==12
assert follow['initialJSONRestoresWithMatchingContactIDs']==0
assert follow['postContinuationNativeContactPairIDsMatched']==12
assert follow['fullLiteraryWorldsVerified']==0
assert follow['independentHumanPostEventObserverTextGoldAvailable'] is False
# Source private evidence files were already checked comprehensively by the
# previous exact version-specific verifiers, which DO NOT launch experiments.
# New manifest checks the latest official human-labeled and source cohorts.
SOURCE_FILES={
 'external_nr3d_csv':VAR/'2026-10-26-nr3d-independent-r7/ScanEnts3D_Nr3D_official_raw.csv',
 'original_lego_human_labels':VAR/'2026-10-26-lego-independent/lego_full_data_public_human_gold.json',
 'actual_lego_native_extended':VAR/'2026-10-26-lego-source-extended-v1/lego_extended_actual_native_matched_130_raw_v2.json',
 'round9_frozen_real_world':VAR/'2026-10-27-prse-round9-room-contract/room_source_to_native_to_factual_text_v3_raw_v2.json',
 'round11_real_future_continuation':VAR/'2026-10-27-prse-round11-causal-restore/round11_actual_native_three_human_source_continuation_raw_v1.json',
 'round11_impulse_followup':VAR/'2026-10-27-prse-round11-causal-restore/round11_native_impulse_strength_diagnostic_raw_v2.json'
}
for name,p in SOURCE_FILES.items():assert p.exists() and S_IMODE(p.stat().st_mode)==0o600,('PRIVATE_EVIDENCE_MISSING_OR_EXPOSED',name)
assert digest(SOURCE_FILES['external_nr3d_csv'])=='f6b437e2bfc15c69c2b497c755e9a5b42eec110dccc25deb29594e3734a31f5b'
assert digest(SOURCE_FILES['original_lego_human_labels'])=='c4cab948b923b522b9ba4991e167e1c5c7d503786f2b2e5c11a64dab89113c21'
assert digest(SOURCE_FILES['actual_lego_native_extended'])=='883d60cf2b458fc4a956b2823b117d0572d347d216643c8b55987e1be57bbc8c'
assert digest(SOURCE_FILES['round9_frozen_real_world'])=='c66a6e814dfd504d93c01fe0232c738421a3138efe082930f57a54790af0fa89'
privateRoot=VAR/'2026-10-27-prse-round11-causal-restore'
assert S_IMODE(privateRoot.stat().st_mode)==0o700
assert data['round11_postsave_continuation']['metadata']['round11InitialActualNativeContinuationSHA256']==digest(SOURCE_FILES['round11_real_future_continuation'])
assert data['round11_postsave_continuation']['metadata']['round11IndependentImpulseMagnitudePhysicalEvidenceSHA256']==digest(SOURCE_FILES['round11_impulse_followup'])
benchmark_gold=read(SOURCE_FILES['original_lego_human_labels'])
assert len(benchmark_gold)==130 and sum(len(x['labels']) for x in benchmark_gold)==1250
assert len(read(SOURCE_FILES['actual_lego_native_extended'])['rows'])==130
verified={
 'checkpointType':'owner-final-postdeadline-readonly-scientific-handoff',
 'ownerTaskDesiredCutoffLocal':'2026-10-27 06:00 Europe/Berlin',
 'verifiedAtLocal':datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
 'originalOwnerRecordedGoalsVerifiedAgainstFourOriginalTranscriptHashes':True,
 'independentPreviousSourceFilesChecked':len(FILES),
 'frozenPrivatePrimaryFilesVerifiedAndNotExposed':len(SOURCE_FILES),
 'publicArtifactSourceSHA256':{k:digest(p) for k,p in FILES.items()},
 'privateEvidenceOnlySHA256':{k:digest(p) for k,p in SOURCE_FILES.items()},
 'originalIndependentHumanWholeLiteraryScenes':130,
 'originalHumanAnnotatedClauses':1250,
 'realUserGameSuccessfullyImportedExternalLiteraryScenes':0,
 'realUserGameFullHumanSceneTextLengthRejected':128,
 'realUserGameShortLiteraryFullSourcesNotImplemented':2,
 'independentCrossGenreScenesWithPreRegisteredTargetClassGold':480,
 'independentCrossGenrePretrainedCorrectCategories':309,
 'independentCrossGenrePretrainedTargetKindCorrectFraction':309/480,
 'independentCrossGenrePretrainedGainPairedBootstrap95':nr3d['pairedBootstrap95Gain'],
 'independentCrossGenrePreRegisteredAccuracyAccepted':False,
 'posthocFixedCompoundLabelsCorrectOnPreviouslySeenSamples':336,
 'posthocFixedCompoundNewTrulyHeldoutAccuracyAvailable':False,
 'provisionalSourceRealRapierWorldsWithSourceRoomIDs':3,
 'provisionalSourceNativeBodyInstances':17,
 'completeOriginalLiteraryScenesAuthorValidated':0,
 'independentHumanSourceSupportsProvenExhaustively':False,
 'nativeRapierActualMatchedPhysicallyNamedContacts':15,
 'supportedContactsWithBothIndependentHumanPhraseRoles':4,
 'originalSourceNonphysicalNegationsProvenByDeletionOnly':False,
 'nativeImmediateBinaryRestoreExactIn12ControlledFollowups':True,
 'nativeFutureTrajectoryAfterIdenticalPhysicalActionAlwaysExact':False,
 'nativeFutureTrajectoryDifferentInStrongActionCases':2,
 'nativeFutureTrajectoryStrongActionCases':3,
 'nativeImpulseStrengthCasesOverOneCentimetreDifference':4,
 'nativeImpulseStrengthCases':6,
 'actualRemainingUnprovedElements':['complete_human_authored_literary_import_to_player_actual_world',
  'independently_human_labeled_referents_with_room_qualified_real_asset_meshes_and_dimensions',
  'actual_3d_support_and_full_room_connectivity_matches_source',
  'general_event_causal_scientific_model_beyond_bounded_examples',
  'deterministic_native_postsave_future_actions',
  'fully_grounded_observer_limited_literary_text_after_real_hidden_offscreen_evolution_and_rematerialization',
  'full_cost_controlled_deployment_vs_baseline_inference_compute_latency'],
 'remoteGitWasVerifiedSeparatelyByReadOnlyGitFetchLsRemote':True,
 'deniedRandomFeasibleParentPlaceboEverRetried':False,
 'blockedObserverLargeTestEverRetried':False,
 'noPhysicsExperimentRerunInThisFinalCheckpoint':True,
 'noLiveGameProductionGPUOrOtherAgentFilesModified':True,
 'status':'PARTIAL'
}
# No source excerpts or model-generated proprietary source text in Git.
out=HERE/'prse_final_crossstudy_human_native_source_evidence_aggregate_v1.json'
if '--write-once' in sys.argv:
 with out.open('x') as f:json.dump(verified,f,indent=2,sort_keys=True);f.write('\n')
if out.exists():
 stored=read(out)
 # Time of original one-time write differs on a later rerunnable verifier.
 verified['verifiedAtLocal']=stored['verifiedAtLocal']
 assert stored==verified,'Previously frozen final audit changed under same source inputs'
print('FINAL VERIFIED SOURCE/REMOTE RESEARCH CROSS-STUDY: PARTIAL')
print('13+ prior verified research files + four original recordings + six protected scientific receipts match immutable hashes.')
print('130 human original scenes, zero user imported; 480 truly different human 3D language scenes, 309 category successes.')
print('3 source-qualified real 3D native worlds/17 objects/8 provisional rooms, zero fully source-validated literary worlds.')
print('12 immediate native exact restores; 2/3 high impulse future physics not exact; 4/6 magnitude tests exceed 1cm.')
print('Observer-specific human literary gold, approved geometry, causality-complete semantic return and full costs remain unavailable.')
print('No rerun of denied experiments, no effect on live systems, status PARTIAL.')
