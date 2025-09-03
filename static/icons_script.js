// Choose 1–3 popular collections for speed
const collections = ['mdi', 'tabler', 'material-symbols'];
const cache = {};

async function loadCollection(prefix) {
  if (cache[prefix]) return cache[prefix];
  const res = await fetch(`https://api.iconify.design/${prefix}.json`);
  const data = await res.json();
  const names = Object.keys(data.icons || {});
  cache[prefix] = names;
  return names;
}

async function searchIcons(q) {
  const term = q.toLowerCase().trim();
  if (!term) {
    document.getElementById('iconResults').innerHTML = '';
    return;
  }

  const results = [];
  for (const p of collections) {
    const names = await loadCollection(p);
    for (const n of names) {
      if (n.includes(term)) results.push({ prefix: p, name: n });
      if (results.length >= 60) break;
    }
    if (results.length >= 60) break;
  }
  render(results);
}

function render(list) {
  const wrap = document.getElementById('iconResults');
  wrap.innerHTML = '';
  list.forEach(({ prefix, name }) => {
    const url = `https://api.iconify.design/${prefix}/${name}.svg`;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'icon-choice';
    btn.innerHTML = `<img src="${url}" alt="${name}"><span>${prefix}:${name}</span>`;
    btn.onclick = () => {
      // set hidden input
      document.getElementById('iconRef').value = `${prefix}:${name}`;
      // uncheck local radios so we prefer icon_ref
      document
        .querySelectorAll('input[name="{{ form.icon.name }}"]')
        .forEach((r) => (r.checked = false));
    };
    wrap.appendChild(btn);
  });
}

const searchBox = document.getElementById('iconSearch');
let t;
searchBox.addEventListener('input', (e) => {
  clearTimeout(t);
  t = setTimeout(() => searchIcons(e.target.value), 250);
});
