const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const {parseYahooDocument}=require('../browser_sync_extension/parser.js');
function fixture(date='2026-10-20',name='Jimmy Butler III',id='4912',position='IL'){
 const cell={innerText:name+'Player Note\nGSW - SF,PF'};
 const link={href:'https://sports.yahoo.com/nba/players/'+id,textContent:name,closest:()=>cell};
 const row={cells:[{textContent:position}],querySelectorAll:()=>[link]};
 const table={textContent:"Private Team's Players roster for "+date+'.',querySelectorAll:()=>[row]};
 return {querySelectorAll:q=>q==='table'?[table]:[]};
}
assert.equal(parseYahooDocument(fixture(),'2026-10-20').rows[0].position,'IL');
assert.throws(()=>parseYahooDocument(fixture(),'2026-10-19'),/日期/);
assert.throws(()=>parseYahooDocument({querySelectorAll:()=>[]},'2026-10-20'),/登入/);
const storage={};let url='',closed=0;const listeners=[];
const ctx={console,Date,Intl,setTimeout,URL,chrome:{
 tabs:{create:async o=>{url=o.url;return {id:1}},get:async()=>({status:'complete'}),update:async(id,o)=>{url=o.url},remove:async()=>{closed++}},
 scripting:{executeScript:async o=>{
  if(o.files){vm.runInContext(fs.readFileSync('browser_sync_extension/parser.js','utf8'),ctx);return [];}
  if(o.args?.length===4){return [{result:{ok:true,primary:{schema:1,league:'7',date:'2026-10-20',capturedAt:new Date().toISOString(),teams:['1','2'].map(id=>({id,...ctx.parseYahooDocument(fixture('2026-10-20',id==='1'?'Jimmy Butler III':'Unknown Rookie',id==='1'?'4912':'9999'),'2026-10-20')}))},history:[],archives:{}}}];}
  ctx.location={pathname:new URL(url).pathname};
  if(url.endsWith('/7'))ctx.document={querySelector:()=>({}),querySelectorAll:()=>['1','2'].map(i=>({href:'https://basketball.fantasysports.yahoo.com/nba/7/'+i}))};
  else ctx.document=fixture('2026-10-20',url.includes('/1/')?'Jimmy Butler III':'Unknown Rookie',url.includes('/1/')?'4912':'9999');
  return [{result:vm.runInContext('('+o.func.toString()+')(...'+JSON.stringify(o.args||[])+')',ctx)}];
 }},
 storage:{local:{get:async k=>({[k]:storage[k]}),set:async o=>Object.assign(storage,o)}},
 runtime:{onConnect:{addListener:f=>listeners.push(f)}},alarms:{onAlarm:{addListener:()=>{}},get:async()=>null}
},importScripts:()=>{}};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync('browser_sync_extension/background.js','utf8'),ctx);
(async()=>{
 const r=await vm.runInContext("collect('7','2026-10-20',()=>{})",ctx);
 assert.equal(r.snapshot.teams.length,2);assert.equal(closed,1);assert.ok(storage.league_7.snapshots['2026-10-20']);
 let disconnected=false;listeners[0]({sender:{origin:'https://evil.example'},disconnect:()=>{disconnected=true}});assert.ok(disconnected);
 let messageHandler;const alarms=[];const messages=[];
 ctx.chrome.alarms.get=async()=>({periodInMinutes:1});
 ctx.chrome.alarms.create=async(name,options)=>alarms.push({name,...options});
 ctx.chrome.alarms.clear=async()=>{};
 listeners[0]({sender:{origin:'https://fantasy-gm-bgjfjwjnxx8mbxjvajm2nk.streamlit.app'},onDisconnect:{addListener:()=>{}},onMessage:{addListener:f=>messageHandler=f},postMessage:m=>messages.push(m)});
 await messageHandler({action:'status',league:'7',date:'2026-10-20'});
 assert.equal(alarms.at(-1).periodInMinutes,5); // migrate an existing one-minute alarm
 await messageHandler({action:'schedule',league:'7',enabled:true});
 assert.equal(alarms.at(-1).periodInMinutes,5);
 assert.equal(messages.at(-1).kind,'scheduled');
 console.log('PASS live-DOM-shaped parser, date/login rejection, background collection, private cache, tab cleanup and origin restriction');
})().catch(e=>{console.error(e);process.exit(1)});
