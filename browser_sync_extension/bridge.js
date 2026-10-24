// Only the packaged sync component can request work; never access cookies.
(() => {
  const component = () => location.pathname.includes('/component/') && location.pathname.includes('league_sync');
  window.addEventListener('message', event => {
    if (event.source !== window || event.origin !== location.origin || !component()) return;
    const m = event.data;
    if (!m || m.channel !== 'fantasy-gm-sync-v1' || typeof m.requestId !== 'string') return;
    const reply = data => window.postMessage({channel:'fantasy-gm-sync-extension-v1',requestId:m.requestId,...data},location.origin);
    if (m.action === 'hello') { reply({kind:'ready',version:chrome.runtime.getManifest().version}); return; }
    if (!['sync','score','cached','mapping','schedule','status'].includes(m.action)) return;
    const port = chrome.runtime.connect({name:'fantasy-gm-sync'});
    port.onMessage.addListener(reply);
    port.onDisconnect.addListener(() => { const error=chrome.runtime.lastError; if(error) reply({kind:'error',message:'擴充功能連線中斷，請重試。'}); });
    port.postMessage({action:m.action,league:m.league,date:m.date,mapping:m.mapping,enabled:m.enabled});
  });
})();
