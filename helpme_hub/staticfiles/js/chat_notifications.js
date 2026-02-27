/**
 * Browser notifications for chat messages.
 */
(function() {
    'use strict';
    
    let notificationPermission = null;
    
    // Request notification permission
    function requestPermission() {
        if (!('Notification' in window)) {
            console.log('This browser does not support notifications');
            return;
        }
        
        if (Notification.permission === 'default') {
            Notification.requestPermission().then(permission => {
                notificationPermission = permission;
            });
        } else {
            notificationPermission = Notification.permission;
        }
    }
    
    // Show notification
    function showNotification(title, body, tag = null) {
        if (!('Notification' in window)) {
            return;
        }
        
        if (Notification.permission !== 'granted') {
            requestPermission();
            return;
        }
        
        // Only show if page is not focused
        if (document.hasFocus()) {
            return;
        }
        
        const options = {
            body: body,
            icon: '/static/favicon.ico', // You can add a favicon later
            tag: tag,
            requireInteraction: false,
        };
        
        try {
            const notification = new Notification(title, options);
            
            // Auto-close after 5 seconds
            setTimeout(() => {
                notification.close();
            }, 5000);
            
            // Focus window when notification is clicked
            notification.onclick = function() {
                window.focus();
                notification.close();
            };
        } catch (error) {
            console.error('Error showing notification:', error);
        }
    }
    
    // Update page title with unread count
    function updatePageTitle(unreadCount) {
        const baseTitle = document.title.replace(/^\(\d+\)\s*/, '');
        if (unreadCount > 0) {
            document.title = `(${unreadCount}) ${baseTitle}`;
        } else {
            document.title = baseTitle;
        }
    }
    
    // Initialize on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', requestPermission);
    } else {
        requestPermission();
    }
    
    // Export functions
    window.ChatNotifications = {
        show: showNotification,
        updateTitle: updatePageTitle,
        requestPermission: requestPermission
    };
})();
