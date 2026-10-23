const fs=require('node:fs'),assert=require('node:assert/strict');
const source=fs.readFileSync('compact_ui.py','utf8');
const block=source.match(/const hideAttribution=\(\)=>\{([\s\S]*?)\n  \};/)[1];
const node=(protectedContent=false)=>({hidden:false,querySelector:()=>protectedContent?{}:null,style:{setProperty(k,v){this.owner.hidden=v==='none';}}});
const badge=node(),appFrameContainer=node(true),mainContainer=node(true);
for(const n of [badge,appFrameContainer,mainContainer])n.style.owner=n;
const shell={body:node(),documentElement:node(),querySelectorAll(selector){assert(!selector.includes('a,span,p,footer'));return [badge,appFrameContainer,mainContainer,this.body,this.documentElement];}};
new Function('shell',block)(shell);
assert(badge.hidden,'Explicit badge is hidden');
for(const n of [appFrameContainer,mainContainer,shell.body,shell.documentElement])assert(!n.hidden,'App shell must remain visible');
// Reproduce the removed bug: a short attribution next to an iframe has a short
// textContent because the iframe document is not included in parent textContent.
const oldParent={textContent:'Hosted with Streamlit',style:{setProperty(){this.hidden=true;}}};
const label={textContent:'Hosted with Streamlit',closest:()=>null,parentElement:oldParent};
const group=label.closest('footer')||label.parentElement;
if(group.textContent.length<400)group.style.setProperty('display','none','important');
assert(oldParent.style.hidden,'Old heuristic can hide a container enclosing the app iframe');
console.log('PASS reproduced old parent-hide bug; new badge cleanup protects iframe, main, body and root');
