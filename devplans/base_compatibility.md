# Base Template Compatibility Plan

## Current Issues

1. **Template Structure**
   - Missing favicon and meta tags for SEO
   - No dark mode support
   - No loading state for JavaScript resources
   - Missing error handling for failed resource loading

2. **Navigation**
   - No active state for current page
   - Missing mobile menu improvements
   - No user profile/avatar display
   - Missing breadcrumb navigation

3. **Flash Messages**
   - No auto-dismiss functionality
   - Missing animation for message appearance/disappearance
   - No message stacking for multiple alerts
   - Missing close button for dismissible alerts

4. **Container Structure**
   - Fixed container width may not be optimal for all pages
   - Missing footer section
   - No responsive padding adjustments
   - Missing max-width constraints for certain content types

## Required Changes

1. **Template Structure Updates**
   ```html
   <head>
       <!-- Add favicon -->
       <link rel="icon" type="image/x-icon" href="{{ url_for('static', filename='favicon.ico') }}">
       
       <!-- Add meta tags -->
       <meta name="description" content="Power Snitch - UPS Monitoring System">
       <meta name="keywords" content="UPS, monitoring, power, battery">
       
       <!-- Add dark mode support -->
       <meta name="color-scheme" content="light dark">
       
       <!-- Add preload for critical resources -->
       <link rel="preload" href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" as="style">
   </head>
   ```

2. **Navigation Improvements**
   ```html
   <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
       <!-- Add active state -->
       <a class="nav-link {% if request.endpoint == 'index' %}active{% endif %}" href="{{ url_for('index') }}">
           Dashboard
       </a>
       
       <!-- Add user profile -->
       <div class="user-profile">
           <img src="{{ current_user.avatar or url_for('static', filename='default-avatar.png') }}" 
                alt="User avatar" class="avatar">
           <span class="username">{{ current_user.username }}</span>
       </div>
   </nav>
   ```

3. **Flash Message Enhancements**
   ```html
   <div class="flash-messages">
       {% with messages = get_flashed_messages(with_categories=true) %}
           {% if messages %}
               {% for category, message in messages %}
                   <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                       {{ message }}
                       <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                   </div>
               {% endfor %}
           {% endif %}
       {% endwith %}
   </div>
   ```

4. **Container and Layout Updates**
   ```html
   <div class="main-container">
       <!-- Add breadcrumb -->
       <nav aria-label="breadcrumb">
           <ol class="breadcrumb">
               {% block breadcrumb %}{% endblock %}
           </ol>
       </nav>
       
       <!-- Main content -->
       <div class="content-wrapper">
           {% block content %}{% endblock %}
       </div>
       
       <!-- Add footer -->
       <footer class="footer mt-auto py-3">
           <div class="container">
               <span class="text-muted">Power Snitch v1.0.0</span>
           </div>
       </footer>
   </div>
   ```

## Implementation Plan

1. **Phase 1: Core Structure Updates**
   - Add favicon and meta tags
   - Implement dark mode support
   - Add resource preloading
   - Update container structure

2. **Phase 2: Navigation Enhancements**
   - Add active state for current page
   - Implement user profile section
   - Add breadcrumb navigation
   - Improve mobile menu

3. **Phase 3: Flash Message Improvements**
   - Add auto-dismiss functionality
   - Implement message animations
   - Add close buttons
   - Handle message stacking

4. **Phase 4: Layout and Responsiveness**
   - Add footer section
   - Implement responsive padding
   - Add max-width constraints
   - Update container classes

5. **Phase 5: Testing and Optimization**
   - Test all changes across different browsers
   - Verify mobile responsiveness
   - Check dark mode functionality
   - Optimize resource loading

## CSS Updates Required

1. **Add to style.css**
   ```css
   /* Dark mode support */
   @media (prefers-color-scheme: dark) {
       :root {
           --bg-color: #1a1a1a;
           --text-color: #ffffff;
       }
   }
   
   /* Flash message animations */
   .alert {
       animation: slideIn 0.3s ease-out;
   }
   
   /* User profile styling */
   .user-profile {
       display: flex;
       align-items: center;
       gap: 0.5rem;
   }
   
   .avatar {
       width: 32px;
       height: 32px;
       border-radius: 50%;
   }
   ```

## JavaScript Updates Required

1. **Add to base template**
   ```javascript
   // Auto-dismiss flash messages
   document.addEventListener('DOMContentLoaded', function() {
       const alerts = document.querySelectorAll('.alert');
       alerts.forEach(alert => {
           setTimeout(() => {
               alert.classList.remove('show');
               setTimeout(() => alert.remove(), 150);
           }, 5000);
       });
   });
   
   // Dark mode toggle
   const darkModeToggle = document.getElementById('darkModeToggle');
   if (darkModeToggle) {
       darkModeToggle.addEventListener('click', () => {
           document.documentElement.classList.toggle('dark-mode');
       });
   }
   ```

## Notes

1. All changes should maintain backward compatibility with existing templates
2. Dark mode implementation should respect system preferences
3. Resource loading should be optimized for performance
4. Mobile responsiveness should be tested thoroughly
5. Flash messages should be accessible and keyboard-navigable 