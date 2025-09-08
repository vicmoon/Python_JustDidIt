// tracking script

// --- config / csrf ---------------------------------------------------
const CSRF_TOKEN =
  document.querySelector('meta[name="csrf-token"]')?.content || '';

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
    const dateIso = box.dataset.date;

    const { ok, data, status } = await postJSON('/log_activity_day', {
      date: dateIso,
      activity_id: Number(activeActivityId), // server expects int
    });

    if (!ok || !data) {
      console.error('Error logging activity', status, data);
      return;
    }
    if (!data.ok) {
      console.error('Server declined logging', data);
      return;
    }

    if (data.state === 'added') {
      // Prefer server-provided icon (icon_ref); fallback to selected
      const ref = data.icon || activeActivityIcon;
      addIconToBox(box, data.activity_id ?? activeActivityId, ref);
    } else if (data.state === 'removed') {
      removeIconFromBox(box, data.activity_id ?? activeActivityId);
    }

    box.classList.toggle('is-selected'); // optional visual feedback
  });
});
