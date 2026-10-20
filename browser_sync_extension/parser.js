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

// Read only the public-facing matchup section, never React state or account data.
function parseYahooMatchupWeek(doc,league,week){
  const base='https://basketball.fantasysports.yahoo.com';
  const dates=[];
  for(const a of doc.querySelectorAll('a[href]')){
    const u=new URL(a.getAttribute('href'),base);
    if(u.pathname!==`/nba/${league}/matchup` || Number(u.searchParams.get('week'))!==week)continue;
    const d=u.searchParams.get('date');if(/^\d{4}-\d{2}-\d{2}$/.test(d??''))dates.push(d);
  }
  const days=[...new Set(dates)].sort();
  if(!days.length)throw Error('Yahoo Week '+week+' 尚無可確認日期。');
  const heading=[...doc.querySelectorAll('h2,h3')].find(h=>h.textContent.trim()==='Matchups');
  const section=heading?.parentElement;
  if(!section)return {week,start:days[0],end:days.at(-1),pairs:[]};
  if(!new RegExp('Week\\s+'+week+'\\s+Matchups').test(section.textContent))throw Error('Yahoo 回傳週次不符。');
  const pairs=[],seen=new Set();
  const teamId=a=>new URL(a.getAttribute('href'),base).pathname.match(new RegExp('^/nba/'+league+'/(\\d+)/?$'))?.[1];
  for(const a of section.querySelectorAll('a[href]')){
    if(!teamId(a))continue;
    let node=a.parentElement;
    while(node && node!==section){
      const ids=[...new Set([...node.querySelectorAll('a[href]')].map(teamId).filter(Boolean))];
      if(ids.length===2){
        const key=[...ids].sort().join(':');
        if(!seen.has(key)){seen.add(key);pairs.push(ids);}break;
      }
      if(ids.length>2)break;node=node.parentElement;
    }
  }
  return {week,start:days[0],end:days.at(-1),pairs};
}

async function collectYahooSchedule(read,league,report=()=>{}){
  const first=await read(`/nba/${league}/matchup?week=1&date=totals`);
  const nums=[...new Set([...first.querySelectorAll('select option')].map(o=>Number(new URL(o.getAttribute('value')??'',`https://basketball.fantasysports.yahoo.com/nba/${league}/matchup`).searchParams.get('week'))).filter(n=>n>0&&n<=40))];
  if(!nums.length)throw Error('Yahoo 尚未提供週次清單。');
  const weeks=[],errors=[];
  // Future weeks use Yahoo's server-rendered team schedule; live cards may be client-only.
  const teamLinks=[...new Set([...first.querySelectorAll('a[href]')].map(a=>new URL(a.getAttribute('href'),'https://basketball.fantasysports.yahoo.com').pathname.match(new RegExp('^/nba/'+league+'/(\\d+)/?$'))?.[1]).filter(Boolean))];
  const home=await read(`/nba/${league}/?module=standings&lhst=sched&sctype=team&scmid=${teamLinks[0]??1}`);
  const ids=[...new Set([...home.querySelectorAll('#schedsubnav a[href]')].map(a=>new URL(a.getAttribute('href'),'https://basketball.fantasysports.yahoo.com').searchParams.get('scmid')).filter(Boolean))];
  if(ids.length<2 || ids.length>30)throw Error('無法確認對戰表的全部球隊。');
  const teamWeeks={};let teamCursor=0;
  async function readTeam(){while(teamCursor<ids.length){const id=ids[teamCursor++];
    const doc=await read(`/nba/${league}/?module=standings&lhst=sched&sctype=team&scmid=${id}`);
    teamWeeks[id]=parseYahooTeamSchedule(doc,league);
  }}
  await Promise.all([readTeam(),readTeam()]);
  // Low concurrency: collect the full season once per day, not on every roster check.
  let cursor=0;
  async function worker(){while(cursor<nums.length){const week=nums[cursor++];
    report('讀取 Yahoo 對戰排程 Week '+week+'/'+Math.max(...nums));
    try{
      const w=parseYahooMatchupWeek(await read(`/nba/${league}/matchup?week=${week}&date=totals`),league,week);
      const pairs=[],seen=new Set();
      for(const id of ids){const other=teamWeeks[id][week];
        if(other && teamWeeks[other]?.[week]===id && !seen.has(id) && !seen.has(other)){seen.add(id);seen.add(other);pairs.push([id,other]);}
      }
      w.pairs=pairs;weeks.push(w);
    }
    catch(e){errors.push('Week '+week+'：'+e.message);}
  }}
  await Promise.all([worker(),worker()]);
  if(!weeks.some(w=>w.pairs.length))throw Error('尚未讀到可確認的對戰配對。');
  return {weeks:weeks.sort((a,b)=>a.week-b.week),errors};
}
function parseYahooTeamSchedule(doc,league){
  const table=[...doc.querySelectorAll('table')].find(t=>/\bWk\b/.test(t.textContent)&&/Opponent/.test(t.textContent));
  if(!table)throw Error('未讀到 Yahoo 球隊對戰表。');
  const out={};
  for(const row of table.querySelectorAll('tbody tr')){
    const week=Number(row.cells[0]?.textContent.trim());
    if(!Number.isInteger(week)||week<1||week>40)continue;
    const ids=[...new Set([...row.querySelectorAll('a[href]')].map(a=>new URL(a.getAttribute('href'),'https://basketball.fantasysports.yahoo.com').pathname.match(new RegExp('^/nba/'+league+'/(\\d+)/?$'))?.[1]).filter(Boolean))];
    if(ids.length===1)out[week]=ids[0];
  }
  return out;
}
if(typeof module!=='undefined')Object.assign(module.exports,{parseYahooMatchupWeek,parseYahooTeamSchedule,collectYahooSchedule});
