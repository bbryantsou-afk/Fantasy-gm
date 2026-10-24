const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync('pwa/web/app.js','utf8'),store=new Map();
const ctx={S:{league:'71585'},PAGES:[['overview'],['sim'],['watch']],sessionStorage:{getItem:k=>store.get(k),setItem:(k,v)=>store.set(k,v)},setDrawer:()=>{},render:()=>{},refreshSimStatus:()=>{},window:{history:{pushState:()=>{}},scrollTo:()=>{}},location:{pathname:'/',search:''},$:()=>({focus:()=>{}})};
vm.createContext(ctx);vm.runInContext(src.slice(src.indexOf('function rememberedPage('),src.indexOf('function rememberedPage('))||'',ctx);
for(const name of ['rememberedPage','navigate']){const start=src.indexOf('function '+name+'('),end=src.indexOf('\n',start);vm.runInContext(src.slice(start,end),ctx);}
assert.equal(ctx.rememberedPage(),'overview');ctx.navigate('sim');assert.equal(ctx.rememberedPage(),'sim');
ctx.S.page='overview';ctx.navigate(ctx.rememberedPage(),{history:false});assert.equal(ctx.S.page,'sim');
ctx.S.league='99';assert.equal(ctx.rememberedPage(),'overview');ctx.S.league='71585';assert.equal(ctx.rememberedPage(),'sim');
ctx.navigate('invalid');assert.equal(ctx.rememberedPage(),'sim');
console.log('PASS refresh restores current page per tab/league; invalid navigation ignored');
