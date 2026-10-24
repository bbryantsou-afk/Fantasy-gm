"""Allowlist of portable UI preferences; excludes tokens and transient actions."""
import re
ENUMS={
 'visual_theme':{'簡約淺色','戰術板草圖','黑色鏡面'},
 'nc_cohort':{'第三組 · 聯盟選秀名單','第二組 · 六項前100名'},
 'nc_mode':{'我的球隊適配','原始加權 Z-score'},
 'watch_scope':{'全部','我的球員','星號追蹤'},
}
BOOLS={'nc_only_ref','nc_show_z','nc_vacancy'}
TEAM_KEYS={'_my_team','sim_opp_team','stream_opponent'}
REFS={'nc_ref_draft','nc_ref_120','nc_ref_100'}
def preference_key(key):
 return bool(re.fullmatch(r'stream_adds_.+_\d{4}-\d{2}-\d{2}',key)) or key in set(ENUMS)|BOOLS|TEAM_KEYS|REFS|{'nc_scale','nc_games','nc_min_gp'} or bool(re.fullmatch(r'(nc_weight_|auto_m_|auto_t_)(PTS|FG3M|REB|AST|STL|BLK|FG|FT|TOV)',key))
def validate_preferences(prefs,teams):
 if not isinstance(prefs,dict):raise ValueError('設定格式不符。')
 out={}
 for k,v in prefs.items():
  if not preference_key(k):continue
  if k=='nc_cohort' and v=='第一組 · 六項前120名':v='第三組 · 聯盟選秀名單'
  if k.startswith('stream_adds_'):
   if type(v) is not int or not 0<=v<=4:raise ValueError('剩餘加人次數須為 0–4。')
  elif k in ENUMS:
   if not isinstance(v,str) or v not in ENUMS[k]:raise ValueError('偏好選項不符。')
  elif k in BOOLS:
   if type(v) is not bool:raise ValueError('偏好格式不符。')
  elif k in TEAM_KEYS:
   if v not in teams:continue
  elif k in REFS:
   if not isinstance(v,list) or len(v)>1000 or any(not isinstance(x,str) or not x.isdigit() for x in v):raise ValueError('參考母體格式不符。')
   from ninecat_strategy import load_data
   snapshot,_=load_data();known={str(p['PLAYER_ID']) for p in snapshot['players']};v=list(dict.fromkeys(x for x in v if x in known))
  elif k=='nc_scale':
   if v not in [.1,.2,.4]:raise ValueError('差距範圍不符。')
  elif k in ['nc_games','nc_min_gp']:
   if type(v) is not int or not (1<=v<=7 if k=='nc_games' else 0<=v<=82):raise ValueError('場次設定不符。')
  elif type(v) not in (int,float) or not 0<=v<=10:raise ValueError('權重格式不符。')
  out[k]=v
 return out

def capture_preferences(state):
 import copy
 saved=copy.deepcopy(state.get('_portable_preferences',{}))
 for k,v in state.items():
  if preference_key(k) and v is not None:saved[k]=copy.deepcopy(v)
 state['_portable_preferences']=saved
 return saved

def hydrate_preferences(state):
 import copy
 for k,v in state.get('_portable_preferences',{}).items():
  if preference_key(k) and k not in state:state[k]=copy.deepcopy(v)
