// tracking script

// --- config / csrf ---------------------------------------------------
const CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]')?.content;

async function postJSON(url, payload) {
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': CSRF_TOKEN, // <-- important
    },
    body: JSON.stringify(payload || {}),
  });
  let data = null;
  try {
    data = await res.json();
  } catch (_) {}
  return { ok: res.ok, status: res.status, data };
}

// --- state ------------------------------------------------------------
let activeActivityId = null; // string id from data-id
let activeActivityIcon = null; // icon_ref like "mdi:run"

const activityList = document.querySelector('#activityList');

// --- selection helpers -----------------------------------------------
function clearSelection() {
  activeActivityId = null;
  activeActivityIcon = null;
  if (activityList) {
    activityList
      .querySelectorAll('.activity-pill')
      .forEach((p) => p.classList.remove('is-selected'));
  }
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') clearSelection();
});

// --- DOM helpers (calendar icons) ------------------------------------
function iconUrl(ref) {
  // ref like "mdi:run"
  return `https://api.iconify.design/${ref.replace(':', '/')}.svg`;
}

function addIconToBox(box, activityId, iconRef) {
  const wrap = box.querySelector('.day-icons');
  if (!wrap) return;

  const existing = wrap.querySelector(`img[data-activity-id="${activityId}"]`);
  if (existing) existing.remove();

  const img = document.createElement('img');
  img.className = 'day-icon';
  img.dataset.activityId = activityId;
  img.alt = 'icon';
  img.src = iconUrl(iconRef);
  wrap.appendChild(img);
}

function removeIconFromBox(box, activityId) {
  const wrap = box.querySelector('.day-icons');
  const existing =
    wrap && wrap.querySelector(`img[data-activity-id="${activityId}"]`);
  if (existing) existing.remove();
}

// --- activity list (select + delete) ---------------------------------
if (activityList) {
  activityList.addEventListener('click', async (e) => {
    // 1) Delete clicked?
    const delBtn = e.target.closest('.pill-delete');
    if (delBtn) {
      e.stopPropagation();
      const li = delBtn.closest('.activity-pill');
      if (!li) return;
      const id = li.dataset.id;

      if (!confirm('Delete this activity and all its logged days?')) return;

      // Call JSON delete endpoint: POST /activity/<id>/delete returns {ok: true}
      const { ok, data, status } = await postJSON(`/activity/${id}/delete`);
      if (!ok || !data?.ok) {
        console.error('Delete failed', status, data);
        alert(data?.error || 'Failed to delete activity.');
        return;
      }

      // Remove any icons for this activity from the visible calendar
      document
        .querySelectorAll(`img.day-icon[data-activity-id="${id}"]`)
        .forEach((img) => img.remove());

      // If this pill was selected, clear selection
      if (activeActivityId === id) {
        clearSelection();
      }

      // Remove the pill
      li.remove();
      return;
    }

    // 2) Otherwise: selection click
    const pill = e.target.closest('.activity-pill');
    if (!pill) return;

    const wasSelected = pill.classList.contains('is-selected');

    // clear all first
    activityList
      .querySelectorAll('.activity-pill')
      .forEach((p) => p.classList.remove('is-selected'));

    if (wasSelected) {
      clearSelection();
      return;
    }

    // select new pill
    pill.classList.add('is-selected');
    activeActivityId = pill.dataset.id; // keep as string, server will cast
    activeActivityIcon = pill.dataset.icon; // always icon_ref now (e.g., "mdi:run")
    // console.log('Selected activity:', activeActivityId, activeActivityIcon);
  });
}

// --- calendar click: toggle log --------------------------------------

document.querySelectorAll('.calendar-box[data-date]').forEach((box) => {
  box.addEventListener('click', async () => {
    if (!activeActivityId || !activeActivityIcon) {
      alert('Select an activity first 🙂');
      return;
    }

    const payload = {
      date: box.dataset.date, // "YYYY-MM-DD"
      activity_id: Number(activeActivityId), // server expects int
    };

    const { ok, data, status } = await postJSON('/log_activity_day', payload);

    if (!ok || !data) {
      console.error('Error logging activity', status, data);
      return;
    }
    if (!data.ok) {
      console.error('Server declined logging', data);
      return;
    }

    if (data.state === 'added') {
      const ref = data.icon || activeActivityIcon;
      addIconToBox(box, data.activity_id ?? activeActivityId, ref);
    } else if (data.state === 'removed') {
      removeIconFromBox(box, data.activity_id ?? activeActivityId);
    }

    box.classList.toggle('is-selected');
    drawRoughBox(box);
  });
});

/* --- ROUGH.JS: sketchy borders + fill ------------------------------ */

// small helper
function cssVar(name, fallback) {
  const v = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
  return v || fallback;
}
function debounce(fn, t = 120) {
  let id;
  return (...a) => {
    clearTimeout(id);
    id = setTimeout(() => fn(...a), t);
  };
}
function stableSeed(str) {
  // deterministic per date
  let h = 0;
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) | 0;
  return Math.abs(h);
}

function drawRoughBox(box) {
  // remove previous drawing
  box.querySelector('svg.sketch')?.remove();

  const w = Math.round(box.clientWidth);
  const h = Math.round(box.clientHeight);
  if (!w || !h) return;

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.classList.add('sketch');
  svg.setAttribute('width', w);
  svg.setAttribute('height', h);
  svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
  box.prepend(svg);

  const rc = rough.svg(svg);
  const margin = 6;
  const seed = stableSeed(box.dataset.date || `${Math.random()}`);

  // Rough fill for selected/logged days
  if (box.classList.contains('is-selected')) {
    const fill = rc.rectangle(margin, margin, w - margin * 2, h - margin * 2, {
      seed,
      roughness: 1.2,
      fill: cssVar('--rough-fill', '#9fd3f6'),
      fillStyle: 'solid',
      stroke: 'none',
    });
    svg.appendChild(fill);
  }

  // Wobbly ink border
  const border = rc.rectangle(margin, margin, w - margin * 2, h - margin * 2, {
    seed,
    roughness: 1.8,
    bowing: 2.3,
    stroke: cssVar('--ink', '#1a1a1a'),
    strokeWidth: 2,
  });
  svg.appendChild(border);
}

function drawAllRough() {
  document.querySelectorAll('.calendar-box[data-date]').forEach(drawRoughBox);
}

window.addEventListener('DOMContentLoaded', drawAllRough);
window.addEventListener('resize', debounce(drawAllRough, 150));
