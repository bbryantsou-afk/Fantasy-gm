// This function is also executed in Yahoo tabs. Keep it self-contained.
function parseYahooDocument(doc, expectedDate) {
  const tables=Array.from(doc.querySelectorAll('table'));
  const table=tables.find(t=>/Players roster for \d{4}-\d{2}-\d{2}/.test(t.textContent));
  if (!table) throw new Error('沒有讀到 Yahoo 陣容。請先登入 Yahoo；若有驗證畫面，請自行完成。');
  const found=table.textContent.match(/Players roster for (\d{4}-\d{2}-\d{2})/)[1];
  if (found!==expectedDate) throw new Error('Yahoo 回傳日期不符，已停止同步。');
  const rows=[];let slots=0;
  for(const tr of table.querySelectorAll('tr')) {
    const cells=Array.from(tr.cells);const pos=cells[0]?.textContent.trim();
    if(!['PG','SG','G','SF','PF','F','C','Util','UTIL','BN','IL','IL+','IR','IR+'].includes(pos)) continue;
    slots++;
    const link=Array.from(tr.querySelectorAll('a')).find(a=>/^https:\/\/sports.yahoo.com\/nba\/players\/\d+\/?$/.test(a.href));
    if(!link){if(!tr.textContent.includes('(Empty)'))throw new Error('球員欄位無法辨識。');continue;}
    const name=link.textContent.trim();const id=link.href.match(/players\/(\d+)/)[1];
    const cell=link.closest('td');const text=cell.innerText||cell.textContent;
    const nba=text.match(/\b([A-Z]{2,3})\s*-\s*((?:PG|SG|SF|PF|C)(?:,(?:PG|SG|SF|PF|C))*)/);
    if(!name || !nba)throw new Error('無法辨識球員位置／NBA 隊伍。');
    rows.push({yahooPlayerId:id,name,position:pos,eligible:nba[2].split(','),nbaTeam:nba[1]});
  }
  if(!slots || !rows.length || new Set(rows.map(r=>r.yahooPlayerId)).size!==rows.length)throw new Error('名單不完整或有重複球員，未套用。');
  const name=table.textContent.match(/([^\n]+)'s Players roster for/)[1].trim();
  return {date:found,name,rows,slots};
}
if(typeof module!=='undefined')module.exports={parseYahooDocument};
