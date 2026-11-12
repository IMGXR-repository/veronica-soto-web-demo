(()=>{
 const section=document.querySelector('#recorrido');if(!section)return;
 // This decision happens before any module request; mobile remains light after rotation.
 const lightweightQuery='(max-width:800px), (pointer:coarse) and (max-height:600px)';
 const mobile=matchMedia(lightweightQuery).matches;
 if(mobile){
  document.documentElement.classList.add('scene-lite');
  section.querySelectorAll('[data-mobile-poster]').forEach(img=>{img.src=img.dataset.mobilePoster});
  return;
 }
 const observer=new IntersectionObserver(async entries=>{
  if(!entries.some(e=>e.isIntersecting))return;
  if(matchMedia(lightweightQuery).matches){observer.disconnect();document.documentElement.classList.add('scene-lite');section.querySelectorAll('[data-mobile-poster]').forEach(img=>{img.src=img.dataset.mobilePoster});return;}
  observer.disconnect();
  try{await import('./app.js')}catch(error){section.classList.add('scene-unavailable');const status=document.querySelector('#loading');if(status)status.textContent='La vista 3D no está disponible en este navegador. Puedes seguir leyendo los artículos.';console.warn('Vista 3D no disponible',error)}
 },{rootMargin:'250px'});observer.observe(section);
})();

