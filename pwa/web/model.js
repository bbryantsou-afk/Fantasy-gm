export const CATS=['FG','FT','FG3M','PTS','REB','AST','STL','BLK','TOV'];
export const LABELS=['FG%','FT%','3PT','PTS','REB','AST','ST','BLK','TO'];
export const KEYS=['FGM','FGA','FTM','FTA','FG3M','PTS','REB','AST','STL','BLK','TOV'];
export const SLOTS=['PG','SG','G','SF','PF','F','C1','C2','UTIL1','UTIL2'];
export const empty=()=>Object.fromEntries(KEYS.map(k=>[k,0]));
export function stats(r){if(!r)return null;return Object.fromEntries(KEYS.map(k=>[k,Number(r[k]??(k==='FG3M'?r['3PM']:k==='TOV'?r.TO:undefined)??0)]));}
export function total(rows){const out=empty();for(const r of rows.filter(Boolean))for(const k of KEYS)out[k]+=Number(r[k]||0);return out;}
export function value(s,cat){return cat==='FG'?(s.FGA?s.FGM/s.FGA:null):cat==='FT'?(s.FTA?s.FTM/s.FTA:null):s[cat]??null;}
export function format(v,cat){if(v==null||!Number.isFinite(Number(v)))return '—';return ['FG','FT'].includes(cat)?(Number(v)*100).toFixed(1).replace(/\.0$/,'')+'%':Number(v).toFixed(1).replace(/\.0$/,'');}
export function compare(a,b){let wins=0,losses=0,ties=0;const rows=CATS.map(cat=>{const x=value(a,cat),y=value(b,cat);let result=x==null||y==null?null:Math.abs(x-y)<1e-9?0:(x-y)*(cat==='TOV'?-1:1)>0?1:-1;if(result===1)wins++;if(result===-1)losses++;if(result===0)ties++;return {cat,a:x,b:y,result};});return {wins,losses,ties,rows};}
export function today(){return new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());}
export function weekDates(day){const d=new Date(day+'T12:00:00Z');d.setUTCDate(d.getUTCDate()-((d.getUTCDay()+6)%7));return Array.from({length:7},(_,i)=>{const a=new Date(d);a.setUTCDate(a.getUTCDate()+i);return a.toISOString().slice(0,10);});}
export function eligible(p,slot){const e=p.eligible||[];if(slot.startsWith('UTIL'))return true;if(slot==='G')return e.some(x=>['PG','SG'].includes(x));if(slot==='F')return e.some(x=>['SF','PF'].includes(x));return e.includes(slot.startsWith('C')?'C':slot);}
export function autoLineup(players,day,schedule){const used=new Set(),out={};for(const slot of SLOTS){const p=players.find(p=>p.status!=='IL'&&!used.has(p.id)&&eligible(p,slot)&&(schedule[p.team]||[]).includes(day));out[slot]=p?.id??null;if(p)used.add(p.id);}return out;}
export function nameKey(v){return String(v).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]/g,'').replace(/(jr|sr|iii|ii|iv)$/,'');}
export function baseline(players){return Object.fromEntries(CATS.map(cat=>{const vs=players.filter(p=>p.GP>=10).map(p=>value(p,cat)).filter(v=>v!=null);const mean=vs.reduce((a,b)=>a+b,0)/Math.max(1,vs.length);const std=Math.sqrt(vs.reduce((a,b)=>a+(b-mean)**2,0)/Math.max(1,vs.length));return [cat,{mean,std:std||1}];}));}
export function zscore(p,base,weights={}){return CATS.reduce((sum,c)=>{const v=value(p,c);return sum+(v==null?0:(v-base[c].mean)/base[c].std)*(c==='TOV'?-1:1)*(weights[c]??1);},0);}
export function closeWeights(a,b){return Object.fromEntries(CATS.map(c=>{const x=value(a,c),y=value(b,c);return [c,x==null||y==null?0:Math.exp(-Math.abs(x-y)/Math.max(Math.abs(x),Math.abs(y),.1)*7)];}));}

// Prefer the newest validated official weekly snapshot; never mix opponents.
export function officialWeekScore(league,saved,team,day){
 const key=weekDates(day)[0];
 const candidates=[league.yahoo_matchups?.[key],saved?.weeks?.[key]].filter(w=>w?.source==='Yahoo 官方對局總表'&&w.start<=day&&w.end>=day).sort((a,b)=>String(b.updated_at||'').localeCompare(String(a.updated_at||'')));
 for(const w of candidates){const a=w.teams?.[team],other=a?.opponent,b=w.teams?.[other];if(!Number.isInteger(a?.score)||!Number.isInteger(b?.score)||a.score<0||b.score<0||a.score+b.score>9||b.opponent!==team)continue;return {wins:a.score,losses:b.score,opponent:other,stamp:w.updated_at||''};}
 return null;
}
