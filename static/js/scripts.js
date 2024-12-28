// Get references to the sidebar and hamburger menu
const sidebar = document.getElementById('sidebar');
const hamburgerMenu = document.getElementById('hamburger-menu');

// Toggle the sidebar on hamburger menu click (for small screens only)
hamburgerMenu.addEventListener('click', function() {
    if (sidebar.style.left === '0px') {
        sidebar.style.left = '-200px'; // Hide the sidebar
    } else {
        sidebar.style.left = '0px'; // Show the sidebar
    }
});
