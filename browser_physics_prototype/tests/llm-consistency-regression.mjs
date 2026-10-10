import assert from 'node:assert/strict';
import {storyRegionBank} from '../generated/story-region-bank.js';
import {checkNarrativeConsistency} from '../llm-grounding-check.js';
import {sceneToEntities} from '../llm-region-adapter.js';
for(const s of storyRegionBank.scenes){const result=checkNarrativeConsistency(s);assert.equal(result.ok,true,`${s.branch}: ${result.reasons}`);assert.equal(sceneToEntities(s).ok,true);if(s.reconciliation)assert.ok(s.raw_model_description&&s.reconciliation.reason,'Original LLM text and editorial reason must remain auditable');}
const example={...storyRegionBank.scenes.find(x=>x.branch==='bridge_unrepaired'),description:"A split oak grips the broken bridge's abutment. The traveler's footprints reach the far bank."};const outcome=checkNarrativeConsistency(example);assert.equal(outcome.ok,false);assert.ok(outcome.reasons.length>=2);
const distant={...example,description:'An enormous rock arch over the stream.',objects:[{kind:'rock',width_m:.7}]};assert.equal(checkNarrativeConsistency(distant).ok,false,'Unsupported large structure should fail');
console.log(JSON.stringify({passed:true,validatedScenes:storyRegionBank.scenes.length,auditedRevisions:storyRegionBank.scenes.filter(x=>x.reconciliation).length,knownContradictions:outcome.reasons}));
