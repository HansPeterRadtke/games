from __future__ import annotations
import cv2
import numpy as np
class _CPU:
    def __init__(self,index:int=0): self.index=index
def cpu(index:int=0): return _CPU(index)
class _Batch:
    def __init__(self,array): self.array=array
    def asnumpy(self): return self.array
class VideoReader:
    def __init__(self,path,ctx=None):
        cap=cv2.VideoCapture(str(path))
        if not cap.isOpened(): raise RuntimeError(f'cannot open video: {path}')
        self.fps=float(cap.get(cv2.CAP_PROP_FPS) or 24.0); self.frames=[]
        while True:
            ok,bgr=cap.read()
            if not ok: break
            self.frames.append(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB))
        cap.release()
        if not self.frames: raise RuntimeError(f'no frames: {path}')
    def __len__(self): return len(self.frames)
    def get_avg_fps(self): return self.fps
    def get_batch(self,indices): return _Batch(np.stack([self.frames[int(i)] for i in indices]))
    def __getitem__(self,index): return self.frames[int(index)]
