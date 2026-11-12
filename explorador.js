(()=>{
const tabs=[...document.querySelectorAll('.explorer [role="tab"]')];
const panels=[...document.querySelectorAll('.explorer [role="tabpanel"]')];
if(!tabs.length||tabs.length!==panels.length)return;
function select(index){tabs.forEach((tab,i)=>{tab.setAttribute('aria-selected',String(i===index));tab.tabIndex=i===index?0:-1;panels[i].hidden=i!==index;});}
tabs.forEach((tab,index)=>{
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
select(0);document.querySelector('.explorer [role="tablist"]').hidden=false;
})();
