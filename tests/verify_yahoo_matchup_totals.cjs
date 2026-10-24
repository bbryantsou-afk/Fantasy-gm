const assert=require('node:assert/strict');
const {parseYahooMatchupTotals,collectYahooMatchupResults}=require('../browser_sync_extension/parser.js');
function fixture(a=['40/100','.400','36/45','.800','6','122','74','40','12','17','19'],b=['72/148','.486','20/29','.690','26','190','75','39','16','7','22']){
 const headers=['Team','FGM/A*','FG%','FTM/A*','FT%','3PTM','PTS','REB','AST','ST','BLK','TO',''];
 const rows=[a,b].map((v,i)=>({cells:['team',...v,String(i===0?5:4)].map(textContent=>({textContent})),querySelectorAll:()=>[{getAttribute:()=>'/nba/7/'+(i+1)}]}));
 const table={querySelectorAll:q=>q==='thead th'?headers.map(textContent=>({textContent})):rows};
 return {querySelector:()=>table,querySelectorAll:q=>q==='a[href]'?['2026-10-20','2026-10-25'].map(d=>({getAttribute:()=>`/nba/7/matchup?week=1&date=${d}`})):[]};
}
const out=parseYahooMatchupTotals(fixture(),'7',['1','2']);
assert.equal(out[0].score,5);assert.equal(out[1].score,4);assert.equal(out[0].totals.PTS,122);assert.equal(out[0].totals.FGM,40);assert.equal(out[1].totals.FTA,29);assert.equal(out[0].opponent,'2');
assert.throws(()=>parseYahooMatchupTotals(fixture(),'7',['1','9']),/隊伍不符/);
assert.throws(()=>parseYahooMatchupTotals({querySelector:()=>null},'7',['1','2']),/未載入/);
assert.throws(()=>parseYahooMatchupTotals(fixture(['-/-','.000','0/0','.000','0','0','0','0','0','0','0']),'7',['1','2']),/命中/);
(async()=>{
 const schedule=[{week:1,start:'2026-10-20',end:'2026-10-25',pairs:[['1','2']]}];
 const data=await collectYahooMatchupResults(async url=>{assert(url.includes('date=totals'));return fixture();},'7','2026-10-22',schedule);
 assert.equal(data.teams.length,2);assert.equal(data.week,1);
 console.log('PASS Yahoo official totals, exact team matching, shot volume, incomplete-data rejection and collection');
})().catch(e=>{console.error(e);process.exitCode=1});
