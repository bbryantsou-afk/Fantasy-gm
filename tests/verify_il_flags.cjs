const assert=require('node:assert/strict');
const {parseYahooDocument}=require('../browser_sync_extension/parser.js');
function fixture(flag){const cell={innerText:'Chet Holmgren\nOKC - PF,C',querySelectorAll:()=>flag?[{textContent:flag}]:[]};const link={href:'https://sports.yahoo.com/nba/players/999',textContent:'Chet Holmgren',closest:()=>cell};const row={cells:[{textContent:'IL'}],querySelectorAll:()=>[link]};const table={textContent:"Team's Players roster for 2026-10-27.",querySelectorAll:()=>[row]};return {querySelectorAll:q=>q==='table'?[table]:[]};}
for(const flag of ['O','Q',''])assert.equal(parseYahooDocument(fixture(flag),'2026-10-27').rows[0].injury_status,flag);
console.log('PASS Yahoo IL slot is independent of injury flag O, Q and healthy');
