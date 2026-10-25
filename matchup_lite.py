"""Optional mobile presentation for the shared, unchanged matchup engine."""
LITE_CSS = """
#lineup-app{padding-bottom:calc(64px + env(safe-area-inset-bottom));font-size:11px}
#lineup-app .board{display:block;min-width:0}
#lineup-app .board>.roster{display:none}
#lineup-app .middle{padding:6px}
#lineup-app .summary{padding:7px;margin-top:8px}
#lineup-app #weekly-table .table-wrap{width:100%;min-width:0}
#lineup-app #weekly-table table{width:100%;min-width:0;table-layout:fixed;font-size:11px;border-spacing:0}
#lineup-app #weekly-table th,#lineup-app #weekly-table td{padding:5px 3px;line-height:1.25;text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
#lineup-app #weekly-table th{font-size:10px}
#lineup-app #weekly-table th:first-child,#lineup-app #weekly-table td:first-child{width:14%;text-align:left}
#lineup-app #weekly-table th:last-child,#lineup-app #weekly-table td:last-child{width:22%;text-align:center}

#lineup-app .head,#lineup-app .lineup-row{grid-template-columns:minmax(0,1fr) 26px minmax(0,1fr);gap:3px}
#lineup-app .lineup-row,#lineup-app .slot{min-height:47px}
#lineup-app .slot{padding:2px}
#lineup-app .player{margin:0;padding:4px;font-size:10px;display:flex;align-items:center;gap:4px}
#lineup-app .lite-name{min-width:0;overflow-wrap:anywhere;line-height:1.2}
#lineup-app .lite-name small{display:block;font-size:9px;opacity:.8}
#lineup-app .lite-avatar{width:29px;height:29px;object-fit:cover;border-radius:50%;background:#1a2435;flex-shrink:0}
#lineup-app .days{gap:2px;min-width:0!important}
#lineup-app .day{font-size:10px;padding:8px 1px}
#lineup-app .editor-fields{grid-template-columns:repeat(3,minmax(0,1fr))}
#lineup-app .editor-panel{padding:12px}
#lineup-app .lite-tray{position:fixed;bottom:0;left:0;right:0;max-height:35dvh;overflow-y:auto;z-index:1000;background:#101826;border-top:1px solid #6c8aa8;padding:10px 6px calc(10px + env(safe-area-inset-bottom));margin-top:12px;border-radius:10px;box-shadow:none}
#lineup-app .lite-tray[hidden]{display:none!important}
#lineup-app.lite-adjusting{padding-bottom:calc(35dvh + 76px)}
#lineup-app .lite-tray-toggle{position:fixed;bottom:0;left:0;right:0;z-index:1001;min-height:48px;width:100%;margin:0;padding:10px 12px calc(10px + env(safe-area-inset-bottom));background:#172238;color:#edf3ff;border:1px solid #6c8aa8;border-radius:10px 10px 0 0}
#lineup-app.lite-adjusting .lite-tray-toggle{bottom:35dvh;padding:10px 12px}
#lineup-app .lite-tray{height:35dvh;box-sizing:border-box;margin:0;border-radius:0}
#lineup-app .lite-tabs{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:6px}
#lineup-app .lite-tabs button{background:#26384d;border:1px solid #486783;border-radius:7px;color:#edf3ff;padding:7px 10px;min-height:32px}
#lineup-app .lite-tabs button.active{background:#1c6a63;border-color:#74dfc4}
#lineup-app .lite-tray-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px;overflow:visible;padding:6px 0 8px;min-height:64px}
#lineup-app .lite-tray-list .player{min-width:0;max-width:100%;min-height:50px;user-select:none}
#lineup-app .lite-picked{outline:2px solid #ffdc7a!important}
#lineup-app .lite-ghost{position:fixed;z-index:10001;pointer-events:none;padding:10px;border-radius:6px;background:#285c73;color:white;max-width:160px}
#lineup-app .slot.over{outline:2px solid #ffdc7a}
@media(max-width:600px){#lineup-app .actions{gap:6px}#lineup-app .actions select{max-width:100%}#lineup-app h3{font-size:12px}#lineup-app .sim-save-controls input,#lineup-app .sim-save-controls select{min-width:0;max-width:100%}#lineup-app .lite-tabs small{font-size:9px}}
"""

