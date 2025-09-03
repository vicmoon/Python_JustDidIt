//console.log('tracking script loaded');

let activeActivityId = null;
let activeActivityIcon = null;

const activityList = document.querySelector('#activityList');
if (activityList) {
  activityList.addEventListener('click', (e) => {
    const pill = e.target.closest('.activity-pill');
    if (!pill) return;

    //store the selection

    activeActivityId = pill.dataset.id;
    activeActivityIcon = pill.dataset.icon;

    console.log('Selected activity:', activeActivityId, activeActivityIcon);

    // Update UI to reflect selection

    activityList
      .querySelectorAll('.activity-pill')
      .forEach((p) => p.classList.remove('is-selected'));
    pill.classList.add('is-selected');
  });
}

const calendarBoxes = document.querySelectorAll('.calendar-box[data-date]');
//console.log('found boxes:', calendarBoxes.length);

calendarBoxes.forEach((box) => {
  box.addEventListener('click', () => {
    const dateIso = box.dataset.date;

    if (!activeActivityId) {
      alert('Select an activity first :)');
      return;
    }

    // Send data to server

    fetch('/log_activity_day', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        date: dateIso,
        activity_id: Number(activeActivityId),
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        console.log('Server response:', data);
      })

      .catch((err) => console.error('Error logging activity:', err));

    // console.log('Log pair →', {
    //   date: dateIso,
    //   activity_id: Number(activeActivityId),
    // });

    box.classList.toggle('is-selected');
  });
});
