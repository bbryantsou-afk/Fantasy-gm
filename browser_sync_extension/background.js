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
    const key='league_'+league;const stored=(await chrome.storage.local.get(key))[key]||{};
    report({kind:'progress',message:'正在讀取當週各日 Fantasy 排陣與單日數據…'});
    await chrome.scripting.executeScript({target:{tabId:tab.id},files:['parser.js']});
    const batch=await execute(tab.id,async(lid,ids,day,cache)=>{
      async function read(path){const r=await fetch(path,{credentials:'same-origin',cache:'no-store',signal:AbortSignal.timeout(15000)});if(!r.ok)throw Error('Yahoo '+r.status);return new DOMParser().parseFromString(await r.text(),'text/html');}
      try{return {ok:true,...await collectYahooRosterWeek(read,lid,ids,day,()=>{},cache)};}catch(e){return {ok:false,error:e.message};}
    },[league,discovery.links.map(u=>u.split('/').pop()),date,stored.dailyArchives||{}]);
    if(!batch.ok)throw Error(batch.error);
    stored.dailyArchives=batch.archives;
    let schedule=stored.matchupSchedule;
    if(!schedule || stored.scheduleDate!==easternDate()){
      try{
        const result=await execute(tab.id,async lid=>{
          async function read(path){const r=await fetch(path,{credentials:'same-origin'});if(!r.ok)throw Error('Yahoo '+r.status);return new DOMParser().parseFromString(await r.text(),'text/html');}
          try{return {ok:true,...await collectYahooSchedule(read,lid)};}catch(e){return {ok:false,error:e.message};}
        },[league]);
        if(result.ok){schedule=result.weeks;stored.matchupSchedule=schedule;stored.scheduleDate=easternDate();}
        else report({kind:'progress',message:'名單已讀取；對戰排程未更新：'+result.error});
      }catch(e){report({kind:'progress',message:'對戰排程未更新：'+e.message});}
    }
    let matchupResults;
    try{
      const result=await execute(tab.id,async(lid,day,weeks)=>{
        async function read(path){const r=await fetch(path,{credentials:'same-origin',cache:'no-store',signal:AbortSignal.timeout(15000)});if(!r.ok)throw Error('Yahoo '+r.status);return new DOMParser().parseFromString(await r.text(),'text/html');}
        try{return {ok:true,results:await collectYahooMatchupResults(read,lid,day,weeks)};}catch(e){return {ok:false,error:e.message};}
      },[league,date,schedule||[]]);
      if(result.ok)matchupResults=result.results;
      else report({kind:'progress',message:'名單已讀取；官方比分未更新：'+result.error});
    }catch(e){report({kind:'progress',message:'官方比分未更新：'+e.message});}
    const snapshot={...batch.primary,history:batch.history,...(schedule?{matchupSchedule:schedule}:{}),...(matchupResults?{matchupResults}:{})};
    stored.snapshots=stored.snapshots||{};
    // Keep daily data once; repeating a full week inside every cached date exceeds Chrome quota.
    const {history:unusedHistory,...dailySnapshot}=snapshot;stored.snapshots[date]=dailySnapshot;
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
        const begin=new Date(m.date+'T12:00:00Z');begin.setUTCDate(begin.getUTCDate()-(begin.getUTCDay()+6)%7);
        const end=new Date(begin);end.setUTCDate(end.getUTCDate()+6);
        const history=Object.entries(stored.dailyArchives||{}).filter(([d])=>d!==m.date&&d>=begin.toISOString().slice(0,10)&&d<=end.toISOString().slice(0,10)).map(([,v])=>v.snapshot);
        send({kind:'result',snapshot:{...stored.snapshots[m.date],...(history.length?{history}:{})},mapping:stored.mapping||{},savedDates:Object.keys(stored.snapshots).sort()});
      }else if(m.action==='mapping'){
        if(!m.mapping || typeof m.mapping!=='object' || Array.isArray(m.mapping) || Object.keys(m.mapping).length>30)throw new Error('隊伍配對格式不符。');
        stored.mapping=m.mapping;await chrome.storage.local.set({[key]:stored});send({kind:'mapped',message:'已在此瀏覽器記住隊伍配對。'});
      }else if(m.action==='schedule'){
        const name='sync_'+m.league;
        if(m.enabled){await chrome.alarms.create(name,{periodInMinutes:5});}else{await chrome.alarms.clear(name);}
        send({kind:'scheduled',message:m.enabled?'已開啟：瀏覽器運作時約每 5 分鐘讀取今日排陣與實績。':'已關閉自動檢查。'});
      }else if(m.action==='status'){
        const alarm=await chrome.alarms.get('sync_'+m.league);
        if(alarm&&alarm.periodInMinutes!==5)await chrome.alarms.create('sync_'+m.league,{periodInMinutes:5});
        send({kind:'status',savedDates:Object.keys(stored.snapshots||{}).sort(),selectedCapturedAt:stored.snapshots?.[m.date]?.capturedAt,lastSuccess:stored.lastSuccess,lastError:stored.lastError,auto:!!(await chrome.alarms.get('sync_'+m.league))});
      }
    }catch(e){send({kind:'error',message:e.message||'同步失敗，未更新 App。'});}
  });
});
chrome.alarms.onAlarm.addListener(async alarm=>{
  if(!/^sync_\d+$/.test(alarm.name))return;
  const league=alarm.name.slice(5);
  try{await collect(league,easternDate(),()=>{});}catch(e){const key='league_'+league;const saved=(await chrome.storage.local.get(key))[key]||{};saved.lastError=e.message;await chrome.storage.local.set({[key]:saved});}
});
