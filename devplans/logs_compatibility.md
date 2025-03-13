# Logs Page Compatibility Plan

## Current Issues

1. **Template Structure**
   - Inline styles should be moved to style.css
   - Missing loading state for log refresh
   - No error handling for failed log loading
   - Missing pagination or infinite scroll for large log files
   - No log filtering/search functionality

2. **Log Display**
   - Basic color coding for log levels
   - No timestamp formatting
   - No log level badges
   - Missing log entry hover effects
   - No copy functionality for individual log entries

3. **Performance**
   - Full page reload on refresh
   - No WebSocket for real-time updates
   - No log buffering for large files
   - Missing log compression for download
   - No log rotation handling

4. **Accessibility**
   - Missing ARIA labels
   - No keyboard navigation
   - Missing screen reader support
   - No high contrast mode support
   - Missing focus management

## Required Changes

1. **Template Structure Updates**
   ```html
   {% extends "base.html" %}
   
   {% block title %}Power Snitch - Logs{% endblock %}
   
   {% block content %}
   <div class="card">
       <div class="card-header d-flex justify-content-between align-items-center">
           <h4 class="mb-0">System Logs</h4>
           <div class="log-controls">
               <div class="input-group me-2">
                   <input type="text" class="form-control" id="log-search" 
                          placeholder="Search logs..." aria-label="Search logs">
                   <button class="btn btn-outline-secondary" type="button">
                       <i class="bi bi-search"></i>
                   </button>
               </div>
               <div class="btn-group">
                   <button class="btn btn-outline-secondary" id="refresh-logs" aria-label="Refresh logs">
                       <i class="bi bi-arrow-clockwise"></i>
                       <span class="spinner-border spinner-border-sm d-none" role="status"></span>
                   </button>
                   <button class="btn btn-outline-primary" id="download-logs" aria-label="Download logs">
                       <i class="bi bi-download"></i>
                   </button>
               </div>
           </div>
       </div>
       <div class="card-body">
           <div class="log-container" id="log-viewer" role="log" aria-live="polite">
               {% for log in logs %}
                   <div class="log-entry {% if 'ERROR' in log %}error{% elif 'WARNING' in log %}warning{% else %}info{% endif %}"
                        role="log" aria-label="Log entry">
                       <span class="log-timestamp">{{ log.timestamp }}</span>
                       <span class="log-level">{{ log.level }}</span>
                       <span class="log-message">{{ log.message }}</span>
                       <button class="btn btn-sm btn-outline-secondary copy-log" aria-label="Copy log entry">
                           <i class="bi bi-clipboard"></i>
                       </button>
                   </div>
               {% endfor %}
           </div>
       </div>
   </div>
   {% endblock %}
   ```

2. **CSS Updates**
   ```css
   /* Log container */
   .log-container {
       background-color: var(--log-bg);
       color: var(--log-text);
       font-family: 'Fira Code', monospace;
       padding: 1rem;
       border-radius: var(--border-radius);
       height: 600px;
       overflow-y: auto;
       position: relative;
   }
   
   /* Log entry */
   .log-entry {
       display: grid;
       grid-template-columns: auto auto 1fr auto;
       gap: 1rem;
       padding: 0.5rem;
       border-radius: var(--border-radius);
       transition: background-color var(--transition-speed);
   }
   
   .log-entry:hover {
       background-color: var(--log-hover-bg);
   }
   
   /* Log levels */
   .log-level {
       padding: 0.25rem 0.5rem;
       border-radius: var(--border-radius);
       font-size: 0.875rem;
       font-weight: 500;
   }
   
   .log-level.error { background-color: var(--danger-color); color: white; }
   .log-level.warning { background-color: var(--warning-color); color: var(--dark-color); }
   .log-level.info { background-color: var(--info-color); color: white; }
   ```

3. **JavaScript Updates**
   ```javascript
   document.addEventListener('DOMContentLoaded', function() {
       const logViewer = document.getElementById('log-viewer');
       const refreshBtn = document.getElementById('refresh-logs');
       const spinner = refreshBtn.querySelector('.spinner-border');
       let autoScroll = true;
       
       // Auto-scroll toggle
       logViewer.addEventListener('scroll', function() {
           const isAtBottom = this.scrollHeight - this.scrollTop === this.clientHeight;
           autoScroll = isAtBottom;
       });
       
       // Refresh logs with loading state
       refreshBtn.addEventListener('click', async function() {
           this.disabled = true;
           spinner.classList.remove('d-none');
           
           try {
               const response = await fetch('/api/logs');
               const logs = await response.json();
               updateLogViewer(logs);
           } catch (error) {
               showError('Failed to refresh logs');
           } finally {
               this.disabled = false;
               spinner.classList.add('d-none');
           }
       });
       
       // Copy log entry
       document.querySelectorAll('.copy-log').forEach(btn => {
           btn.addEventListener('click', function() {
               const logEntry = this.closest('.log-entry');
               const text = logEntry.querySelector('.log-message').textContent;
               navigator.clipboard.writeText(text);
               showToast('Log entry copied to clipboard');
           });
       });
       
       // Search logs
       const searchInput = document.getElementById('log-search');
       searchInput.addEventListener('input', debounce(function() {
           const query = this.value.toLowerCase();
           filterLogs(query);
       }, 300));
   });
   ```

## Implementation Plan

1. **Phase 1: Core Structure Updates**
   - Move inline styles to style.css
   - Add loading states
   - Implement error handling
   - Add search functionality
   - Update log entry structure

2. **Phase 2: Log Display Improvements**
   - Add timestamp formatting
   - Implement log level badges
   - Add hover effects
   - Add copy functionality
   - Improve log entry layout

3. **Phase 3: Performance Optimization**
   - Implement WebSocket updates
   - Add log buffering
   - Optimize download
   - Add log rotation handling
   - Implement infinite scroll

4. **Phase 4: Accessibility Enhancements**
   - Add ARIA labels
   - Implement keyboard navigation
   - Add screen reader support
   - Support high contrast mode
   - Improve focus management

5. **Phase 5: Testing and Optimization**
   - Test with large log files
   - Verify WebSocket functionality
   - Check accessibility compliance
   - Test performance
   - Verify error handling

## Notes

1. All changes should maintain backward compatibility with existing log format
2. WebSocket implementation should handle connection errors gracefully
3. Log filtering should be efficient for large files
4. Accessibility features should follow WCAG guidelines
5. Performance optimizations should not compromise functionality 