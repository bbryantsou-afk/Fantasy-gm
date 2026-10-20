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
    const part=t=>parts.find(x=>x.type===t).value;const day=part('year')+'-'+part('month')+'-'+part('day');
    async function read(path){const r=await fetch(path,{credentials:'same-origin'});if(!r.ok)throw Error('Yahoo 回傳 '+r.status+'，請確認登入。');return new DOMParser().parseFromString(await r.text(),'text/html');}
    status('讀取聯盟隊伍，請保持頁面開啟…');
    const home=await read('/nba/'+league);
    const ids=[...new Set([...home.querySelectorAll('a[href]')].map(a=>new URL(a.getAttribute('href'),location.origin).pathname.match(new RegExp('^/nba/'+league+'/(\\d+)(?:/team)?/?$'))?.[1]).filter(Boolean))];
    if(ids.length<2 || ids.length>30)throw Error('沒有取得完整聯盟隊伍；請確認登入及聯盟頁面。');
    const teams=[];
    for(const [i,id] of ids.entries()){
      status('讀取 '+(i+1)+'/'+ids.length+' 隊 · '+day+'，請勿離開頁面…');
      const doc=await read('/nba/'+league+'/'+id+'/team?date='+day+'&stat1=S');
      teams.push({id,...parseYahooDocument(doc,day)});
    }
    const players=teams.flatMap(t=>t.rows.map(p=>p.yahooPlayerId));
    if(new Set(players).size!==players.length)throw Error('不同隊伍出現同一球員，可能正好有交易，請稍後重試。');
    const snapshot={schema:1,league,date:day,capturedAt:new Date().toISOString(),teams};
    const bytes=new TextEncoder().encode(JSON.stringify(snapshot));
    const payload=btoa(Array.from(bytes,b=>String.fromCharCode(b)).join(''));
    status('已取得 '+teams.length+' 隊、'+players.length+' 人，返回 App 驗證…');
    location.assign(APP+'#yahoo-roster='+payload);
  }catch(e){status('未同步：'+e.message);const close=document.createElement('button');close.textContent='關閉';close.style.cssText='display:block;margin-top:12px;padding:10px';close.onclick=()=>panel.remove();panel.append(close);}
})();
