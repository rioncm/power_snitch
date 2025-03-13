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