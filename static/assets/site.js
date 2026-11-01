(function(){
  function ga(n,p){try{if(typeof window.gtag==='function')window.gtag('event',n,p||{})}catch(_){}}
  document.addEventListener('click',function(e){try{
    var a=e.target.closest&&e.target.closest('a[href]');if(!a)return;var h=a.getAttribute('href')||'';
    if(a.dataset.ev==='sign_in')ga('generate_lead',{link_type:'sign_in',link_url:h.slice(0,200),transport_type:'beacon'});
    else if(/\/apply\/?$/.test(h))ga('generate_lead',{link_type:'apply_click',link_url:h,transport_type:'beacon'});
    else if(/namastebookshop\.com\/products\//.test(h))ga('select_item',{item_list_name:'wholesale_line',items:[{item_id:h.split('/products/')[1]}],transport_type:'beacon'});
  }catch(_){}},true);
  var f=document.getElementById('applyForm');
  if(f)f.addEventListener('submit',function(){var t=f.querySelector('[name="contact[Business type]"]');ga('generate_lead',{link_type:'wholesale_application',business_type:t?t.value:'',transport_type:'beacon'})});
})();
// line sheet: search, sort, empty state; product page gallery
(function(){
  var $=function(s,r){return (r||document).querySelector(s)},$$=function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))};
  var q=$('#mq'),so=$('#msort'),none=$('#mnone');
  function cur(){var c=$('.chip.on');return c?c.dataset.f:'all'}
  function apply(){
    var t=(q&&q.value||'').trim().toLowerCase(),f=cur(),shown=0;
    $$('[data-pane] .card').forEach(function(el){var ok=(f==='all'||el.dataset.cat===f)&&(!t||(el.dataset.t||'').indexOf(t)>-1||(el.dataset.vs||'').toLowerCase().indexOf(t)>-1);el.hidden=!ok;if(ok&&el.closest('[data-pane="cards"]'))shown++});
    if(none)none.hidden=shown>0;
  }
  function sort(){
    var m=so&&so.value;[$('[data-pane="cards"]'),$('[data-pane="sheet"] tbody')].forEach(function(box){if(!box)return;
      var els=$$('.card',box);els.forEach(function(e,i){if(!e.dataset.o)e.dataset.o=i});
      els.sort(function(a,b){if(!m)return a.dataset.o-b.dataset.o;if(m==='lo')return a.dataset.ws-b.dataset.ws;if(m==='hi')return b.dataset.ws-a.dataset.ws;if(m==='mk')return b.dataset.mk-a.dataset.mk;return a.dataset.t<b.dataset.t?-1:1});
      els.sort(function(a,b){return (b.dataset.av|0)-(a.dataset.av|0)});
      els.forEach(function(e){box.appendChild(e)});});
  }
  if(q)q.addEventListener('input',apply);
  if(so)so.addEventListener('change',sort);
  $$('.chip').forEach(function(c){c.addEventListener('click',function(){setTimeout(apply,0)})});
  if(q||so)setTimeout(apply,0);
  var gi=$('#gimg');
  if(gi)$$('.gth').forEach(function(b){b.addEventListener('click',function(){var u=b.dataset.g;gi.removeAttribute('srcset');gi.src=u+'&width=1200';$$('.gth').forEach(function(x){x.classList.toggle('on',x===b)})})});
})();
