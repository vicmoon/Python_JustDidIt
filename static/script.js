<script>
let activeActivityId = null;
let activeActivityIcon = null;


{/* 1) Pick an activity from the pills */}
document.querySelectorAll('#activityList .activity-pill').forEach(li => {
  li.addEventListener('click', () => {
    activeActivityId = li.dataset.id;
    activeActivityIcon = li.dataset.icon;       // e.g. "book.png"

    // visual state
    document.querySelectorAll('#activityList .activity-pill')
      .forEach(x => x.classList.remove('selected'));
    li.classList.add('selected');
  });
});

// helper: add/remove icon in a day cell
function addIcon(box, activityId, iconFile) {
  const wrap = box.querySelector('.day-icons');
  if (!wrap) return;

  // avoid duplicate for same activity
  const existing = wrap.querySelector(`img[data-activity-id="${activityId}"]`);
  if (existing) existing.remove();

  const img = document.createElement('img');
  img.className = 'day-icon';
  img.alt = '';
  img.dataset.activityId = activityId;
  img.src = "{{ url_for('static', filename='icons/') }}" + iconFile;
  wrap.appendChild(img);
}

function removeIcon(box, activityId) {
  const wrap = box.querySelector('.day-icons');
  if (!wrap) return;
  const existing = wrap.querySelector(`img[data-activity-id="${activityId}"]`);
  if (existing) existing.remove();
}

// 2) Click a calendar cell to toggle a log
document.querySelectorAll('.calendar-box[data-date]').forEach(box => {
  box.addEventListener('click', async () => {
    if (!activeActivityId || !activeActivityIcon) {
      alert('Pick an activity first.');
      return;
    }
    const dateIso = box.dataset.date;

    // POST to your endpoint; JSON is easiest (you can keep x-www-form-urlencoded if you prefer)
    const res = await fetch("{{ url_for('log_activity_day') }}", {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }, // add CSRF header if you use it
      body: JSON.stringify({ activity_id: Number(activeActivityId), date: dateIso })
    });

    // Expect JSON: { ok: true, state: "added"|"removed", icon: "file.png" }
    const data = await res.json();
    if (!data.ok) { console.error(data); return; }

    if (data.state === 'added') {
      addIcon(box, activeActivityId, data.icon || activeActivityIcon);
    } else if (data.state === 'removed') {
      removeIcon(box, activeActivityId);
    }
  });
});

// Optional: paint from `loggedDays` if you prefer client-side initial render
// loggedDays = [{date:"YYYY-MM-DD", activity_id:1, icon:"book.png"}, ...]
if (Array.isArray(window.loggedDays)) {
  window.loggedDays.forEach(log => {
    const box = document.querySelector(`.calendar-box[data-date="${log.date}"]`);
    if (box) addIcon(box, log.activity_id, log.icon);
  });
}
</script>
