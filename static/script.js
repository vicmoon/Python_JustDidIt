// Wait until the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function () {
  // Select all elements with the calendar-box class
  const calendarBoxes = document.querySelectorAll('.calendar-box');

  // Add a click event listener to each box
  calendarBoxes.forEach((box) => {
    box.addEventListener('click', function () {
      // Toggle the "crossed" class on click
      box.classList.toggle('crossed');
    });
  });
});
