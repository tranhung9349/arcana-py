/* Native PDF printing: no upload, new window, HTML download or PDF dependency. */
(() => {
  let busy=false;
  function prepare(result, title) {
    document.getElementById('print-snapshot')?.remove();
    const page=document.createElement('main');page.id='print-snapshot';
    const brand=document.createElement('p');brand.className='eyebrow';brand.textContent='ARCANA · KẾT QUẢ PHIÊN';page.appendChild(brand);
    const heading=document.createElement('h1');heading.textContent=title;page.appendChild(heading);
    const time=document.createElement('p');time.className='hint';time.textContent='Xuất lúc '+new Date().toLocaleString('vi-VN',{timeZone:'Asia/Ho_Chi_Minh'});page.appendChild(time);
    const workspace=result.closest('.workspace, .date-workspace');
    const form=workspace?.querySelector('form');
    const content=result.closest('#date-popup')?.querySelector('#date-popup-content') || result;
    const sources=[...(form?[form]:[]),content];
    for(const source of sources) {
      const copy=source.cloneNode(true);
      const originalFields=[...source.querySelectorAll('input,select,textarea')];
      copy.querySelectorAll('input,select,textarea').forEach((field,index)=>{
        const original=originalFields[index], value=document.createElement('span');value.className='print-field-value';
        value.textContent=original.tagName==='SELECT'?original.selectedOptions[0]?.textContent || '':
          ['checkbox','radio'].includes(original.type)?(original.checked?'Có':'Không'):original.value || 'Chưa nhập';
        field.replaceWith(value);
      });
      copy.querySelectorAll('button.date-tile').forEach(node=>{
        const tile=document.createElement('article');tile.className=node.className;
        while(node.firstChild)tile.appendChild(node.firstChild);
        node.replaceWith(tile);
      });
      copy.querySelectorAll('.ai-reading-panel').forEach(node=>{
        if(!node.querySelector('.ai-reading-content')?.children.length)node.remove();
      });
      copy.querySelectorAll('[hidden],button,[data-export-control],script,style,iframe,object,embed,.ai-reading-status,.ai-reading-error,.date-tile-action,.bazi-saved-readings,[role="alert"]').forEach(node=>node.remove());
      copy.querySelectorAll('details').forEach(node=>node.open=true);
      // Copied DOM must not add active content or repeat IDs from the live page.
      for(const node of [copy,...copy.querySelectorAll('*')]) {
        for(const attr of [...node.attributes]) {
          if(!['class','colspan','rowspan','open','lang','aria-label'].includes(attr.name))node.removeAttribute(attr.name);
        }
      }
      page.appendChild(copy);
    }
    document.body.appendChild(page);
    return page;
  }
  function mount(result,title='Kết quả phiên') {
    const existing=result.querySelector('[data-export-control]');
    if(existing){existing.dataset.exportTitle=title;existing.setAttribute('aria-label','Xuất PDF · '+title);return;}
    const button=document.createElement('button');button.type='button';button.className='secondary export-pdf';
    button.textContent='Xuất PDF';button.dataset.exportControl='true';button.setAttribute('aria-label','Xuất PDF · '+title);
    button.dataset.exportTitle=title;
    button.addEventListener('click',async()=>{
      if(busy)return;busy=true;button.disabled=true;
      const oldTitle=document.title;
      const cleanup=()=>{document.body.classList.remove('printing-result');document.getElementById('print-snapshot')?.remove();document.title=oldTitle;busy=false;button.disabled=false;window.removeEventListener('afterprint',cleanup);};
      try {
        await document.fonts?.ready;
        const currentTitle=button.dataset.exportTitle;
        prepare(result,currentTitle);document.title='Arcana - '+currentTitle;document.body.classList.add('printing-result');
        window.addEventListener('afterprint',cleanup,{once:true});window.print();
      } catch {cleanup();}
    });
    result.prepend(button);
  }
  window.ResultPDF={mount,prepare};
})();
