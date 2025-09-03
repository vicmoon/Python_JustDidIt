//console.log('tracking script loaded');

const ICON_BASE = window.ICON_BASE || '/static/icons/';

let activeActivityId = null;
let activeActivityIcon = null;

const activityList = document.querySelector('#activityList');

function clearSelection() {
  activeActivityId = null;
  activeActivityIcon = null;
  if (activityList) {
    activityList
      .querySelectorAll('.activity-pill')
      .forEach((p) => p.classList.remove('is-selected'));
  }
}

if (activityList) {
  activityList.addEventListener('click', (e) => {
    const pill = e.target.closest('.activity-pill');
    if (!pill) return;

    const wasSelected = pill.classList.contains('is-selected');

    // clear all first
    activityList
      .querySelectorAll('.activity-pill')
      .forEach((p) => p.classList.remove('is-selected'));

    if (wasSelected) {
      // clicking the same pill -> deselect
      clearSelection();
      return;
    }

    // select new pill
    pill.classList.add('is-selected');
    activeActivityId = pill.dataset.id; // or Number(pill.dataset.id)
    activeActivityIcon = pill.dataset.icon; // e.g., "book.png"
    console.log('Selected activity:', activeActivityId, activeActivityIcon);
  });
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') clearSelection();
});

/* --- helpers unchanged --- */
function addIconToBox(box, activityId, iconFile) {
  const wrap = box.querySelector('.day-icons');
  if (!wrap) return;
  const existing = wrap.querySelector(`img[data-activity-id="${activityId}"]`);
  if (existing) existing.remove();
  const img = document.createElement('img');
  img.className = 'day-icon';
  img.dataset.activityId = activityId;
  img.alt = 'icon';
  img.src = ICON_BASE + iconFile;
  wrap.appendChild(img);
}

function removeIconFromBox(box, activityId) {
  const wrap = box.querySelector('.day-icons');
  const existing =
    wrap && wrap.querySelector(`img[data-activity-id="${activityId}"]`);
  if (existing) existing.remove();
}

/* --- calendar click handler unchanged --- */
document.querySelectorAll('.calendar-box[data-date]').forEach((box) => {
  box.addEventListener('click', async () => {
    if (!activeActivityId || !activeActivityIcon) {
      alert('Select an activity first 🙂');
      return;
    }
    const dateIso = box.dataset.date;

    try {
      const res = await fetch('/log_activity_day', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date: dateIso,
          activity_id: Number(activeActivityId),
        }),
      });
      const data = await res.json();

      if (!data.ok) {
        console.error('Error logging activity:', data.error || data);
        return;
      }
      if (data.state === 'added') {
        addIconToBox(
          box,
          data.activity_id ?? activeActivityId,
          data.icon ?? activeActivityIcon
        );
      } else if (data.state === 'removed') {
        removeIconFromBox(box, data.activity_id ?? activeActivityId);
      }
      box.classList.toggle('is-selected'); // optional
    } catch (err) {
      console.error('Network/parse error:', err);
    }
  });
});
