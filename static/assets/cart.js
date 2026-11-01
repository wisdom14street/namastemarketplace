/* Namaste Marketplace wholesale order builder (cartkit pattern). The order lives in this browser's localStorage.
   Quantities move in whole case packs. Checkout hands the order to namastebookshop.com as a cart permalink
   (/cart/V:Q,...?storefront=true&attributes[Storefront]=...), where the approved buyer signs in and Shopify's
   B2B catalog sets the real price. */
(function(){
  const C=window.NM_CART;if(!C)return;
  const $=(s,r)=>(r||document).querySelector(s),$$=(s,r)=>[...(r||document).querySelectorAll(s)];
  const money=v=>'$'+Number(v).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
  const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const ga=(n,p)=>{try{if(typeof window.gtag==='function')window.gtag('event',n,p)}catch(_){}};
  const gaItem=(x,q)=>({item_id:String(x.sku||x.v),item_name:x.t+(x.vt?' - '+x.vt:''),item_variant:x.vt||undefined,item_category:x.c||undefined,price:+x.p,quantity:q});
  const KEY='nm_order_v1',MAXC=50;
  let items=load();
  function load(){try{const a=JSON.parse(localStorage.getItem(KEY)||'[]');return Array.isArray(a)?a.filter(x=>x&&x.v&&x.cases>0&&x.min>0):[]}catch(e){return[]}}
  function save(){try{localStorage.setItem(KEY,JSON.stringify(items))}catch(e){}paint()}
  window.addEventListener('storage',e=>{if(e.key===KEY){items=load();paint()}});
  const units=x=>x.cases*x.min;
  const tot=()=>items.reduce((a,x)=>({cases:a.cases+x.cases,units:a.units+units(x),sub:a.sub+units(x)*x.p,msrp:a.msrp+units(x)*x.msrp}),{cases:0,units:0,sub:0,msrp:0});
  function url(){
    if(!items.length)return'';
    const parts=items.map(x=>x.v+':'+units(x));
    return C.shop+'/cart/'+parts.join(',')+'?storefront=true&attributes%5BStorefront%5D='+encodeURIComponent(C.domain)+'&attributes%5BOrder%20type%5D=Wholesale'
      +'&note='+encodeURIComponent('Wholesale order built on '+C.brand+' ('+C.domain+')')+'&ref='+encodeURIComponent(C.domain);
  }
  function add(d,cases){
    let x=items.find(y=>y.v===String(d.v));
    if(x)x.cases=Math.min(MAXC,x.cases+cases);
    else{x={v:String(d.v),h:d.h,t:d.t,vt:d.vt||'',sku:d.sku||'',p:+d.p,msrp:+d.msrp,min:+d.min,i:d.i||'',c:d.c||'',cases:Math.min(MAXC,cases)};items.push(x)}
    save();ga('add_to_cart',{currency:'USD',value:+(x.p*x.min*cases).toFixed(2),items:[gaItem(x,x.min*cases)]});
  }
  // ---------- drawer ----------
  const drawer=$('#cart'),dim=$('.cdim');
  function rowHtml(x){
    const title=x.t+(x.vt?' – '+x.vt:'');
    return `<li class="ci" data-v="${esc(x.v)}">${x.i?`<img src="${esc(x.i)}&width=140" alt="" width="64" height="64" loading="lazy">`:'<span></span>'}
<div class="cim"><b class="cit">${esc(title)}</b><span class="cisku">${x.sku?'Item '+esc(x.sku)+' &middot; ':''}${money(x.p)}/unit &middot; case of ${x.min}</span>
<div class="cq"><button type="button" data-cdec aria-label="One case fewer of ${esc(title)}">&minus;</button><span><b>${x.cases}</b> case${x.cases===1?'':'s'} <small>${units(x)} units</small></span><button type="button" data-cinc aria-label="One case more of ${esc(title)}"${x.cases>=MAXC?' disabled':''}>+</button><button type="button" class="crm" data-crm>Remove</button></div></div>
<b class="cil">${money(units(x)*x.p)}</b></li>`;
  }
  function html(){
    if(!items.length)return `<div class="cempty"><p>No cases added yet.</p><a class="btn" href="/line/" data-cart-close>Open the line sheet</a></div>${notes()}`;
    const t=tot(),pct=Math.min(100,t.sub/C.min*100),left=C.min-t.sub;
    return `<ul class="clist">${items.map(rowHtml).join('')}</ul>
<div class="csum"><div class="crow"><span>Cases</span><b>${t.cases}</b></div><div class="crow"><span>Units</span><b>${t.units}</b></div>
<div class="crow big"><span>Wholesale subtotal (est.)</span><b>${money(t.sub)}</b></div><div class="crow"><span>Suggested retail value</span><b>${money(t.msrp)}</b></div><div class="crow"><span>Your margin at MSRP</span><b>${money(t.msrp-t.sub)}</b></div>
<div class="prog" role="progressbar" aria-valuemin="0" aria-valuemax="${C.min}" aria-valuenow="${Math.round(t.sub)}" aria-label="Progress to the opening order minimum"><span style="width:${pct.toFixed(1)}%"></span></div>
<p class="small">${left>0?`<b>${money(left)}</b> more to reach the $${C.min} opening order. Reorders only need full cases.`:`Opening order minimum of $${C.min} reached.`}</p></div>
<div class="cnote"><b>Sign in with your approved account at checkout; prices are confirmed there.</b><span>Continue to checkout moves these cases to the namastebookshop.com cart. Sign in with your approved email and Shopify applies your wholesale price list, case minimums and tax status. Shipping and any tax are shown at checkout.</span><span class="tip">Best order of steps: sign in first (link below), then tap Continue, so the cart opens with your wholesale prices. If it still shows retail prices, call 212-645-0141 and we will check your account.</span></div>
<a class="btn ccheck" href="${esc(url())}" rel="nofollow" data-checkout>Continue to checkout</a>
<p class="calt"><a href="${esc(C.login)}" target="_blank" rel="noopener" data-ev="sign_in">Sign in first (opens namastebookshop.com)</a></p>${notes()}`;
  }
  function notes(){return `<p class="capply">Not approved yet? You can build an order, but it will be priced at retail until your account is approved. <a href="/apply/">Apply for a wholesale account</a>.</p>`}
  function fill(){const b=$('[data-cart-body]',drawer);if(b)b.innerHTML=html()}
  function paint(){const n=tot().cases;$$('[data-cart-count]').forEach(b=>{b.textContent=n>99?'99+':n;b.hidden=!n});if(drawer&&drawer.classList.contains('open'))fill()}
  let lastFocus=null;
  function open(){if(!drawer)return;lastFocus=document.activeElement;fill();drawer.classList.add('open');drawer.setAttribute('aria-hidden','false');drawer.inert=false;dim.hidden=false;document.body.classList.add('noscroll');const x=$('.x',drawer);x&&x.focus();
    const t=tot();if(items.length)ga('view_cart',{currency:'USD',value:+t.sub.toFixed(2),items:items.map(x=>gaItem(x,units(x)))})}
  function close(){if(!drawer)return;drawer.classList.remove('open');drawer.setAttribute('aria-hidden','true');drawer.inert=true;dim.hidden=true;document.body.classList.remove('noscroll');lastFocus&&lastFocus.focus&&lastFocus.focus()}
  window.NM_OPEN=open;
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&drawer&&drawer.classList.contains('open'))close()});
  // ---------- product cards ----------
  function syncBuy(b){const n=+b.dataset.cases||1,m=+b.dataset.min;$('[data-cases]',b).textContent=n;$('[data-pl]',b).textContent=n===1?'':'s';$('[data-units]',b).textContent=(n*m)+' units';$('[data-dn]',b).disabled=n<=1;$('[data-up]',b).disabled=n>=MAXC}
  $$('.buy').forEach(b=>{b.dataset.cases=1;syncBuy(b)});
  function setVariant(card,idx){
    const vs=JSON.parse(card.dataset.vs),v=vs[idx];if(!v)return;
    const set=(s,t)=>$$(s,card).forEach(e=>{if(!e.classList.contains('buy'))e.textContent=t});
    set('[data-ws]',money(v.ws));set('[data-msrp]',money(v.msrp));set('[data-pack]',v.min);set('[data-casep]',money(v.ws*v.min));set('[data-earn]',money(v.msrp-v.ws));set('[data-mk]',(v.msrp/v.ws).toFixed(2)+'x');set('[data-sku]',v.sku);
    $$('.buy',card).forEach(b=>{Object.assign(b.dataset,{v:v.v,vt:v.vt==='Default Title'?'':v.vt,sku:v.sku,p:v.ws.toFixed(2),msrp:v.msrp.toFixed(2),min:v.min,cases:1});syncBuy(b);const a=$('[data-add]',b);a.disabled=!v.avail;a.textContent=v.avail?'Add to order':'Restocking'});
    $$('[data-vsel]',card).forEach(s=>s.value=idx);
  }
  document.addEventListener('change',e=>{const s=e.target.closest('[data-vsel]');if(s)setVariant(s.closest('.card'),+s.value)});
  document.addEventListener('click',e=>{
    const t=e.target;
    if(t.closest('[data-cart-open]')){e.preventDefault();open();return}
    if(t.closest('[data-cart-close]')&&!t.closest('[data-checkout]')){if(t.closest('a[href]')&&t.closest('a').getAttribute('href')!=='#'){close();return}e.preventDefault();close();return}
    const b=t.closest('.buy');
    if(b){
      if(t.closest('[data-up]')){b.dataset.cases=Math.min(MAXC,(+b.dataset.cases||1)+1);syncBuy(b);return}
      if(t.closest('[data-dn]')){b.dataset.cases=Math.max(1,(+b.dataset.cases||1)-1);syncBuy(b);return}
      if(t.closest('[data-add]')){const n=+b.dataset.cases||1;add(b.dataset,n);const a=$('[data-add]',b);a.textContent='Added ✓';setTimeout(()=>{a.textContent='Add to order'},1600);b.dataset.cases=1;syncBuy(b);open();return}
    }
    const li=t.closest('.ci');
    if(li){const x=items.find(y=>y.v===li.dataset.v);if(!x)return;
      if(t.closest('[data-cinc]')){x.cases=Math.min(MAXC,x.cases+1);save();ga('add_to_cart',{currency:'USD',value:+(x.p*x.min).toFixed(2),items:[gaItem(x,x.min)]});return}
      if(t.closest('[data-cdec]')){if(x.cases>1)x.cases--;else items=items.filter(y=>y!==x);save();ga('remove_from_cart',{currency:'USD',value:+(x.p*x.min).toFixed(2),items:[gaItem(x,x.min)]});return}
      if(t.closest('[data-crm]')){items=items.filter(y=>y!==x);save();ga('remove_from_cart',{currency:'USD',value:+(x.p*units(x)).toFixed(2),items:[gaItem(x,units(x))]});return}
    }
    const co=t.closest('[data-checkout]');
    if(co){const u=url();if(!u){e.preventDefault();return}co.href=u;const tt=tot();
      ga('begin_checkout',{currency:'USD',value:+tt.sub.toFixed(2),items:items.map(x=>gaItem(x,units(x))),transport_type:'beacon'});return}
    const d=t.closest('[data-detail]');
    if(d){const card=d.closest('.card'),dlg=$('#detail');if(!card||!dlg)return;
      const b2=$('.buy',card),bd=b2.dataset,img=bd.i,vs=JSON.parse(card.dataset.vs),v=vs.find(z=>z.v===bd.v)||vs[0];
      $('[data-dbody]',dlg).innerHTML=`${img?`<img src="${esc(img)}&width=720" alt="${esc(bd.t)}" width="720" height="720">`:''}<p class="sku">Item ${esc(v.sku)}</p><h3>${esc(bd.t)}${bd.vt?' – '+esc(bd.vt):''}</h3>
<table class="ls mini"><tbody><tr><th>Wholesale</th><td class="n"><b>${money(v.ws)}</b> / unit</td></tr><tr><th>Case pack</th><td class="n">${v.min} units</td></tr><tr><th>Case price</th><td class="n">${money(v.ws*v.min)}</td></tr><tr><th>MSRP</th><td class="n">${money(v.msrp)}</td></tr><tr><th>You earn</th><td class="n">${money(v.msrp-v.ws)} / unit (${(v.msrp/v.ws).toFixed(2)}x)</td></tr></tbody></table>
<p class="small muted">Retail product page: <a href="${esc(C.shop)}/products/${esc(bd.h)}" target="_blank" rel="noopener">namastebookshop.com</a></p>`;
      dlg.showModal?dlg.showModal():dlg.setAttribute('open','');
      ga('view_item',{currency:'USD',value:v.ws,items:[gaItem({v:v.v,sku:v.sku,t:bd.t,vt:bd.vt,c:bd.c,p:v.ws},1)]});return}
  });
  // ---------- filters and view toggle ----------
  $$('.chip').forEach(c=>c.addEventListener('click',()=>{const f=c.dataset.f;$$('.chip').forEach(x=>x.classList.toggle('on',x===c));$$('[data-pane] .card').forEach(el=>{el.hidden=!(f==='all'||el.dataset.cat===f)});history.replaceState(null,'',f==='all'?location.pathname:'#'+f)}));
  const h=location.hash.slice(1);if(h){const c=$(`.chip[data-f="${CSS.escape(h)}"]`);c&&c.click()}
  $$('.vbtn').forEach(b=>b.addEventListener('click',()=>{const v=b.dataset.view;$$('.vbtn').forEach(x=>x.classList.toggle('on',x===b));$$('[data-pane]').forEach(p=>p.hidden=p.dataset.pane!==v);try{localStorage.setItem('nm_view',v)}catch(_){}}));
  try{const v=localStorage.getItem('nm_view');if(v&&window.matchMedia('(min-width:980px)').matches){const b=$(`.vbtn[data-view="${v}"]`);b&&b.click()}}catch(_){}
  if($('[data-pane]'))ga('view_item_list',{item_list_name:'wholesale_line',items:$$('[data-pane="cards"] .buy').slice(0,50).map(b=>gaItem(b.dataset,+b.dataset.min))});
  paint();
  if(location.hash==='#order')open();
})();
