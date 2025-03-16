document.addEventListener('DOMContentLoaded', function() {
    // Initialize service sections based on enabled state
    document.querySelectorAll('[data-service]').forEach(section => {
        const fields = section.querySelector('.fields');
        const toggle = section.querySelector('.service-toggle');
        const checkbox = section.querySelector('input[type="checkbox"]');
        
        // Set initial state
        if (section.dataset.expanded === 'true') {
            fields.style.display = 'block';
            if (toggle) {
                toggle.querySelector('i').classList.remove('fa-chevron-down');
                toggle.querySelector('i').classList.add('fa-chevron-up');
            }
        } else {
            fields.style.display = 'none';
            if (toggle) {
                toggle.querySelector('i').classList.remove('fa-chevron-up');
                toggle.querySelector('i').classList.add('fa-chevron-down');
            }
        }
        
        // Handle toggle button click
        if (toggle) {
            toggle.addEventListener('click', function() {
                const isExpanded = fields.style.display === 'block';
                fields.style.display = isExpanded ? 'none' : 'block';
                const icon = this.querySelector('i');
                icon.classList.toggle('fa-chevron-down');
                icon.classList.toggle('fa-chevron-up');
            });
        }
        
        // Handle checkbox change
        if (checkbox) {
            checkbox.addEventListener('change', function() {
                const isEnabled = this.checked;
                fields.style.display = isEnabled ? 'block' : 'none';
                if (toggle) {
                    const icon = toggle.querySelector('i');
                    if (isEnabled) {
                        icon.classList.remove('fa-chevron-down');
                        icon.classList.add('fa-chevron-up');
                    } else {
                        icon.classList.remove('fa-chevron-up');
                        icon.classList.add('fa-chevron-down');
                    }
                }
            });
        }
    });
});

// Webhook form submission
document.addEventListener('DOMContentLoaded', function() {
    const webhookForm = document.getElementById('webhook-form');
    if (webhookForm) {
        webhookForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const form = this;
            const submitButton = form.querySelector('button[type="submit"]');
            const spinner = submitButton.querySelector('.spinner-border');
            const statusDiv = document.getElementById('webhookStatus');
            
            // Disable button and show spinner
            submitButton.disabled = true;
            spinner.classList.remove('d-none');
            statusDiv.innerHTML = '';
            
            // Create FormData object
            const formData = new FormData(form);
            
            // Send AJAX request
            fetch('/api/settings/webhook', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': formData.get('csrf_token')
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast('success', data.message);
                } else {
                    showToast('error', data.error || 'Failed to update webhook settings');
                }
            })
            .catch(error => {
                showToast('error', 'Failed to update webhook settings');
                console.error('Error:', error);
            })
            .finally(() => {
                // Re-enable button and hide spinner
                submitButton.disabled = false;
                spinner.classList.add('d-none');
            });
        });
    }
});

// Toast notification function
function showToast(type, message) {
    const toast = $(`
        <div class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <strong class="me-auto">${type === 'success' ? 'Success' : 'Error'}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `);
    
    $('.toast-container').append(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.on('hidden.bs.toast', function() {
        toast.remove();
    });
} 