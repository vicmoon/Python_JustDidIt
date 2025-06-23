// Global variables to store the currently selected color and activity ID.
let selectedColor = null;
let selectedActivityId = null;

// Add click event listeners to each activity item.
document.querySelectorAll('.activity-item').forEach((item) => {
  item.addEventListener('click', () => {
    const colorPicker = item.querySelector('.activity-color-picker');
    selectedColor = colorPicker.value;
    // Save the selected activity id
    selectedActivityId = item.dataset.activityId;

    // Visually indicate selection.
    document
      .querySelectorAll('.activity-item')
      .forEach((i) => i.classList.remove('selected'));
    item.classList.add('selected');
  });

  // Update the data attribute and selectedColor if the color picker changes.
  item
    .querySelector('.activity-color-picker')
    .addEventListener('change', (e) => {
      const newColor = e.target.value;
      item.dataset.activityColor = newColor;
      if (item.classList.contains('selected')) {
        selectedColor = newColor;
      }

      fetch(`/update_activity_color/${item.dataset.activityId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ activity_color: newColor }),
      })
        .then((response) => response.text())
        .then((data) => {
          console.log('Color updated successfully:', data);
        })
        .catch((error) => {
          console.error('Error updating the color', error);
        });
    });
});

// When a calendar box is clicked, mark it with the selected color.
document.querySelectorAll('.calendar-box').forEach((box) => {
  box.addEventListener('click', () => {
    if (selectedColor && selectedActivityId) {
      box.style.backgroundColor = selectedColor;

      // Infer the date from the box and surrounding month/year
      const day = box.innerText;
      const monthName = box.closest('ul').previousElementSibling.innerText;
      const month = new Date(`${monthName} 1, 2000`).getMonth() + 1; // Convert name to month index
      const year = new Date().getFullYear(); // You can improve this if you show other years

      const formattedDate = `${year}-${month
        .toString()
        .padStart(2, '0')}-${day.padStart(2, '0')}`;

      fetch('/log_activity_day', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          activity_id: selectedActivityId,
          date: formattedDate,
        }),
      })
        .then((res) => res.text())
        .then((data) => {
          console.log(data); // Optional
        })
        .catch((error) => console.error('Error logging activity day:', error));
    } else {
      alert('Please select an activity first.');
    }
  });
});

document.addEventListener('DOMContentLoaded', () => {
  if (!loggedDays || !Array.isArray(loggedDays)) return;

  loggedDays.forEach((log) => {
    const date = log.date;
    const activityId = log.activity_id;
    const color = log.activity?.color || '#ccc'; // fallback color

    // Find matching calendar box
    const box = document.querySelector(`.calendar-box[data-date="${date}"]`);
    if (box) {
      box.style.backgroundColor = color;
      box.classList.add(`activity-${activityId}`);
    }
  });
});
