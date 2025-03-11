// Global variable to store the currently selected color.
let selectedColor = null;

// Add click event listeners to each activity item.
document.querySelectorAll('.activity-item').forEach((item) => {
  item.addEventListener('click', () => {
    // When an activity is clicked, set selectedColor to its current color.
    const colorPicker = item.querySelector('.activity-color-picker');
    selectedColor = colorPicker.value;

    // Optional: visually indicate selection.
    document
      .querySelectorAll('.activity-item')
      .forEach((i) => i.classList.remove('selected'));
    item.classList.add('selected');
  });

  // Update the data attribute and selectedColor if the color picker changes.
  item
    .querySelector('.activity-color-picker')
    .addEventListener('change', (e) => {
      item.dataset.activityColor = e.target.value;
      if (item.classList.contains('selected')) {
        selectedColor = e.target.value;
      }
    });
});

// When a calendar box is clicked, mark it with the selected color.
document.querySelectorAll('.calendar-box').forEach((box) => {
  box.addEventListener('click', () => {
    if (selectedColor) {
      box.style.backgroundColor = selectedColor;
    } else {
      alert('Please select an activity first.');
    }
  });
});
