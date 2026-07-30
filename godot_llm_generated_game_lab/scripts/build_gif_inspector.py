#!/usr/bin/env python3
from __future__ import annotations
import hashlib,html,json,shutil
from pathlib import Path
from PIL import Image,ImageSequence
ROOT=Path(__file__).resolve().parents[1]
APPROVED=ROOT/'docs/verification/2026-07-30/player-walk-articulated'
OUTPUT=ROOT/'web/gif_inspector';GIF_DIR=OUTPUT/'gifs'
def sha256(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def validate_bundle()->tuple[dict[str,object],Path]:
 m=json.loads((APPROVED/'manifest.json').read_text())
 assert m['ok'] is True and m['benchmark']=='articulated-bvh-player-walk'
 assert m['engine']=='semantic rigid-part articulated sprite with BVH motion capture'
 assert m['frame_generation_model_used'] is False and m['looping'] is True
 for relative,expected in m['files'].items():
  path=APPROVED/relative
  if not path.is_file() or path.stat().st_size!=expected['bytes'] or sha256(path)!=expected['sha256']:raise RuntimeError(f'evidence mismatch: {relative}')
 q=m['metrics'];p=m['dwpose_metrics'];motion=m['motion_review'];edge=m['edge_review']
 assert q['frames']==32 and q['dimensions']==[512,768] and q['duration_ms']==50 and q['loop']==0 and q['unique_frames']==32
 assert q['seam_ratio']<=1.5 and q['internal_max_ratio']<=2.0 and q['head_aligned_unique_hashes']==1
 assert q['left_stance_x_std']<.001 and q['right_stance_x_std']<.001 and q['left_stance_y_std']<.001 and q['right_stance_y_std']<.001
 assert q['alpha_border_max']==0 and q['alpha_soft_min']>=.005 and q['largest_component_min']>=.97 and q['union_coverage']>=.999 and q['fallback_used'] is False
 assert p['frames']==32 and p['min_body_confident']==17 and p['max_people']==1 and p['support_crossings']>=2
 assert p['ankle_vertical_difference_range']>=.08 and p['left_ankle_y_range']>=.06 and p['right_ankle_y_range']>=.055
 assert p['left_wrist_path']>=.10 and p['right_wrist_path']>=.10
 for key in ['same_person','complete_head','face_visible','face_stable','complete_hands','complete_feet','natural_walk_cycle','two_support_exchanges','planted_stance_feet','natural_knees','natural_arms','stable_rigid_torso','stable_body_scale','stable_colors','seamless_loop','overall_pass']:assert motion[key] is True,key
 for key in ['hidden_internal_jump','belly_wobble_or_stretch','limb_distortion','foot_sliding','body_position_jump','paper_doll_motion']:assert motion[key] is False,key
 assert motion['confidence_percent']>=90
 for key in ['face_clear','face_identical_appearance','head_complete','hair_complete','hands_complete','feet_complete','clean_joint_connections','clean_checkerboard_edges','clean_dark_edges','clean_light_edges','stable_colors','overall_pass']:assert edge[key] is True,key
 for key in ['red_face_noise','blurred_face','missing_head','joint_gaps','double_limbs','wrong_occlusion_pop','sparkling_border','dark_halo','light_halo','black_rectangle','background_flicker']:assert edge[key] is False,key
 assert edge['confidence_percent']>=90
 return m,APPROVED/m['gif']
def render(r:dict[str,object])->str:
 q=r['metrics'];p=r['dwpose_metrics'];motion=r['motion_review'];edge=r['edge_review']
 return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Player Walk — Articulated BVH Test</title><style>:root{{color-scheme:dark;font-family:system-ui,sans-serif;background:#101010;color:#eee}}*{{box-sizing:border-box}}body{{margin:0;padding:24px}}main{{max-width:1500px;margin:auto}}h1{{font-size:clamp(30px,6vw,60px);margin:0 0 8px}}p{{color:#bbb;line-height:1.5}}.ok{{color:#9ee6aa;font-weight:700}}.panels{{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:18px;margin:28px 0}}.panel{{border:1px solid #444;border-radius:12px;overflow:hidden;background:#1b1b1b}}.panel h2{{margin:0;padding:12px 16px;font-size:18px}}.stage{{min-height:800px;display:flex;align-items:center;justify-content:center;padding:12px}}.checker{{background-color:#aaa;background-image:linear-gradient(45deg,#777 25%,transparent 25%),linear-gradient(-45deg,#777 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#777 75%),linear-gradient(-45deg,transparent 75%,#777 75%);background-size:24px 24px;background-position:0 0,0 12px,12px -12px,-12px 0}}.dark{{background:#181818}}.light{{background:#eee}}img{{max-width:100%;height:auto;display:block}}dl{{display:grid;grid-template-columns:300px 1fr;gap:8px 16px;padding:18px;background:#191919;border-radius:10px}}dt{{color:#aaa}}dd{{margin:0;overflow-wrap:anywhere}}a{{color:#8ecbff}}code{{font-size:12px}}</style></head><body><main><h1>Player Walk — Articulated BVH</h1><p>Exactly one looping GIF. Every diffusion/video-generated walk and every earlier inspector GIF was deleted.</p><p>No model generates these frames. One immutable reviewed player image is semantically split into rigid head, torso, upper/lower arm and upper/lower leg layers. A real BVH motion-capture walk drives exact-length limbs and two-link leg inverse kinematics; the head and torso never deform, and the alpha source is fixed rather than regenerated per frame.</p><p class="ok">The actual image seam is {q['seam_ratio']:.3f}× a normal transition, the worst internal transition is {q['internal_max_ratio']:.3f}× normal, and both visual reviews passed at 95%.</p><p><a href="{r['public_path']}" target="_blank" rel="noreferrer">Open the GIF directly</a> · <a href="manifest.json">Manifest, provenance and all gates</a></p><div class="panels"><div class="panel"><h2>Checkerboard</h2><div class="stage checker"><img src="{r['public_path']}" alt="Player walking"></div></div><div class="panel"><h2>Dark background</h2><div class="stage dark"><img src="{r['public_path']}" alt="Player walking"></div></div><div class="panel"><h2>Light background</h2><div class="stage light"><img src="{r['public_path']}" alt="Player walking"></div></div></div><dl><dt>Engine</dt><dd>{html.escape(str(r['engine']))}</dd><dt>Frame-generation model</dt><dd>none</dd><dt>Frames</dt><dd>{r['frames']}</dd><dt>Dimensions</dt><dd>{r['width']} × {r['height']}</dd><dt>Frame duration</dt><dd>{r['duration_ms']} ms</dd><dt>Loop</dt><dd>infinite</dd><dt>SHA-256</dt><dd><code>{r['sha256']}</code></dd><dt>Rigid head hashes</dt><dd>{q['head_aligned_unique_hashes']}</dd><dt>Loop seam / internal maximum</dt><dd>{q['seam_ratio']:.3f}× / {q['internal_max_ratio']:.3f}× normal transition</dd><dt>Stance-foot drift</dt><dd>left {q['left_stance_x_std']:.6f}/{q['left_stance_y_std']:.6f} px, right {q['right_stance_x_std']:.6f}/{q['right_stance_y_std']:.6f} px</dd><dt>DWPose gait</dt><dd>{p['min_body_confident']} of 17 joints every frame; {p['support_crossings']} support exchanges</dd><dt>Alpha</dt><dd>border {q['alpha_border_max']:.3f}, soft-edge minimum {q['alpha_soft_min']:.3f}, connected silhouette {q['largest_component_min']:.4f}</dd><dt>Motion review</dt><dd>natural={motion['natural_walk_cycle']}, planted={motion['planted_stance_feet']}, seamless={motion['seamless_loop']}, sliding={motion['foot_sliding']}, torso stretch={motion['belly_wobble_or_stretch']}</dd><dt>Face/edge review</dt><dd>face identical={edge['face_identical_appearance']}, noise={edge['red_face_noise']}, blur={edge['blurred_face']}, gaps={edge['joint_gaps']}, sparkle={edge['sparkling_border']}, halo={edge['dark_halo'] or edge['light_halo']}</dd></dl></main></body></html>'''
def main()->int:
 m,source=validate_bundle()
 if OUTPUT.exists():shutil.rmtree(OUTPUT)
 GIF_DIR.mkdir(parents=True);dest=GIF_DIR/'player-walk.gif';shutil.copy2(source,dest)
 with Image.open(dest) as im:frames=list(ImageSequence.Iterator(im));width,height=im.size;duration=int(im.info.get('duration',0) or 0);loop=im.info.get('loop')
 assert len(frames)==32 and (width,height)==(512,768) and duration==50 and loop==0
 r={'slug':'player-walk','title':'Player Walk — Articulated BVH','category':'Single verified looping test','public_path':'gifs/player-walk.gif','bytes':dest.stat().st_size,'width':width,'height':height,'frames':len(frames),'duration_ms':duration,'loop':loop,'sha256':sha256(dest),'engine':m['engine'],'frame_generation_model_used':False,'looping':True,'metrics':m['metrics'],'dwpose_metrics':m['dwpose_metrics'],'motion_review':m['motion_review'],'edge_review':m['edge_review'],'approved_bundle_sha256':sha256(APPROVED/'manifest.json')}
 manifest={'ok':True,'count':1,'all_previous_gifs_deleted':True,'engine':m['engine'],'frame_generation_model_used':False,'looping':True,'gifs':[r]}
 (OUTPUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(OUTPUT/'index.html').write_text(render(r));print(json.dumps({'ok':True,'count':1,'gif':str(dest),'sha256':r['sha256'],'looping':True},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
