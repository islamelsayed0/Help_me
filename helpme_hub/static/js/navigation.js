// Mobile Navigation Functionality

document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuButton = document.getElementById('mobileMenuButton');
    const closeMobileMenu = document.getElementById('closeMobileMenu');
    const mobileSidebar = document.getElementById('mobileSidebar');
    const mobileSidebarContent = document.getElementById('mobileSidebarContent');
    const profileDropdownButton = document.getElementById('profileDropdownButton');
    const profileDropdown = document.getElementById('profileDropdown');
    let isMenuOpen = false;
    
    // Prevent body scroll when menu is open
    function preventBodyScroll(prevent) {
        if (prevent) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
    }
    
    // Open mobile menu
    function openMobileMenu() {
        if (mobileSidebar && mobileSidebarContent) {
            mobileSidebar.classList.remove('hidden');
            // Force reflow to ensure transition works
            setTimeout(() => {
                mobileSidebarContent.classList.remove('-translate-x-full');
            }, 10);
            isMenuOpen = true;
            preventBodyScroll(true);
        }
    }
    
    // Close mobile menu
    function closeMobileMenuFunc() {
        if (mobileSidebar && mobileSidebarContent) {
            mobileSidebarContent.classList.add('-translate-x-full');
            setTimeout(() => {
                mobileSidebar.classList.add('hidden');
            }, 300); // Match transition duration
            isMenuOpen = false;
            preventBodyScroll(false);
        }
    }
    
    // Mobile menu toggle
    if (mobileMenuButton) {
        mobileMenuButton.addEventListener('click', function(e) {
            e.stopPropagation();
            if (isMenuOpen) {
                closeMobileMenuFunc();
            } else {
                openMobileMenu();
            }
        });
    }
    
    if (closeMobileMenu) {
        closeMobileMenu.addEventListener('click', function(e) {
            e.stopPropagation();
            closeMobileMenuFunc();
        });
    }
    
    // Close mobile menu when clicking outside (on backdrop)
    if (mobileSidebar) {
        mobileSidebar.addEventListener('click', function(e) {
            if (e.target === mobileSidebar) {
                closeMobileMenuFunc();
            }
        });
    }
    
    // Close mobile menu when clicking on a link
    if (mobileSidebarContent) {
        const links = mobileSidebarContent.querySelectorAll('a');
        links.forEach(link => {
            link.addEventListener('click', function() {
                closeMobileMenuFunc();
            });
        });
    }
    
    // Close mobile menu with ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && isMenuOpen) {
            closeMobileMenuFunc();
        }
    });
    
    // Profile dropdown toggle
    if (profileDropdownButton && profileDropdown) {
        profileDropdownButton.addEventListener('click', function(e) {
            e.stopPropagation();
            profileDropdown.classList.toggle('hidden');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!profileDropdownButton.contains(e.target) && !profileDropdown.contains(e.target)) {
                profileDropdown.classList.add('hidden');
            }
        });
    }
    
    // Handle window resize - close menu if switching to desktop
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 1024 && isMenuOpen) {
            closeMobileMenuFunc();
        }
    });
});


