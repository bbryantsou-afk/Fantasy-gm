const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const script=fs.readFileSync('sync_bridge/index.html','utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
function setup(){
 const messages=[],timers=[],nodes={};let handler,n=0;
 const parent={postMessage:m=>messages.push(m)};
 const window={parent,addEventListener:(type,fn)=>handler=fn,postMessage:m=>messages.push(m)};
 const document={body:{style:{}},visibilityState:'visible',querySelector:s=>nodes[s]??=( {style:{},textContent:'',disabled:true} ),querySelectorAll:()=>[]};
 vm.runInNewContext(script,{window,document,location:{origin:'https://example.test'},crypto:{randomUUID:()=>String(++n)},setInterval:()=>{},setTimeout:fn=>timers.push(fn)});
 return {messages,render(args){handler({source:parent,data:{type:'streamlit:render',args}})},ready(){handler({source:window,origin:'https://example.test',data:{channel:'fantasy-gm-sync-extension-v1',kind:'ready'}})},timers};
}
const a=setup();a.render({league:'71585',date:'2026-10-23',force:'click-1'});a.ready();
assert.equal(a.messages.filter(m=>m.action==='sync').length,1);
a.render({league:'71585',date:'2026-10-23',force:'click-1'});
assert.equal(a.messages.filter(m=>m.action==='sync').length,1,'Rerender must not duplicate a running sync');
const b=setup();b.render({league:'71585',date:'2026-10-23',force:'phone-click'});b.timers.forEach(fn=>fn());
assert(b.messages.some(m=>m.value?.syncUnavailable&&m.value.force==='phone-click'),'Missing extension must report unavailable, not success');
console.log('PASS force request runs once and unconnected phone reports unavailable');
