#!/usr/bin/env python3
"""Reproduce OFFLINE imitation results on authenticated public HUMAN robomimic data.

Does not execute a learned policy in MuJoCo or PRSE; action prediction is not
closed-loop physical competence. Demo-episode split never mixes adjacent frames.
Dataset source: https://huggingface.co/datasets/robomimic/robomimic_datasets
             /resolve/main/v1.5/lift/ph/low_dim_v15.hdf5
Official robomimic Lift PH 200 human teleoperation demonstrations.
"""
import argparse
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.neighbors import KNeighborsRegressor
from sklearn.preprocessing import StandardScaler

def read_split(h5, name):
    names=[x.decode() for x in h5['mask'][name][:]]
    assert len(names)==len(set(names)), 'duplicated episode'
    return names

def read_episode(h5,name):
    group=h5['data'][name]
    X=group['states'][:].astype('float32')
    Y=group['actions'][:].astype('float32')
    assert X.ndim==Y.ndim==2 and X.shape[1]==32 and Y.shape[1]==7
    assert len(X)==len(Y)>0
    assert np.isfinite(X).all() and np.isfinite(Y).all()
    return X,Y,{'steps':len(Y),'rewards':group['rewards'][:].sum(),'done':float(group['dones'][-1])}

def temporal(X,history=4):
    # State input at current and three previous ticks, padded only within episode.
    return np.concatenate([np.roll(X,min(k,len(X)-1),axis=0)
        if k==0 else np.vstack([np.repeat(X[0:1],k,axis=0),X[:-k]])
        for k in range(history)],axis=1)

