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
