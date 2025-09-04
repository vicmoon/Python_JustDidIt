// /static/icons_script.js
(() => {
  // Avoid double init
  if (window.__ICONIFY_MIN_INIT__) return;
  window.__ICONIFY_MIN_INIT__ = true;

  // Wait until DOM parsed (defer should be enough, this is extra-safe)
  document.addEventListener('DOMContentLoaded', () => {
    const iconSearchInput = document.getElementById('iconSearch');
    const iconResultsGrid = document.getElementById('iconResults');
    const iconRefHidden = document.getElementById('iconRef');

    if (!iconSearchInput || !iconResultsGrid || !iconRefHidden) {
      console.warn('[iconify] required elements not found on page');
      return;
    }

    const debounce = (fn, ms = 250) => {
      let t;
      return (...args) => {
        clearTimeout(t);
        t = setTimeout(() => fn(...args), ms);
      };
    };

    async function doSearch(q) {
      const term = (q || '').trim();
      iconResultsGrid.innerHTML = '';
      if (term.length < 2) return;

      const url = `https://api.iconify.design/search?query=${encodeURIComponent(
        term
      )}&limit=48`;
      try {
        const res = await fetch(url);
        if (!res.ok) throw new Error(String(res.status));
        const data = await res.json();
        const icons = data.icons || [];

        if (!icons.length) {
          iconResultsGrid.textContent = 'No results';
          return;
        }

        const frag = document.createDocumentFragment();
        icons.forEach((id) => {
          const [prefix, name] = id.split(':');
          const btn = document.createElement('button');
          btn.type = 'icon-button';
          btn.className = 'icon-choice';
          btn.innerHTML =
            `<img src="https://api.iconify.design/${prefix}/${name}.svg" ` +
            `alt="${id}">`;
          btn.addEventListener('click', () => {
            iconRefHidden.value = id;
            [...iconResultsGrid.children].forEach((el) =>
              el.classList.remove('selected')
            );
            btn.classList.add('selected');
          });
          frag.appendChild(btn);
        });
        iconResultsGrid.appendChild(frag);
      } catch (err) {
        console.error('[iconify] search failed:', err);
        iconResultsGrid.textContent = 'Search failed';
      }
    }

    iconSearchInput.addEventListener(
      'input',
      debounce((e) => doSearch(e.target.value))
    );
    console.log('[iconify] wired');
  });
})();
