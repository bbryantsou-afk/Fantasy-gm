import sys,ast,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from streamlit.testing.v1 import AppTest
from matchup_lite import enhance_lite,LITE_JS
from player_hub import news_tone
assert news_tone('Player cleared to play')[0]=='🟢'
assert news_tone('Player ruled out after injury')[0]=='🔴'
assert news_tone('Player could return after injury')[0]=='⚪'
assert news_tone('Player records career-high in win')[0]=='🟢'
assert news_tone('Player speaks at media day')[0]=='⚪'
a=AppTest.from_file(str(ROOT/'app.py'),default_timeout=40).run()
a.sidebar.radio[0].set_value('Matchup Simulator Lite').run()
assert not a.exception,a.exception
assert len(a.selectbox(key='sim_my_team').options)==14
assert any('Lite' in x.value for x in a.subheader)
a.sidebar.radio[0].set_value('模擬對局 Matchup Simulator').run()
assert not a.exception,a.exception
assert any('Matchup Simulator' in x.value for x in a.title)
source=(ROOT/'matchup_simulator_v15.py').read_text();tree=ast.parse(source)
js=next(n.value.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='JS' for x in n.targets))
node='/Users/zoupeien/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
with tempfile.TemporaryDirectory() as temp:
 path=Path(temp)/'lite.mjs';path.write_text(enhance_lite(js))
 subprocess.run([node,'--check',str(path)],check=True)
 move=LITE_JS[LITE_JS.index('      function moveLite'):LITE_JS.index('      function liteCard')]
 test="""
const assert=require('node:assert/strict');
const ps=[{id:'c',name:'Center',eligible:['C']},{id:'g',name:'Guard',eligible:['PG']}];
let state=[{my:{C1:null,PG:null,UTIL1:'c'}}],dayIndex=0,picked={id:'c'},renders=0;
const getPlayer=(side,id)=>ps.find(p=>p.id===id);
const plays=p=>true;
const eligible=(p,pos)=>pos==='UTIL1'||p.eligible.includes(pos==='C1'?'C':pos);
const location=(side,id)=>Object.keys(state[0][side]).find(k=>state[0][side][k]===id);
const setMessage=()=>{};const render=()=>renders++;
"""+move+"""
moveLite('my','c','PG');assert.equal(state[0].my.PG,null);assert.equal(renders,0);
moveLite('my','c','C1');assert.equal(state[0].my.C1,'c');assert.equal(state[0].my.UTIL1,null);
assert.equal(picked,null);assert.equal(renders,1);
moveLite('my','g','C1');assert.equal(state[0].my.C1,'c');
console.log('PASS Lite placement and eligibility');
"""
 subprocess.run([node,'-e',test],check=True)
print('PASS Lite entry, original entry, JavaScript and headline signals')
