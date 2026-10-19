importScripts('parser.js');
const APP='https://fantasy-gm-bgjfjwjnxx8mbxjvajm2nk.streamlit.app';
let busy=false;
function validLeague(x){return typeof x==='string' && /^\d{1,10}$/.test(x);}
function validDate(x){return typeof x==='string' && /^\d{4}-\d{2}-\d{2}$/.test(x) && !Number.isNaN(Date.parse(x));}
function easternDate(){return new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());}
async function loaded(id){
  const until=Date.now()+45000;
  while(Date.now()<until){const t=await chrome.tabs.get(id);if(t.status==='complete')return;await new Promise(r=>setTimeout(r,400));}
  throw new Error('Yahoo 載入逾時，保留上次成功資料。');
}
async function execute(id,func,args=[]){return (await chrome.scripting.executeScript({target:{tabId:id},func,args}))[0].result;}
async function collect(league,date,report){
  if(busy)throw new Error('已有同步進行中，請稍候。');busy=true;let tab;
  try{
    tab=await chrome.tabs.create({url:`https://basketball.fantasysports.yahoo.com/nba/${league}`,active:false});await loaded(tab.id);
    const discovery=await execute(tab.id,()=>{
      const base=location.pathname.match(/^\/nba\/(\d+)/)?.[1];
      const links=Array.from(new Set(Array.from(document.querySelectorAll('a')).map(a=>a.href).filter(h=>new RegExp('^https://basketball\\.fantasysports\\.yahoo\\.com/nba/'+base+'/\\d+$').test(h))));
      const standings=document.querySelector('table.standingstable')||document.querySelector('table[id*="standings"]');
      return {links,hasLeague:!!document.querySelector('#ybarAccountMenu') && links.length>1};
    });
    if(!discovery.hasLeague || discovery.links.length<2 || discovery.links.length>30)throw new Error('請先在同一個瀏覽器登入 Yahoo 並確認可查看聯盟。');
    const teams=[];
    for(let i=0;i<discovery.links.length;i++){
      report({kind:'progress',message:`正在讀取 ${i+1}/${discovery.links.length} 隊 · ${date}`});
      const url=discovery.links[i];await chrome.tabs.update(tab.id,{url:`${url}/team?date=${date}&stat1=S`});await loaded(tab.id);
      // Inject the parser file, then call it in the same isolated world.
      await chrome.scripting.executeScript({target:{tabId:tab.id},files:['parser.js']});
      const result=await execute(tab.id,d=>{
        try{return {ok:true,value:parseYahooDocument(document,d)};}catch(e){return {ok:false,error:e.message};}
      },[date]);
      if(!result.ok)throw new Error(result.error);
      teams.push({id:url.split('/').pop(),...result.value});
    }
    const ids=teams.flatMap(t=>t.rows.map(r=>r.yahooPlayerId));
    if(new Set(ids).size!==ids.length)throw new Error('不同隊出現重複球員，可能同步時發生交易。請重新同步。');
    const snapshot={schema:1,league,date,capturedAt:new Date().toISOString(),teams};
    const key='league_'+league;const stored=(await chrome.storage.local.get(key))[key]||{};
    stored.snapshots=stored.snapshots||{};stored.snapshots[date]=snapshot;
    // Keep 14 distinct dates; cloud sessions can restore them from this browser.
    for(const old of Object.keys(stored.snapshots).sort().slice(0,-14))delete stored.snapshots[old];
    stored.lastSuccess=snapshot.capturedAt;stored.lastError=null;await chrome.storage.local.set({[key]:stored});
    return {snapshot,mapping:stored.mapping||{},savedDates:Object.keys(stored.snapshots).sort()};
  }finally{busy=false;if(tab)await chrome.tabs.remove(tab.id).catch(()=>{});}
}
chrome.runtime.onConnect.addListener(port=>{
  const origin=port.sender?.origin;let connected=true;
  if(![APP,'http://localhost:8501','http://127.0.0.1:8501'].includes(origin)){port.disconnect();return;}
  port.onDisconnect.addListener(()=>{connected=false;});
  const send=x=>{if(connected)try{port.postMessage(x);}catch{}};
  port.onMessage.addListener(async m=>{
    try{
      if(!validLeague(m.league))throw new Error('聯盟 ID 不符。');
      const key='league_'+m.league;const stored=(await chrome.storage.local.get(key))[key]||{};
      if(m.action==='sync'){
        if(!validDate(m.date))throw new Error('日期不符。');
        send({kind:'result',...(await collect(m.league,m.date,send))});
      }else if(m.action==='cached'){
        if(!validDate(m.date)||!stored.snapshots?.[m.date])throw new Error('此瀏覽器尚未保存這一天，請按同步。');
        send({kind:'result',snapshot:stored.snapshots[m.date],mapping:stored.mapping||{},savedDates:Object.keys(stored.snapshots).sort()});
      }else if(m.action==='mapping'){
        if(!m.mapping || typeof m.mapping!=='object' || Array.isArray(m.mapping) || Object.keys(m.mapping).length>30)throw new Error('隊伍配對格式不符。');
        stored.mapping=m.mapping;await chrome.storage.local.set({[key]:stored});send({kind:'mapped',message:'已在此瀏覽器記住隊伍配對。'});
      }else if(m.action==='schedule'){
        const name='sync_'+m.league;
        if(m.enabled){await chrome.alarms.create(name,{periodInMinutes:30});}else{await chrome.alarms.clear(name);}
        send({kind:'scheduled',message:m.enabled?'已開啟：瀏覽器運作時每 30 分鐘檢查一次。':'已關閉自動檢查。'});
      }else if(m.action==='status'){
        send({kind:'status',savedDates:Object.keys(stored.snapshots||{}).sort(),lastSuccess:stored.lastSuccess,lastError:stored.lastError,auto:!!(await chrome.alarms.get('sync_'+m.league))});
      }
    }catch(e){send({kind:'error',message:e.message||'同步失敗，未更新 App。'});}
  });
});
chrome.alarms.onAlarm.addListener(async alarm=>{
  if(!/^sync_\d+$/.test(alarm.name))return;
  const league=alarm.name.slice(5);
  try{await collect(league,easternDate(),()=>{});}catch(e){const key='league_'+league;const saved=(await chrome.storage.local.get(key))[key]||{};saved.lastError=e.message;await chrome.storage.local.set({[key]:saved});}
});
