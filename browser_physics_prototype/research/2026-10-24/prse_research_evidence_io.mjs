// Read-only access to the private raw SceneEval experiment outputs on Nitro.
// The official benchmark ZIP and complete source-derived text are intentionally
// not redistributed in the public Games research repository.
import {readFileSync} from 'node:fs';
import {join} from 'node:path';
const BASE='/data/var/games/prse_semantic_research/runs/2026-10-25-general-constraints';
export function readResearchEvidence(name){
 if(typeof name!=='string'||!/^[a-zA-Z][a-zA-Z0-9_.-]*\.json$/.test(name))
  throw Error('Unsafe evidence filename');
 try{return readFileSync(new URL(name,import.meta.url),'utf8');}
 catch(e){
  if(e.code!=='ENOENT')throw e;
  return readFileSync(join(process.env.PRSE_SCENEEVAL_RAW_DIR||BASE,name),'utf8');
 }
}
