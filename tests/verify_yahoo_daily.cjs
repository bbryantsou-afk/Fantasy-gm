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
(async()=>{
 const parts=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
 const v=t=>parts.find(p=>p.type===t).value;const today=v('year')+'-'+v('month')+'-'+v('day');
 let reads=0;const read=async path=>{reads++;const url=new URL(path,'https://basketball.fantasysports.yahoo.com');assert.equal(url.searchParams.get('stat2'),'D');return fixture(url.searchParams.get('date'),url.pathname.split('/')[3]);};
 const first=await collectYahooRosterWeek(read,'7',['1','2'],today);assert.equal(first.primary.date,today);assert.equal(first.primary.teams.length,2);assert(first.history.length<=6);
 reads=0;await collectYahooRosterWeek(read,'7',['1','2'],today,()=>{},first.archives);assert.equal(reads,2); // reread today, reuse settled earlier days
 console.log('PASS Yahoo day-only mode, genuine zero versus no data, date guards, full week collection and fresh-today cache behavior');
})().catch(e=>{console.error(e);process.exit(1)});
