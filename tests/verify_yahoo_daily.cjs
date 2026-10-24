const assert=require('node:assert/strict');
const {parseYahooDocument,collectYahooRosterWeek}=require('../browser_sync_extension/parser.js');
function fixture(day,id='1',values=null,selected=true){
 const keys=['Pos','Players','FGM/A*','FTM/A*','3PTM','PTS','REB','AST','ST','BLK','TO'];
 const data=values??['C','Player','0/0','-/-','0','0','0','0','0','0','0'];
 const link={href:'https://sports.yahoo.com/nba/players/'+id,textContent:'Player '+id,closest:()=>({innerText:'Player '+id+'\nSAS - C',querySelector:()=>({textContent:'Q1 1:00'})})};
 const row={cells:data.map(textContent=>({textContent})),querySelectorAll:()=>[link]};
 const header={cells:keys.map(textContent=>({textContent}))};
 const table={textContent:"Team's Players roster for "+day,querySelectorAll:q=>q==='thead tr'?[header]:[row]};
 return {querySelectorAll:q=>q==='table'?[table]:q==='li.Selected a[href]'&&selected?[{getAttribute:()=>'/nba/7/1?stat1=S&stat2=D'}]:[]};
}
const zero=parseYahooDocument(fixture('2026-10-20'),'2026-10-20',true);
assert.equal(zero.rows[0].daily_stats.PTS,0);assert.equal(zero.rows[0].daily_stats.FTA,0);assert.equal(zero.statsScope,'day');
const empty=['C','Player','-/-','-/-','-','-','-','-','-','-','-'];
assert.equal(parseYahooDocument(fixture('2026-10-20','1',empty),'2026-10-20',true).rows[0].daily_stats,null);
assert.throws(()=>parseYahooDocument(fixture('2026-10-20','1',null,false),'2026-10-20',true),/單日/);
assert.throws(()=>parseYahooDocument(fixture('2026-10-20'),'2026-10-21',true),/日期/);
const partial=['C','Player','3/7','3/3','0','9','8','-','1','0','1'];
const partialRow=parseYahooDocument(fixture('2026-10-20','1',partial),'2026-10-20',true).rows[0];
assert.equal(partialRow.daily_stats.AST,0);assert.equal(partialRow.yahooPlayerId,'1');
const malformed=[...partial];malformed[7]='unavailable';assert.equal(parseYahooDocument(fixture('2026-10-20','1',malformed),'2026-10-20',true).rows[0].daily_stats,null);
// Real Yahoo layout: Iron Will / Anthony Edwards, 2026-10-23.
function ironFixture(actionSpan){
 const headers=['Pos','Players','Action','Opp','Pre-Season','% Start','% Ros','MIN*','FGM/A*','FG%','FTM/A*','FT%','3PTM','PTS','REB','AST','ST','BLK','TO',''];
 const values=['PG','Anthony Edwards',...Array(actionSpan).fill('button'),'@ORL','9','99%','100%','33','5/23','.217','3/4','.750','2','15','4','4','4','0','2',''];
 const link={href:'https://sports.yahoo.com/nba/players/6355',textContent:'Anthony Edwards',closest:()=>({innerText:'Anthony Edwards MIN - PG,SG',querySelector:()=>null})};
 const row={cells:values.map(textContent=>({textContent})),querySelectorAll:()=>[link]};
 const header={cells:headers.map(textContent=>({textContent,colSpan:textContent==='Action'?actionSpan:1}))};
 const table={textContent:"鐵的意志's Players roster for 2026-10-23",querySelectorAll:q=>q==='thead tr'?[header]:[row]};
 return {querySelectorAll:q=>q==='table'?[table]:q==='li.Selected a[href]'?[{getAttribute:()=>'/nba/71585/9?stat1=S&stat2=D'}]:[]};
}
const other=parseYahooDocument(ironFixture(2),'2026-10-23',true).rows[0];
const own=parseYahooDocument(ironFixture(1),'2026-10-23',true).rows[0];
assert.deepEqual(other.daily_stats,{PTS:15,FG3M:2,REB:4,AST:4,STL:4,BLK:0,TOV:2,FGM:5,FGA:23,FTM:3,FTA:4});
assert.deepEqual(own.daily_stats,other.daily_stats);
console.log('PASS Iron Will real Yahoo row; own/other layouts yield identical correct statistics');
// Other-team Yahoo page exposes only Stats (no selected Daily link).
const dailyDoc=ironFixture(2);const originalQuery=dailyDoc.querySelectorAll;
dailyDoc.querySelectorAll=q=>q==='li.Selected a[href]'?[{getAttribute:()=>'/nba/71585/9?date=2026-10-23&stat1=S'}]:originalQuery(q);
assert.equal(parseYahooDocument(dailyDoc,'2026-10-23',true,'https://basketball.fantasysports.yahoo.com/nba/71585/9/team?date=2026-10-23&stat1=S&stat2=D').rows[0].daily_stats.PTS,15);
assert.throws(()=>parseYahooDocument(dailyDoc,'2026-10-23',true,'https://basketball.fantasysports.yahoo.com/nba/71585/9/team?date=2026-10-23&stat1=S&stat2=S'),/單日/);
console.log('PASS other-team Stats-only navigation with validated daily response URL');
(async()=>{
 const parts=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
 const v=t=>parts.find(p=>p.type===t).value;const today=v('year')+'-'+v('month')+'-'+v('day');
 let reads=0;const read=async path=>{reads++;const url=new URL(path,'https://basketball.fantasysports.yahoo.com');assert.equal(url.searchParams.get('stat2'),'D');return fixture(url.searchParams.get('date'),url.pathname.split('/')[3]);};
 const first=await collectYahooRosterWeek(read,'7',['1','2'],today);assert.equal(first.primary.date,today);assert.equal(first.primary.teams.length,2);assert(first.history.length<=6);
 reads=0;await collectYahooRosterWeek(read,'7',['1','2'],today,()=>{},first.archives);assert.equal(reads,2); // reread today, reuse only corrected-parser archives
 const stale=structuredClone(first.archives);for(const a of Object.values(stale))delete a.parserVersion;reads=0;await collectYahooRosterWeek(read,'7',['1','2'],today,()=>{},stale);if(first.history.length)assert(reads>2,'old misaligned history must be refetched');
 reads=0;await collectYahooRosterWeek(read,'7',['1','2'],today,()=>{},first.archives,true);assert.equal(reads,(first.history.length+1)*2,'manual sync rereads every day including pregame archives');
 await assert.rejects(()=>collectYahooRosterWeek(async()=>{throw Error('bad response');},'7',['1','2'],today,()=>{},{},true),/排陣未更新/);
 console.log('PASS Yahoo day-only mode, genuine zero versus no data, date guards, full week collection and fresh-today cache behavior');
})().catch(e=>{console.error(e);process.exit(1)});
