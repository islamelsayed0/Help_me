/**
 * Kanban Board Drag-and-Drop Functionality
 */
(function() {
    'use strict';
    
    let draggedElement = null;
    let draggedStatus = null;
    
    // Initialize drag and drop
    function initDragAndDrop() {
        const ticketCards = document.querySelectorAll('.ticket-card');
        const kanbanColumns = document.querySelectorAll('.kanban-column');
        
        // Make ticket cards draggable
        ticketCards.forEach(card => {
            card.addEventListener('dragstart', handleDragStart);
            card.addEventListener('dragend', handleDragEnd);
        });
        
        // Setup drop zones
        kanbanColumns.forEach(column => {
            column.addEventListener('dragover', handleDragOver);
            column.addEventListener('dragleave', handleDragLeave);
            column.addEventListener('drop', handleDrop);
        });
    }
    
    function handleDragStart(e) {
        draggedElement = this;
        draggedStatus = this.dataset.status;
        this.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', this.outerHTML);
    }
    
    function handleDragEnd(e) {
        this.classList.remove('dragging');
        
        // Remove drag-over class from all columns
        document.querySelectorAll('.kanban-column').forEach(col => {
            col.classList.remove('drag-over');
        });
    }
    
    function handleDragOver(e) {
        if (e.preventDefault) {
            e.preventDefault();
        }
        e.dataTransfer.dropEffect = 'move';
        this.classList.add('drag-over');
        return false;
    }
    
    function handleDragLeave(e) {
        this.classList.remove('drag-over');
    }
    
    function handleDrop(e) {
        if (e.stopPropagation) {
            e.stopPropagation();
        }
        
        this.classList.remove('drag-over');
        
        if (draggedElement) {
            const newStatus = this.dataset.status;
            const ticketId = draggedElement.dataset.ticketId;
            
            // Only update if status changed
            if (newStatus !== draggedStatus) {
                updateTicketStatus(ticketId, newStatus, draggedElement);
            }
        }
        
        return false;
    }
    
    function updateTicketStatus(ticketId, newStatus, element) {
        // Show loading state
        element.style.opacity = '0.5';
        
        // Get CSRF token
        const csrfToken = getCookie('csrftoken');
        
        // Send AJAX request
        fetch(`/tickets/admin/${ticketId}/update-status/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: `status=${encodeURIComponent(newStatus)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Move element to new column
                const targetColumn = document.querySelector(`[data-status="${newStatus}"] .space-y-3`);
                if (targetColumn) {
                    // Update element's status
                    element.dataset.status = newStatus;
                    element.style.opacity = '1';
                    
                    // Remove from old column
                    draggedElement.remove();
                    
                    // Add to new column
                    targetColumn.appendChild(element);
                    
                    // Update column counts
                    updateColumnCounts();
                }
            } else {
                // Revert on error
                element.style.opacity = '1';
                alert('Failed to update ticket status. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error updating ticket status:', error);
            element.style.opacity = '1';
            alert('An error occurred. Please refresh the page.');
        });
    }
    
    function updateColumnCounts() {
        // Update count badges in column headers
        document.querySelectorAll('.kanban-column').forEach(column => {
            const status = column.dataset.status;
            const count = column.querySelectorAll('.ticket-card').length;
            const header = column.querySelector('h3');
            if (header) {
                const match = header.textContent.match(/^(.+?)\s*\((\d+)\)/);
                if (match) {
                    header.textContent = `${match[1]} (${count})`;
                }
            }
        });
    }
    
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDragAndDrop);
    } else {
        initDragAndDrop();
    }
})();
