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

      fetch(`/update_activity_color/${selectedActivityId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ activity_color: selectedColor }),
      })
        .then((response) => response.text())
        .then((data) => {
          console.log('Box color updated in database:', data);
        })
        .catch((error) => {
          console.error('Error updating box color:', error);
        });
    } else {
      alert('Please select an activity first.');
    }
  });
});
