#!/usr/bin/env python3
"""Create truthful Unity Asset Store marketing media from *real Unity scene renders*.

The source scene pixels are never AI-generated or altered inside the screenshot
frame. Additional typography, callouts, and a source-architecture graphic are
editorial overlays. All derived media stays outside Git in the release folder.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageStat

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
W, H = 1600, 900
BG = (11, 21, 36)
WHITE = (237, 246, 250)
MUTED = (153, 176, 195)
CYAN = (62, 229, 246)
AMBER = (255, 192, 91)
DIM = (23, 42, 60)


def font(n: int, bold: bool = False):
    return ImageFont.truetype(BOLD if bold else FONT, n)


def scene_check(path: Path):
    if not path.is_file():
        raise FileNotFoundError(f"Actual Unity screenshot required: {path}")
    im = Image.open(path).convert("RGB")
    if im.size != (W, H) or min(ImageStat.Stat(im).stddev) < 5:
        raise ValueError(f"Invalid, blank or wrong-size genuine screenshot: {path}")
    return im


def backdrop():
    im = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(im)
    for y in range(H):
        shift = int(15 * y / H)
        draw.line([(0, y), (W, y)], fill=(11 + shift//3, 21 + shift//2, 36 + shift))
    return im


def text(draw, xy, s, n, color=WHITE, bold=False):
    draw.text(xy, s, font=font(n, bold), fill=color)


def line(draw, xy, color=CYAN, width=4):
    draw.line(xy, fill=color, width=width)


def panel(draw, coords, color=DIM, outline=None, radius=18):
    draw.rounded_rectangle(coords, radius=radius, fill=color, outline=outline, width=2 if outline else 1)


def thumbnail(source: Image.Image, destination: Path):
    im = backdrop()
    d = ImageDraw.Draw(im)
    text(d, (75, 62), "HPR", 38, CYAN, True)
    text(d, (194, 70), "/ MULTIVERSE3D", 26, MUTED)
    line(d, [(75, 122), (1528, 122)], (47, 79, 98), 2)
    text(d, (70, 188), "GAMEPLAY", 76, WHITE, True)
    text(d, (70, 284), "SYSTEMS SUITE", 72, WHITE, True)
    text(d, (78, 410), "TEN MODULAR C# RUNTIMES", 29, CYAN, True)
    text(d, (78, 466), "A real, integrated Unity training lab", 25, MUTED)
    for i, label in enumerate(("COMBAT", "INVENTORY", "ABILITIES", "EVENTS", "SAVE STATE")):
        y = 543 + i * 43
        d.ellipse((83, y+10, 96, y+23), fill=CYAN if i % 2 == 0 else AMBER)
        text(d, (115, y), label, 25, WHITE, True)
    # Show a genuine complete scene render in a framed panel.
    region = (760, 168, 1520, 720)
    panel(d, (region[0]-12, region[1]-12, region[2]+12, region[3]+12),
          (21, 39, 54), (61, 110, 135), 18)
    pic = ImageOps.fit(source, (region[2]-region[0], region[3]-region[1]),
                       method=Image.Resampling.LANCZOS, centering=(.5,.55))
    im.paste(pic, region[:2])
    text(d, (785, 744), "ACTUAL UNITY SCENE   •   PRIMITIVE-BASED DEMO", 18, MUTED)
    line(d, [(75, 842), (1525, 842)], (47,79,98), 2)
    text(d, (76, 857), "MODULAR SOURCE CODE  /  DOCUMENTED WORKFLOWS  /  NO RUNTIME AI SERVICE", 15, MUTED)
    im.save(destination, optimize=True)


def annotated(source: Image.Image, dest: Path):
    im = backdrop()
    d = ImageDraw.Draw(im)
    text(d, (60, 45), "THE INTEGRATED ENCOUNTER", 48, WHITE, True)
    text(d, (63, 114), "Real Unity camera capture • Independent source-level gameplay modules", 22, MUTED)
    shot = ImageOps.fit(source, (1040, 585), Image.Resampling.LANCZOS)
    im.paste(shot, (46, 180))
    d = ImageDraw.Draw(im)
    d.rectangle((46,180,1086,765),outline=(60,112,138),width=3)
    panel(d, (1120,180,1546,765), (23,41,59), (44,85,109))
    text(d, (1146,210), "WHAT THE CODE DOES", 23, CYAN, True)
    notes = [
      ("01 / COMBAT", "Hitscan rays and enemy damage"),
      ("02 / INVENTORY", "Collect a key and medkits"),
      ("03 / ABILITIES", "Stamina, effects and cooldowns"),
      ("04 / EVENTS", "Typed inter-module damage"),
      ("05 / SAVING", "Ammo, state and JSON slots"),
      ("06 / COMPOSITION", "Runtime registry + world data")
    ]
    for i, (head, detail) in enumerate(notes):
        y=270+i*75
        text(d,(1146,y),head,20,AMBER if i%2 else CYAN,True)
        text(d,(1146,y+29),detail,17,WHITE)
    text(d,(52,813),"SCENE IS A PROGRAMMING DEMONSTRATION — NO CHARACTER ART PACK OR NAVMESH ROUTING",17,MUTED)
    im.save(dest,optimize=True)


def architecture(dest: Path):
    im=backdrop()
    d=ImageDraw.Draw(im)
    text(d,(70,70),"TEN MODULES. ONE WORKING SYSTEM.",49,WHITE,True)
    text(d,(73,140),"Typed interfaces and original, editable Unity C# source",27,MUTED)
    blocks=[
      ("GAMEPLAY & COMBAT",["Inventory Core","Stats & Damage","Weapon Runtime","Enemy Runtime"],CYAN),
      ("COORDINATION",["Typed Event Bus","Composition Root","Interaction Toolkit","Ability Runtime"],AMBER),
      ("STATE & WORLD",["Save Snapshots","World Asset Registry"],CYAN)
    ]
    box_w=453
    for col,(name,items,accent) in enumerate(blocks):
        x=70+col*493
        panel(d,(x,228,x+box_w,705),(23,42,60),(53,93,118))
        d.rectangle((x,228,x+box_w,235),fill=accent)
        text(d,(x+27,264),name,25,accent,True)
        for i,item in enumerate(items):
            y=335+i*80
            panel(d,(x+24,y,x+box_w-24,y+57),(31,55,73))
            d.ellipse((x+40,y+18,x+54,y+32),fill=accent)
            text(d,(x+69,y+13),item,22,WHITE)
    text(d,(75,764),"INTEGRATION: playable arena • physical aiming • pickup & gate • state restore",23,WHITE)
    text(d,(77,818),"This is a code toolkit, not a complete game creator or 3D asset pack.",20,MUTED)
    im.save(dest,optimize=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--media",type=Path,required=True)
    a=p.parse_args()
    root=a.media
    first=scene_check(root/"01-arena-actual-unity-camera.png")
    second=scene_check(root/"02-encounter-actual-unity-camera.png")
    output=root/"store"
    output.mkdir(parents=True,exist_ok=True)
    thumbnail(second,output/"01-store-cover.png")
    annotated(first,output/"02-live-encounter.png")
    architecture(output/"03-code-architecture.png")
    for file in sorted(output.glob("*.png")):
        im=Image.open(file)
        assert im.size == (1600,900)
        print("MARKETPLACE_MEDIA_READY",file.name,file.stat().st_size,"bytes")


if __name__=="__main__":
    main()
