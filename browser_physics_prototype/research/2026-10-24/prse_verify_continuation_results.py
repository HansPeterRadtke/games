#!/usr/bin/env python3
"""Independent, read-only evidence consistency checks for the PRSE continuation.

This is not a replacement for running physics. It checks immutable result
claims against each other and rejects accidental promotion of old negatives.
"""
from pathlib import Path
import json

root=Path(__file__).parent

def read(name):
    return json.loads((root/name).read_text())

old=read('prse_semantic_adversarial_results.json')
fixed=read('prse_clock_reentry_prose_v3.json')
visible=read('prse_observer_reentry_prose_v3.json')
native=read('prse_native_offscreen_ash_reentry_gap.json')
lineage=read('prse_ash_lineage_capacity_guard_results.json')
counter=read('prse_clock_counterfactual_visible_vs_offscreen.json')
scene=read('prse_native_clock_observer_scoped_physics_regression.json')
automatic=read('prse_auto_native_clock_scene_pipeline.json')
baseline=read('prse_auto_external_text_to_physics_results.json')
assert old['noCauseNoDamage']['semanticVsGameCoreTimeGapSeconds']>60
assert abs(fixed['differences']['authoritativeSceneClockDelta'])<1e-6
assert fixed['differences']['offscreenPhysicsTicks']==0
assert fixed['differences']['nativeEvents']==7
assert fixed['reentry']['materializedSurvivingEntities']==2
assert fixed['reentry']['destroyedStableIdPreserved']
assert all(fixed['differences']['invalidSnapshotRejections'].values())
assert visible['offscreen']['nativeTimeError']<1e-6
assert visible['before']['offscreenNoEventsLeaked']
assert visible['offscreen']['offscreenNoLeakAfterRestore']
assert 'Ash from note remains' in visible['reentry']['description']
assert visible['reentry']['description'].count('Ash from note')==1
assert visible['support']['potSupport'] is None
assert len(visible['support']['supportEvents'])>=1
assert native['nativePhysical']['originalNoteBodyMaterialized']
assert native['nativePhysical']['originalNoteColliderCount']==0
assert not native['nativePhysical']['distinctAshEntityFound']
assert native['narrative']['textClaimsAsh']
assert lineage['stableDerivedPhysicalRemnant']['explicitOriginReferenceVerified']
assert lineage['stableDerivedPhysicalRemnant']['forgedOriginRejected']
assert lineage['boundedCapacityBehavior']['rejected']
assert lineage['boundedCapacityBehavior']['causalEntryStillPending']==1
assert lineage['activeGoalSkipsRefused']
assert counter['comparison']['sameSevenNativeCausalEvents']
assert counter['comparison']['sameNativeSemanticFinalConditions']
assert abs(counter['comparison']['timeDifferenceSeconds'])<1e-6
assert not counter['comparison']['fullStateEquivalent']
assert counter['comparison']['controlledDifferences']['physicsTicksDifference']==2400
assert counter['comparison']['controlledDifferences']['hydrationDelta']>0
assert counter['fullSimulation']['wallMs']>0 and counter['offscreenOnly']['wallMs']>0
assert len(scene['rooms'])==6 and all(x['stableIds'] for x in scene['rooms'])
assert len(scene['physicalContact']['impactEvents'])==2
assert any(set(x['ids'])=={'ball-1','pot-2'} for x in scene['physicalContact']['impactEvents'])
assert scene['physicalContact']['physicalEventCount']>=3
assert scene['physicalContact']['duplicateAfterCursor']==0
assert scene['offscreenDamage']['offscreenNoLeak']
assert scene['offscreenDamage']['survivingBodies']==2
assert 'Ash from note' in scene['offscreenDamage']['descriptiveReturn']
assert all(x['rejected'] for x in scene['negativeSceneValidation'])
for name in ['inputCount','physicalAccepted','savedConsistently']:
    assert automatic['summary'][name]==baseline['summary'][name]
assert automatic['summary']['inputCount']==34
assert automatic['summary']['physicalAccepted']==33
assert automatic['summary']['relationGroundingVerified']==0
print('PASS: previous time bug retained; unified native/semantic time, '
      'seven causal stages, observer nonleak, ash lineage and reentry, '
      'native ash gap, support relation, incomplete player need changes '
      'and unrelated SceneEval parser limitations verified across source JSON.')
