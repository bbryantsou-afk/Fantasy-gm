const fs=require('fs'),vm=require('vm'),assert=require('assert');
const code=fs.readFileSync('browser_records/index.html','utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
const storage=new Map();
function page(){let fn;const messages=[];const parent={postMessage:m=>messages.push(m)};const ctx={parent,window:{addEventListener:(e,f)=>fn=f},document:{getElementById:()=>({textContent:''})},localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v)},JSON};vm.runInNewContext(code,ctx);return {messages,send:a=>fn({source:parent,data:{type:'streamlit:render',args:a}})};}
const a=page();a.send({mode:'write',enabled:false,snapshot:{schema:1,files:{seed:true}}});assert.equal(storage.size,0);
const snapshot={schema:1,files:{'league_results.json':{weeks:{},days:{}}},prefs:{}};
a.send({mode:'write',enabled:true,snapshot});
const b=page();b.send({mode:'read'});const m=b.messages.find(x=>x.type==='streamlit:setComponentValue');assert.deepEqual(m.value.snapshot,snapshot);
console.log('PASS no write before hydration, persistent browser storage and independent-page reload recovery');
