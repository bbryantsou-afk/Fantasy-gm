const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
(async()=>{
 const source=fs.readFileSync('pwa/web/app.js','utf8'),one=name=>source.split('\n').find(l=>l.startsWith('function '+name+'('));
 let sent,scrolls=0;const rows=[{id:'a',name:'A'},{id:'a',name:'A'}];
 const league={teams:{mine:rows,other:[]},matchup_schedule:{weeks:[{start:'2026-10-26',end:'2026-11-01',opponents:{mine:'other',other:'mine'}}]}};
 const controls={'#planner-research':{checked:false},'#planner-remaining':{value:'2'},'#planner-analysis':{scrollIntoView:()=>scrolls++}};
 const context={Map,Set,Array,String,JSON,Number,Date,Error,console,PORTRAITS:{darrynpeterson:'1643408'},S:{team:'mine',payload:{files:{'league_rosters.json':league}},sim:{},page:'planner'},league:()=>league,roster:()=>rows,pkey:p=>String(p.id),plannerStart:'2026-10-27',plannerDrops:['a','a'],plannerResearch:false,plannerRemaining:2,plannerBusy:false,plannerTrayOpen:true,plannerResult:null,render:()=>{},today:()=> '2026-10-27',weekDates:()=>['2026-10-26'],opponent:()=> 'other',$:s=>controls[s],api:async(path,request)=>{sent=request.body;return {sequences:[]};},document:{querySelectorAll:()=>{throw Error('obsolete checkbox lookup');}}};
 vm.createContext(context);vm.runInContext(one('uniqueRoster'),context);
 vm.runInContext(source.slice(source.indexOf('async function action('),source.indexOf('\nfunction safeURL(')),context);
 await context.action({dataset:{action:'planner-analyze'}});
 assert.deepEqual(Array.from(sent.drops),['a']);assert.equal(sent.remaining,2);assert.equal(context.plannerDrops.length,1);assert.equal(context.plannerTrayOpen,false);assert.equal(scrolls,1);
 assert.equal(context.uniqueRoster(rows).length,1);
 const aliases=[{id:null,name:'Darryn Peterson',status:'IL'},{id:'1643408',name:'Darryn Peterson',status:'IL'}];
 const distinct=context.uniqueRoster(aliases);assert.equal(distinct.length,1);assert.equal(distinct[0].id,'1643408');assert.equal(aliases[0].id,null);
 const renderer=source.slice(source.indexOf('function plannerPage()'),source.indexOf('\nfunction tradePage'));
 assert(renderer.indexOf("html+=section('整週補強流程'")<renderer.indexOf("html+=section('優先補強球隊'"));
 console.log('PASS actual planning click retains tile selection, deduplicates IDs/names, leaves source unchanged, closes tray and reveals named recommendations before supporting tables');
})();
