(async()=>{
  const APP=__APP_URL__;
  if(location.hostname!=='basketball.fantasysports.yahoo.com')return alert('請先在 Safari／Chrome 開啟並登入 Yahoo Fantasy 籃球聯盟，再點此同步書籤。');
  const league=location.pathname.match(/^\/nba\/(\d+)/)?.[1];
  if(!league)return alert('請先開啟 Yahoo Fantasy 籃球聯盟頁。');
  if(document.getElementById('fgm-phone-sync'))return;
  const panel=document.createElement('div');panel.id='fgm-phone-sync';panel.style.cssText='position:fixed;z-index:2147483647;inset:12px 12px auto;padding:18px;background:#fff;color:#172b3a;border:2px solid #277a65;border-radius:12px;font:16px system-ui;box-shadow:0 5px 30px #0004';document.body.append(panel);
  function status(message){panel.textContent='Fantasy GM 手機同步：'+message;}
  try{
    __PARSER__
    const parts=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
    const part=t=>parts.find(x=>x.type===t).value;const today=part('year')+'-'+part('month')+'-'+part('day');
    panel.textContent='選擇要同步的日期（會讀取所屬整週已發生的排陣與數據）';
    const picker=document.createElement('input');picker.type='date';picker.value=today;picker.max=today;picker.style.cssText='display:block;margin:12px 0;padding:10px;font:inherit';panel.append(picker);
    const go=document.createElement('button');go.textContent='同步這一週';go.style.cssText='padding:10px;font:inherit';panel.append(go);
    const day=await new Promise(resolve=>go.onclick=()=>resolve(picker.value));
    async function read(path){const r=await fetch(path,{credentials:'same-origin',cache:'no-store'});if(!r.ok)throw Error('Yahoo 回傳 '+r.status+'，請確認登入。');return new DOMParser().parseFromString(await r.text(),'text/html');}
    status('讀取聯盟隊伍，請保持頁面開啟…');
    const home=await read('/nba/'+league);
    const ids=[...new Set([...home.querySelectorAll('a[href]')].map(a=>new URL(a.getAttribute('href'),location.origin).pathname.match(new RegExp('^/nba/'+league+'/(\\d+)(?:/team)?/?$'))?.[1]).filter(Boolean))];
    if(ids.length<2 || ids.length>30)throw Error('沒有取得完整聯盟隊伍；請確認登入及聯盟頁面。');
    let archives={};const archiveKey='fantasy-gm-yahoo-daily:'+league;
    try{archives=JSON.parse(localStorage.getItem(archiveKey)||'{}');}catch{}
    const batch=await collectYahooRosterWeek(read,league,ids,day,status,archives,true);
    try{localStorage.setItem(archiveKey,JSON.stringify(batch.archives));}catch{}
    let schedule;
    try{
      const cacheKey='fantasy-gm-yahoo-schedule:'+league;
      let cached;try{cached=JSON.parse(localStorage.getItem(cacheKey)||'null');}catch{}
      if(cached?.day===day)schedule=cached.weeks;
      else{
        const result=await collectYahooSchedule(read,league,status);schedule=result.weeks;
        try{localStorage.setItem(cacheKey,JSON.stringify({day,weeks:schedule}));}catch{}
      }
    }catch(e){status('名單已讀取；對戰表暫未更新：'+e.message);}
    let matchupResults;
    try{matchupResults=await collectYahooMatchupResults(read,league,day,schedule,status);}
    catch(e){status('名單已讀取；官方比分未更新：'+e.message);}
    const snapshot={...batch.primary,history:batch.history,...(schedule?{matchupSchedule:schedule}:{}),...(matchupResults?{matchupResults}:{})};
    let bytes=new TextEncoder().encode(JSON.stringify(snapshot));let prefix='#yahoo-roster=';
    if(typeof CompressionStream!=='undefined'){
      bytes=new Uint8Array(await new Response(new Blob([bytes]).stream().pipeThrough(new CompressionStream('gzip'))).arrayBuffer());prefix='#yahoo-roster-gzip=';
    }
    const payload=btoa(Array.from(bytes,b=>String.fromCharCode(b)).join(''));
    status('已取得 '+snapshot.teams.length+' 隊當週每日排陣與數據，返回 App 驗證…');
    location.assign(APP+prefix+payload);
  }catch(e){status('未同步：'+e.message);const close=document.createElement('button');close.textContent='關閉';close.style.cssText='display:block;margin-top:12px;padding:10px';close.onclick=()=>panel.remove();panel.append(close);}
})();