def metrics(y,p,names):
    rows=[]
    start=0
    for name,actual in names:
        length=len(actual);pred=p[start:start+length];start+=length
        rows.append(float(np.mean((actual-pred)**2)))
    assert start==len(y)
    return {'step_mse':float(np.mean((y-p)**2)),
       'episode_mean_mse':float(np.mean(rows)),
       'episode_mse_sd':float(np.std(rows)),
       'median_abs_error':float(np.median(np.abs(y-p))),
       'end_effector_mse':float(np.mean((y[:,:6]-p[:,:6])**2)),
       'gripper_sign_accuracy':float(np.mean(np.sign(y[:,6])==np.sign(p[:,6])))}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--data',default='/data/var/games/human_habit_research/robomimic_lift_ph_low_dim_v15.hdf5')
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    np.random.seed(1927)
    import torch
    torch.manual_seed(1927);torch.set_num_threads(1)
    path=Path(args.data)
    if not path.is_file() or path.stat().st_size>50_000_000:raise RuntimeError('Missing or oversized public dataset')
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    with h5py.File(path,'r') as h:
        train_ids=read_split(h,'train')
        valid_ids=read_split(h,'valid')
        assert len(train_ids)==180 and len(valid_ids)==20 and not(set(train_ids)&set(valid_ids))
        train=[(id,*read_episode(h,id)) for id in train_ids]
        valid=[(id,*read_episode(h,id)) for id in valid_ids]
        meta={'source':'robomimic v1.5 Lift proficient human low_dim official public HDF5',
              'url':'https://huggingface.co/datasets/robomimic/robomimic_datasets/resolve/main/v1.5/lift/ph/low_dim_v15.hdf5',
              'file_bytes':path.stat().st_size,'sha256':digest,
              'environment':'robosuite Lift MuJoCo, not PRSE; human teleoperation',
              'source_attribution':'Original data creators Mandlekar et al., CoRL 2021',
              'split':'official HDF5 mask/train and mask/valid, disjoint episodes',
              'train_episodes':len(train),'valid_episodes':len(valid),
              'train_steps':sum(len(e[2]) for e in train),
              'valid_steps':sum(len(e[2]) for e in valid),
              'normalization':'train-only StandardScaler; no access to validation before predictions',
              'fixed_random_seed':1927,
              'human_evidence_scope':'action prediction on authentic human demonstrations; NOT autonomous rollout',
              'contact_rich_scope':'lifting task requires object grasp and physical contact, but cannot infer contact success from action error'}
        T=np.concatenate([e[1] for e in train]);Y=np.concatenate([e[2] for e in train])
        V=np.concatenate([e[1] for e in valid]);Z=np.concatenate([e[2] for e in valid])
        Tseq=np.concatenate([temporal(e[1]) for e in train]);Vseq=np.concatenate([temporal(e[1]) for e in valid])
        scaler=StandardScaler().fit(T)
        x=np.clip(scaler.transform(T),-10,10)
        v=np.clip(scaler.transform(V),-10,10)
        ts=StandardScaler().fit(Tseq)
        xseq=np.clip(ts.transform(Tseq),-10,10)
        vseq=np.clip(ts.transform(Vseq),-10,10)
        yscale=StandardScaler().fit(Y)
        sy=yscale.transform(Y)
        pairs=[(e[0],e[2]) for e in valid]
        candidates={}
        def report(name,pred,trainmse=None):
            pred=np.nan_to_num(pred,nan=0,posinf=0,neginf=0)
            obj=metrics(Z,pred,pairs)
            if trainmse is not None:obj['training_action_mse']=float(trainmse)
            candidates[name]=obj
        report('mean_action',np.tile(Y.mean(axis=0),(len(Z),1)))
        # Time-only average sequence, with no peeking at validation episode length.
        bytime=[]
        for t in range(max(len(e[2]) for e in train)):
            bytime.append(np.mean([e[2][t] for e in train if t<len(e[2])],axis=0))
        macro=np.array(bytime)
        estimate=np.vstack([macro[np.minimum(np.arange(len(e[2])),len(macro)-1)]
              for e in valid])
        report('time_only_macro',estimate)
        ridge=Ridge(alpha=10.0).fit(x,sy)
        report('ridge_state',yscale.inverse_transform(ridge.predict(v)),
               np.mean((Y-yscale.inverse_transform(ridge.predict(x)))**2))
        ridge_temporal=Ridge(alpha=50.0).fit(xseq,sy)
        report('ridge_four_frame_history',yscale.inverse_transform(ridge_temporal.predict(vseq)),
               np.mean((Y-yscale.inverse_transform(ridge_temporal.predict(xseq)))**2))
        knn=KNeighborsRegressor(n_neighbors=9,weights='distance',n_jobs=1)
        knn.fit(x,sy)
        report('knn_state',yscale.inverse_transform(knn.predict(v)))
        # Tiny CPU MLP: manually fixed architecture/hyperparameters before validation.
        model=torch.nn.Sequential(torch.nn.Linear(x.shape[1],32),torch.nn.Tanh(),
            torch.nn.Linear(32,32),torch.nn.Tanh(),torch.nn.Linear(32,7))
        opt=torch.optim.Adam(model.parameters(),lr=.002,weight_decay=.0001)
        tx=torch.tensor(x,dtype=torch.float32);ty=torch.tensor(sy,dtype=torch.float32)
        for epoch in range(35):
            order=torch.randperm(len(tx))
            model.train()
            for idx in order.split(256):
                prediction=model(tx[idx])
                loss=torch.mean((prediction-ty[idx])**2)
                opt.zero_grad();loss.backward();opt.step()
        model.eval()
        with torch.no_grad():
            pv=model(torch.tensor(v,dtype=torch.float32)).numpy()
            pt=model(tx).numpy()
        report('tiny_mlp_state',yscale.inverse_transform(pv),
               np.mean((Y-yscale.inverse_transform(pt))**2))
        print('dataset',{'train_episodes':len(train),'validation_episodes':len(valid),
                         'train_frames':len(Y),'validation_frames':len(Z),
                         'finished_demos':sum(vv[3]['done']>0 for vv in valid)})
        for key,val in candidates.items():
            print(key,'heldout_episode_mse',round(val['episode_mean_mse'],5),
                  'gripper_sign_accuracy',round(val['gripper_sign_accuracy'],3),
                  'train_action_mse',round(val.get('training_action_mse',-1),5))
        result={'metadata':meta,'algorithms':candidates,
          'assessment':'No model was executed in MuJoCo or PRSE. Validation used human trajectories only. More accurate next-action predictions may still catastrophically fail in closed-loop control. The official validation episodes are consumed for comparison, not an untouched post-selection test.'}
        out=Path(args.out)
        with out.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
if __name__=='__main__':main()