LITE_JS = r"""
      let traySide='my',picked=null,trayOpen=false;
      root.querySelectorAll('.lite-tray,.lite-ghost').forEach(n=>n.remove());
      const tray=document.createElement('section');tray.className='lite-tray';
      tray.setAttribute('aria-label','固定球員名單');root.appendChild(tray);
      const trayToggle=document.createElement('button');trayToggle.type='button';trayToggle.className='lite-tray-toggle';
      trayToggle.onclick=()=>{trayOpen=!trayOpen;picked=null;render();};root.querySelector('.board').before(trayToggle);
      function benchLite(side,id){const p=getPlayer(side,id);if(!p||weekDates[dayIndex]<data.today||!canPredict(p,dayIndex)){setMessage("過去與已開賽排陣不可修改。");return;}const pos=location(side,id);if(pos)state[dayIndex][side][pos]=null;picked=null;render();}
      function moveLite(side,id,pos){
        const p=getPlayer(side,id);
        if(!p||!onRoster(p,side)||!canPredict(p,dayIndex)||weekDates[dayIndex]<data.today){setMessage("此球員不在當日名單，或排陣已鎖定。");return;}
        if(!p||!plays(p)){setMessage('這位球員當天沒有出賽，不能排入。');return;}
        if(!eligible(p,pos)){setMessage(`${p.name} 不符合 ${pos} 位置。`);return;}
        const old=location(side,id),occupant=state[dayIndex][side][pos];
        if(old===pos){picked=null;return;}
        if(old)state[dayIndex][side][old]=null;
        state[dayIndex][side][pos]=id;
        if(occupant&&old){const other=getPlayer(side,occupant);if(other&&plays(other)&&eligible(other,old))state[dayIndex][side][old]=occupant;}
        picked=null;render();setMessage(`${p.name} 已排入 ${pos.replace(/[12]$/,'')}。`);
      }
      function liteCard(p,side,inSlot){
        const el=document.createElement('div');
        el.className='player '+(side==='opp'?'opp ':'')+status(p).toLowerCase()+(picked?.id===p.id?' lite-picked':'');
        el.draggable=trayOpen;el.style.touchAction=trayOpen?"none":"pan-y";let dragged=false;
        el.setAttribute('aria-label',`${p.name} ${p.eligible.join('/')} ${inSlot?'查看當天數據':'選取或拖曳排陣'}`);
        el.tabIndex=0;
        if(inSlot){
          const photo=document.createElement('img');photo.className='lite-avatar';photo.alt=p.name;photo.loading='lazy';
          photo.src=p.nba_id?`https://cdn.nba.com/headshots/nba/latest/260x190/${p.nba_id}.png`:'';
          photo.onerror=()=>{photo.hidden=true;};el.appendChild(photo);
        }
        const text=document.createElement('span');text.className='lite-name';
        text.appendChild(document.createTextNode(p.name));
        const pos=document.createElement('small');pos.textContent=p.eligible.join('/')+(inSlot&&isLocked(p,dayIndex)?' 🔒':'');text.appendChild(pos);el.appendChild(text);
        el.ondragstart=e=>{if(!trayOpen){e.preventDefault();return;}dragging={side,id:p.id};e.dataTransfer.setData('text/plain',p.id);};
        el.ondragend=()=>{dragging=null;};
        const choose=()=>{if(inSlot){if(picked?.side===side&&picked.id!==p.id)moveLite(side,picked.id,location(side,p.id));else openEditor(p,side);}else{picked={side,id:p.id};renderTray();setMessage('點選同側的位置格排入；也可以直接拖曳。');}};
        el.onclick=e=>{e.stopPropagation();if(dragged){dragged=false;return;}choose();};
        el.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose();}};
        el.onpointerdown=e=>{
          if(!trayOpen||e.pointerType==='mouse')return;
          const origin=[e.clientX,e.clientY];let ghost=null,moved=false;
          el.setPointerCapture(e.pointerId);
          el.onpointermove=event=>{
            if(Math.hypot(event.clientX-origin[0],event.clientY-origin[1])<8&&!moved)return;
            moved=true;dragged=true;
            if(!ghost){ghost=document.createElement('div');ghost.className='lite-ghost';ghost.textContent=p.name;root.appendChild(ghost);}
            ghost.style.left=event.clientX+'px';ghost.style.top=(event.clientY-45)+'px';
          };
          el.onpointerup=event=>{
            el.onpointermove=null;el.onpointerup=null;ghost?.remove();
            if(!moved)return;
            event.preventDefault();
            const scope=root.getRootNode();
            const target=scope.elementFromPoint(event.clientX,event.clientY);
            const hit=target?.closest('[data-lite-pos]'),bench=target?.closest('[data-lite-bench]');
            if(hit&&hit.dataset.liteSide===side)moveLite(side,p.id,hit.dataset.litePos);
            else if(bench&&bench.dataset.liteBench===side)benchLite(side,p.id);
            else setMessage('拖到同側先發位置或板凳區。');
          };
          el.onpointercancel=()=>{ghost?.remove();el.onpointermove=null;};
        };
        return el;
      }
      function renderTray(){
        tray.hidden=!trayOpen;trayToggle.textContent=trayOpen?'完成調整 · 收起球員':'調整名單 · 展開球員';trayToggle.setAttribute('aria-expanded',String(trayOpen));
        root.classList.toggle('lite-adjusting',trayOpen);
        tray.replaceChildren();
        const tabs=document.createElement('div');tabs.className='lite-tabs';
        for(const [side,label] of [['my','我的球隊'],['opp','對手球隊']]){
          const button=document.createElement('button');button.textContent=label;button.className=side===traySide?'active':'';
          button.onclick=()=>{traySide=side;picked=null;renderTray();};tabs.appendChild(button);
        }
        tray.appendChild(tabs);
        const list=document.createElement('div');list.className='lite-tray-list';
        list.dataset.liteBench=traySide;
        list.ondragover=e=>{e.preventDefault();};
        list.ondrop=e=>{e.preventDefault();if(dragging?.side===traySide)benchLite(traySide,dragging.id);dragging=null;};
        const bench=players[traySide].filter(p=>onRoster(p,traySide)&&!location(traySide,p.id));
        for(const p of bench)list.appendChild(liteCard(p,traySide,false));
        if(!bench.length){const empty=document.createElement('small');empty.textContent='板凳區 · 拖曳球員到這裡';list.appendChild(empty);}
        const heading=document.createElement('small');heading.textContent='板凳 · 拖曳上下場';tabs.appendChild(heading);
        tray.appendChild(list);
      }
"""

def enhance_lite(js):
    js=js.replace('["9-Cat","我的球隊","差距（我方 − 對手）","對手球隊","領先方"]', '["項目","我方","差距","對手","領先"]',1)
    js=js.replace('      function card(p,side,inSlot=false) {', LITE_JS+'\n      function card(p,side,inSlot=false) {\n        return liteCard(p,side,inSlot);',1)
    js=js.replace('            dropTarget(slot,side,pos);', '''            slot.dataset.liteSide=side;slot.dataset.litePos=pos;
            slot.onclick=()=>{if(picked?.side===side)moveLite(side,picked.id,pos);};
            dropTarget(slot,side,pos);''',1)
    js=js.replace('        summary();\n      }','        summary();renderTray();\n      }',1)
    return js
