"""Full-roster, photo-only drop selection shared by Streamlit layouts."""
import streamlit as st
from player_portraits import portrait_id,unique_roster

def drop_picker(rows,key):
    rows=unique_roster(rows)
    html='<div id="portraits"></div>'
    css='#portraits{display:grid;grid-template-columns:repeat(auto-fill,minmax(72px,1fr));gap:8px}button{position:relative;border:3px solid #cbd5df;border-radius:12px;background:transparent;padding:2px;height:82px;cursor:pointer}button[aria-pressed="true"]{border-color:#d9634d;background:#d9634d22}img{width:100%;height:70px;object-fit:contain}small{position:absolute;right:3px;top:3px;color:#b43737}button:focus-visible{outline:3px solid #36a99d}'
    js="""export default function(component){const {data,parentElement:root}=component;const grid=root.querySelector('#portraits');grid.replaceChildren();let selected=new Set(data.selected);for(const p of data.rows){const b=document.createElement('button');b.type='button';b.title=p.name;b.setAttribute('aria-label',p.name+(p.il?' · 傷兵':''));b.setAttribute('aria-pressed',String(selected.has(p.id)));const img=document.createElement('img');img.src=p.photo;img.alt=p.name;b.append(img);if(p.il){const badge=document.createElement('small');badge.textContent='IL';b.append(badge);}b.onclick=()=>{selected.has(p.id)?selected.delete(p.id):selected.add(p.id);b.setAttribute('aria-pressed',String(selected.has(p.id)));component.setTriggerValue('selection',[...selected]);};grid.append(b);}}"""
    widget=st.components.v2.component('weekly_rotation_photos',html=html,css=css.replace('}', '}\n'),js=js.replace(';',';\n'))
    selected=st.session_state.get(key+'_selected',[])
    def update():st.session_state[key+'_selected']=st.session_state.get(key,{}).get('selection',[])
    widget(key=key,on_selection_change=update,data={'selected':selected,'rows':[{'id':str(r.get('id') or r['name']),'name':r['name'],'il':r.get('status')=='IL','photo':'https://cdn.nba.com/headshots/nba/latest/260x190/'+portrait_id(r)+'.png'} for r in rows]},height='content')
    return st.session_state.get(key+'_selected',[])
