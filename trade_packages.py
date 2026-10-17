"""Enumerate near-value NBA fantasy trades, with explicit roster balancing."""
from itertools import combinations
import numpy as np
from ninecat_model import CATS,KEYS,zscore,weighted_z,aggregate,value,gap,utility,bundle

def near_value_trades(own,other,pool,ref,my_weights,their_weights,n_send=2,n_receive=2,tolerance=.25,
                      my_fill=(),their_fill=(),my_release=(),their_release=(),both_improve=True,limit=50,positions=(),prefer_middle=True,my_protected=(),their_protected=(),market_values=None,draft_picks=None,draft_guard_samples=None):
    if not 1<=n_send<=4 or not 1<=n_receive<=4:
        raise ValueError('每方交易人數必須介於1到4。')
    mine=[str(r['id']) for r in own if str(r.get('id')) in pool]
    theirs=[str(r['id']) for r in other if str(r.get('id')) in pool]
    if set(mine)&set(theirs): raise ValueError('雙方球隊名單重複，請重新選擇。')
    my_fill,their_fill,my_release,their_release=map(list,(my_fill,their_fill,my_release,their_release))
    if len(my_fill)!=max(n_send-n_receive,0) or len(their_fill)!=max(n_receive-n_send,0):
        raise ValueError('請填滿多出空位的補進球員。')
    if len(my_release)!=max(n_receive-n_send,0) or len(their_release)!=max(n_send-n_receive,0):
        raise ValueError('請指定超出席位時額外釋出的球員。')
    extras=my_fill+their_fill
    if len(extras)!=len(set(extras)) or set(extras)&set(mine+theirs):
        raise ValueError('補進球員不可重複或已在雙方名單。')
    if not set(my_release)<=set(mine) or not set(their_release)<=set(theirs):
        raise ValueError('額外釋出球員必須在該方名單。')
    if len(set(my_release))!=len(my_release) or len(set(their_release))!=len(their_release):
        raise ValueError('釋出名單不可重複。')
    if any(k not in pool for k in extras): raise ValueError('補進球員缺少數據，不能以0計算。')
    if set(my_release)&set(my_protected) or set(their_release)&set(their_protected):
        raise ValueError('非賣品不能被額外釋出。')
    mine_pool=[k for k in mine if k not in my_release and k not in my_protected]
    their_pool=[k for k in theirs if k not in their_release and k not in their_protected]
    left=list(combinations(mine_pool,n_send));right=list(combinations(their_pool,n_receive))
    if positions:
        right=[pack for pack in right if all(any(pos in pool[k].get('eligible',set()) for k in pack) for pos in positions)]
    if not left or not right: return []
    if len(left)*len(right)>2000000:
        raise ValueError('候選組合超過200萬，請先縮小可交易名單。')
    eq={c:1 for c in CATS}
    statistical_price={k:weighted_z(p,ref,eq) for k,p in pool.items()}
    price=statistical_price if market_values is None else market_values
    if any(k not in price or not np.isfinite(price[k]) for k in mine+theirs+extras):
        raise ValueError('交易價值資料不完整，無法比較。')
    amounts=lambda packs:np.array([sum(price[k] for k in pack) for pack in packs])
    left_price,right_price=amounts(left),amounts(right)
    adjustment=lambda filled,released:sum(price[k] for k in filled)-sum(price[k] for k in released)
    dm=right_price[None,:]-left_price[:,None]+adjustment(my_fill,my_release)
    dt=left_price[:,None]-right_price[None,:]+adjustment(their_fill,their_release)
    fairness=np.maximum(np.abs(dm),np.abs(dt))
    valid=fairness<=tolerance
    if draft_picks and n_send==n_receive and n_send>=2:
        lp=np.array([sorted(draft_picks.get(k) or 0 for k in pack) for pack in left])
        rp=np.array([sorted(draft_picks.get(k) or 0 for k in pack) for pack in right])
        known=(lp>0).all(axis=1)[:,None] & (rp>0).all(axis=1)[None,:]
        differences=lp[:,None,:]-rp[None,:,:]
        dominated=((differences>0).all(axis=2)|(differences<0).all(axis=2)) & (np.abs(differences).mean(axis=2)>=14)
        early=np.ones(valid.shape,dtype=bool)
        if draft_guard_samples is not None:
            early=np.array([all(draft_guard_samples.get(k,0)<20 for k in pack) for pack in left])[:,None] & np.array([all(draft_guard_samples.get(k,0)<20 for k in pack) for pack in right])[None,:]
        valid &= ~(known & dominated & early)
    def all_totals(ids): return np.array([sum(pool[k][c] for k in ids) for c in KEYS],dtype=float)
    send=np.array([all_totals(pack) for pack in left])
    receive=np.array([all_totals(pack) for pack in right])
    m_before=all_totals(mine);t_before=all_totals(theirs)
    my_after=m_before[None,None,:]-send[:,None,:]+receive[None,:,:]+all_totals(my_fill)-all_totals(my_release)
    their_after=t_before[None,None,:]-receive[None,:,:]+send[:,None,:]+all_totals(their_fill)-all_totals(their_release)
    def score(after,before,g,weights):
        change=np.zeros(after.shape[:2])
        focus=np.zeros(after.shape[:2])
        den=sum(weights.values()) or 1
        if g==0: return change,focus
        for c in CATS:
            if c in ('FG','FT'):
                idx,att=KEYS.index(c+'M'),KEYS.index(c+'A')
                x=np.divide(after[:,:,idx],after[:,:,att],out=np.full(after.shape[:2],np.nan),where=after[:,:,att]>0)
                old=before[idx]/before[att] if before[att]>0 else np.nan
            else:
                idx=KEYS.index(c);x=after[:,:,idx]/g;old=before[idx]/g
            if not np.isfinite(old): continue
            mean=ref[c]['mean']
            if mean<=0: continue
            sign=-1 if c=='TOV' else 1
            z=(x-mean)/mean*sign
            before_gap=(old-mean)/mean*sign
            part=np.nan_to_num(100*weights[c]/den*(1/(1+np.exp(-np.clip(z/.2,-50,50)))-utility(before_gap)))
            change+=part
            if weights[c]==max(weights.values()) and weights[c]>0:
                focus+=part
        return change,focus
    mg,mf=score(my_after,m_before,len(mine),my_weights)
    tg,tf=score(their_after,t_before,len(theirs),their_weights)
    if both_improve: valid &= (mg>1e-8)&(tg>1e-8)&(mf>1e-8)&(tf>1e-8)
    ranking=mg+tg if both_improve else mg
    indices=np.flatnonzero(valid)
    if not len(indices): return []
    ordered=sorted(indices,key=lambda k:(-ranking.flat[k],fairness.flat[k]))
    def middle(index):
        i,j=np.unravel_index(index,valid.shape)
        return any(2<=int(pool[k].get('draft_round') or 0)<=8 for k in left[i]) and any(2<=int(pool[k].get('draft_round') or 0)<=8 for k in right[j])
    if prefer_middle:
        preferred=[k for k in ordered if middle(k)]
        others=[k for k in ordered if not middle(k)]
        quota=max(1,int(limit*.75))
        chosen=preferred[:quota]+others[:limit-min(quota,len(preferred))]
        chosen_set=set(chosen)
        chosen.extend(k for k in ordered if k not in chosen_set)
        ordered=chosen[:limit]
    else:
        ordered=ordered[:limit]
    result=[]
    for index in ordered:
        i,j=np.unravel_index(index,valid.shape)
        result.append({'send':list(left[i]),'receive':list(right[j]),'my_gain':float(mg[i,j]),
                       'their_gain':float(tg[i,j]),'my_focus':float(mf[i,j]),'their_focus':float(tf[i,j]),'gap':float(fairness[i,j]),
                       'statistical_gap':abs(sum(statistical_price[k] for k in right[j])+sum(statistical_price[k] for k in my_fill)-sum(statistical_price[k] for k in left[i])-sum(statistical_price[k] for k in my_release)),'middle_rounds':bool(middle(index)),'send_value':float(left_price[i]),'receive_value':float(right_price[j]),
                       'my_value_delta':float(dm[i,j]),'their_value_delta':float(dt[i,j])})
    return result
