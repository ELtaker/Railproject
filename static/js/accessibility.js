/**
 * Raildrops Accessibility JavaScript Components
 * 
 * This file contains all JavaScript functionality for accessibility features:
 * 1. Dark/Light mode toggle
 * 2. Toast notifications
 * 3. Password visibility toggle
 * 4. Focus management
 * 5. Keyboard navigation enhancements
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    
    // ------------------------------------------
    // Dark/Light Mode Toggle (DISABLED FOR DEVELOPMENT)
    // ------------------------------------------
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        // Remove dark-mode class if it exists to ensure CSS controls the styling
        document.body.classList.remove('dark-mode');
        
        // Clear any saved theme preference
        localStorage.removeItem('raildrops-theme');
        
        // Update icon to show light mode is active
        updateToggleIcon(false);
        
        // Hide the toggle button since it's not functional
        themeToggle.style.display = 'none';
        
        /* ORIGINAL CODE (COMMENTED OUT)
        // Check for saved theme preference or preferred color scheme
        const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const savedTheme = localStorage.getItem('raildrops-theme');
        
        // Set initial theme based on saved preference or system preference
        if (savedTheme === 'dark' || (!savedTheme && prefersDarkMode)) {
            document.body.classList.add('dark-mode');
            updateToggleIcon(true);
        }
        
        // Handle toggle click
        themeToggle.addEventListener('click', function() {
            const isDarkMode = document.body.classList.toggle('dark-mode');
            localStorage.setItem('raildrops-theme', isDarkMode ? 'dark' : 'light');
            updateToggleIcon(isDarkMode);
            
            // Announce theme change to screen readers
            announceToScreenReader(`Byttet til ${isDarkMode ? 'mørk' : 'lys'} modus`);
        });
        */
    }
    
    // Helper function to update icon
    function updateToggleIcon(isDarkMode) {
        const icon = themeToggle.querySelector('i');
        if (icon) {
            icon.className = isDarkMode ? 'fa fa-sun' : 'fa fa-moon';
            
            // Update the text too if present
            const text = themeToggle.querySelector('span');
            if (text) {
                text.textContent = isDarkMode ? 'Lys modus' : 'Mørk modus';
            }
        }
    }
    
    // ------------------------------------------
    // Toast Notifications
    // ------------------------------------------
    const toastContainer = document.querySelector('.toast-container');
    if (toastContainer) {
        const toasts = document.querySelectorAll('.toast');
        toasts.forEach(toast => {
            new bootstrap.Toast(toast, {
                autohide: true,
                delay: 5000
            }).show();
        });
    }
    
    // ------------------------------------------
    // Password Visibility Toggle
    // ------------------------------------------
    const togglePasswordButtons = document.querySelectorAll('.toggle-password');
    togglePasswordButtons.forEach(button => {
        button.addEventListener('click', function() {
            const passwordInput = this.previousElementSibling;
            
            // Toggle input type between password and text
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            
            // Toggle icon between eye and eye-slash
            const icon = this.querySelector('i');
            icon.className = type === 'password' ? 'fa fa-eye' : 'fa fa-eye-slash';
            
            // Announce to screen readers
            const message = type === 'password' ? 'Passord skjult' : 'Passord synlig';
            announceToScreenReader(message);
        });
    });
    
    // ------------------------------------------
    // Focus Management & Keyboard Navigation
    // ------------------------------------------
    
    // Add focus indicator to improve keyboard navigation visibility
    document.addEventListener('keydown', function(e) {
        // Check if tab key was pressed
        if (e.key === 'Tab') {
            document.body.classList.add('keyboard-user');
        }
    });
    
    // Remove focus indicator if mouse is used
    document.addEventListener('mousedown', function() {
        document.body.classList.remove('keyboard-user');
    });
    
    // ------------------------------------------
    // Helper Functions
    // ------------------------------------------
    
    // Function to announce messages to screen readers
    function announceToScreenReader(message) {
        let announcer = document.getElementById('screen-reader-announcer');
        
        // Create announcer element if it doesn't exist
        if (!announcer) {
            announcer = document.createElement('div');
            announcer.id = 'screen-reader-announcer';
            announcer.setAttribute('aria-live', 'polite');
            announcer.setAttribute('aria-atomic', 'true');
            announcer.className = 'visually-hidden';
            document.body.appendChild(announcer);
        }
        
        // Set the message and clear it after a short delay
        announcer.textContent = message;
        setTimeout(() => {
            announcer.textContent = '';
        }, 3000);
    }
});
