(()=>{
const entries=[
 {title:'Dolor de hombro',excerpt:'Saber cuál es la causa cambia el tratamiento.',links:[['dolor-de-hombro.html','Dolor de hombro'],['calcificacion-hombro.html','Calcificación de hombro'],['hombro-congelado.html','Hombro congelado']]},
 {title:'Lesiones deportivas',excerpt:'la epicondilitis es un problema del tendón que se inserta en la parte de fuera del codo. Duele al coger peso, al apretar o al girar la muñeca.',links:[['epicondilitis.html','Epicondilitis'],['fascitis-plantar.html','Fascitis plantar']]},
 {title:'Dolor persistente',excerpt:'El dolor crónico es el que dura o se repite más de tres meses.',links:[['dolor-agudo-y-cronico.html','Dolor agudo y crónico'],['ciatica.html','Ciática'],['nervio-atrapado.html','Nervio atrapado']]},
 {title:'Después de una cirugía',excerpt:'después de una cirugía (abdominoplastia, liposucción, cirugía de mama, hernia o cualquier otra) puede acumularse líquido o sangre bajo la piel.',links:[['seroma-tras-cirugia.html','Seroma tras cirugía']]}
];
const tabs=[...document.querySelectorAll('[role="tab"]')];
const panel=document.querySelector('#area-panel');
const ids=['area-hombro','area-deporte','area-dolor','area-cirugia'];
function select(index){
 const entry=entries[index];
 tabs.forEach((tab,i)=>{tab.setAttribute('aria-selected',String(i===index));tab.tabIndex=i===index?0:-1});
 panel.setAttribute('aria-labelledby',ids[index]);
 document.querySelector('#area-title').textContent=entry.title;
 document.querySelector('#area-text').textContent=entry.excerpt;
 const list=panel.querySelector('.article-links');list.replaceChildren();
 entry.links.forEach(([href,label])=>{const row=document.createElement('li');const link=document.createElement('a');link.href=href;link.textContent=label+' ↗';row.append(link);list.append(row)});
}
tabs.forEach((tab,index)=>{
 tab.id=ids[index];tab.setAttribute('aria-controls','area-panel');tab.tabIndex=index? -1:0;
 tab.addEventListener('click',()=>select(index));
 tab.addEventListener('keydown',event=>{
  let next=index;
  if(['ArrowDown','ArrowRight'].includes(event.key))next=(index+1)%tabs.length;
  else if(['ArrowUp','ArrowLeft'].includes(event.key))next=(index+tabs.length-1)%tabs.length;
  else if(event.key==='Home')next=0;
  else if(event.key==='End')next=tabs.length-1;
  else return;
  event.preventDefault();select(next);tabs[next].focus();
 });
});
panel.setAttribute('aria-labelledby',ids[0]);
})();
