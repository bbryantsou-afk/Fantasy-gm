const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('drive_authorization/index.html','utf8'),script=html.split('<script>')[1].split('</script>')[0];
function setup(storage=new Map()){
 const messages=[],ui={children:[],replaceChildren(){this.children=[]},append(x){this.children.push(x)}};
 const parent={postMessage(m){messages.push(m)}};let listener;
 const context={parent,Date,JSON,localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)},window:{addEventListener(_,f){listener=f}},document:{getElementById:()=>ui,createElement:tag=>({tag,addEventListener(_,f){this.click=f}})}};
 vm.runInNewContext(script,context);
 return {messages,ui,storage,render:a=>listener({source:parent,data:{type:'streamlit:render',args:a}}),foreign:a=>listener({source:{},data:{type:'streamlit:render',args:a}}),value:()=>messages.filter(m=>m.type==='streamlit:setComponentValue').at(-1)?.value};
}
let s=setup();s.render({mode:'login',flow:{url:'https://accounts.google.com/o/oauth2/v2/auth',state:'signed-state',verifier:'pkce'}});s.ui.children[0].click({preventDefault(){throw Error('unexpected')}});
assert.equal(JSON.parse(s.storage.get('fgm-drive-pending-v1')).verifier,'pkce');
let callback=setup(s.storage);callback.render({mode:'read',callback:{state:'wrong'}});assert.equal(callback.value().error,'state_mismatch');
callback=setup(s.storage);callback.render({mode:'read',callback:{state:'signed-state'}});assert.equal(callback.value().verifier,'pkce');
callback.render({mode:'save',envelope:'encrypted-token'});assert.equal(s.storage.get('fgm-drive-login-v1'),'encrypted-token');assert(!s.storage.has('fgm-drive-pending-v1'));
let restore=setup(s.storage);restore.render({mode:'read'});assert.equal(restore.value().envelope,'encrypted-token');
restore.render({mode:'logout'});restore.ui.children[0].onclick();assert(!s.storage.has('fgm-drive-login-v1'));assert.equal(restore.value().logout,true);
let other=setup();other.foreign({mode:'save',envelope:'bad'});assert.equal(other.storage.size,0);
console.log('PASS browser-bound PKCE, mismatched callback rejection, encrypted envelope restore, logout removal and parent-source checking');
