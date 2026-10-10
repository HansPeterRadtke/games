#!/usr/bin/env python3
"""Idempotently connect validated pre-generated LLM story branches to PRSE streamer."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
generator=ROOT/'world-generator.js';core=ROOT/'physics-core.js'
s=generator.read_text()
imports="import {storyRegionBank} from './generated/story-region-bank.js';\nimport {chooseLiteraryScene,sceneToEntities} from './llm-region-adapter.js';\n"
if 'import {storyRegionBank}' not in s:s=imports+s
source='export function proposeRegion(index){if(!Number.isInteger(index)||index<0||index>=8)throw Error(\'Region outside bounded demo world\');'
target='export function proposeRegion(index,flags={}){if(!Number.isInteger(index)||index<0||index>=8)throw Error(\'Region outside bounded demo world\');\n const literary=chooseLiteraryScene(storyRegionBank.scenes,index,flags);\n if(literary){const result=sceneToEntities(literary);if(!result.ok)throw Error(`Invalid pre-generated LLM region: ${result.error}`);return result.entities;}'
if source in s:s=s.replace(source,target)
assert 'export function proposeRegion(index,flags={})' in s
old='update(playerX,direction,semantic){if(!Number.isFinite(playerX)'
new='update(playerX,direction,semantic,flags={}){if(!Number.isFinite(playerX)'
if old in s:s=s.replace(old,new)
assert 'update(playerX,direction,semantic,flags={})' in s
old='const proposal=proposeRegion(region),check=validateWorldProposal(proposal,existing);'
new='const proposal=proposeRegion(region,flags),check=validateWorldProposal(proposal,existing);'
if old in s:s=s.replace(old,new)
assert new in s
generator.write_text(s)
s=core.read_text();old='this.worldStreamer.update(this.player.translation().x,this.direction,this.semantic)';new='this.worldStreamer.update(this.player.translation().x,this.direction,this.semantic,{bridgeRepaired:this.character.bridgeRepaired,mechanismOpen:this.character.fenceOpened})';
if old in s:s=s.replace(old,new)
assert new in s
core.write_text(s)
print('INTEGRATED',len((ROOT/'generated/story-region-bank.js').read_bytes()),'story bytes into deterministic PRSE streamer')
