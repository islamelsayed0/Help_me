// Dark Mode Toggle Functionality

document.addEventListener('DOMContentLoaded', function() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    const sunIcon = document.getElementById('sunIcon');
    const moonIcon = document.getElementById('moonIcon');
    const html = document.documentElement;
    
    // Check localStorage for dark mode preference
    const darkModePreference = localStorage.getItem('darkMode');
    const isDarkMode = darkModePreference === null ? true : darkModePreference === 'true';
    
    // Set initial state
    if (isDarkMode) {
        html.classList.add('dark');
        sunIcon.classList.add('hidden');
        moonIcon.classList.remove('hidden');
    } else {
        html.classList.remove('dark');
        sunIcon.classList.remove('hidden');
        moonIcon.classList.add('hidden');
    }
    
    // Toggle dark mode
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function() {
            const isCurrentlyDark = html.classList.contains('dark');
            
            if (isCurrentlyDark) {
                html.classList.remove('dark');
                sunIcon.classList.remove('hidden');
                moonIcon.classList.add('hidden');
                localStorage.setItem('darkMode', 'false');
            } else {
                html.classList.add('dark');
                sunIcon.classList.add('hidden');
                moonIcon.classList.remove('hidden');
                localStorage.setItem('darkMode', 'true');
            }
            
            // Update user preference in database (via AJAX if user is logged in)
            // This will be implemented when we have API endpoints
        });
    }
});


