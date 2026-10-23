const fs=require('node:fs'),assert=require('node:assert/strict');
(async()=>{const source=fs.readFileSync('pwa/web/model.js','utf8');const m=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
const my={FGM:5,FGA:10,FTM:4,FTA:5,FG3M:3,PTS:20,REB:8,AST:6,STL:2,BLK:1,TOV:1},opp={...my,TOV:4};
assert.equal(m.compare(my,opp).wins,1);assert.equal(m.compare(my,opp).ties,8);assert.equal(m.value({},'FG'),null);
assert.equal(m.format(1,'FG'),'100%');assert.deepEqual(m.weekDates('2026-10-23'),['2026-10-19','2026-10-20','2026-10-21','2026-10-22','2026-10-23','2026-10-24','2026-10-25']);
const players=[{id:'a',team:'ATL',eligible:['PG'],status:'active'},{id:'b',team:'ATL',eligible:['C'],status:'IL'},{id:'c',team:'BOS',eligible:['SG'],status:'active'}];
const lineup=m.autoLineup(players,'2026-10-23',{ATL:['2026-10-23']});assert.equal(lineup.PG,'a');assert(!Object.values(lineup).includes('b'));assert(!Object.values(lineup).includes('c'));assert.equal(Object.values(lineup).filter(Boolean).length,1);
console.log('PASS PWA nine-category ordering, ratio aggregation, TO direction, seven dates, eligibility and IL exclusion');})();
