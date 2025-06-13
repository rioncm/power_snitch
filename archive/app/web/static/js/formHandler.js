/*
* * This script handles form submissions using AJAX, processes the response
* * and displays appropriate messages to the user.
* * It supports multiple forms by initializing the handler with different form IDs.
* * It also handles errors and displays messages accordingly using tostify-js.
* * Usage:
* * Include this script in your HTML and call setupFormHandler with the form ID.
* * Example:
* * <script src="path/to/formHandler.js"></script>
* * setupFormHandler("myForm");  // Example form ID
* * setupFormHandler("contactForm"); // Another example
* * Form Example:
* * <form id="myForm" action="/api/submit-form" method="POST">
* *      <input type="text" name="username" required placeholder="Username">    
* *      <input type="email" name="email" required placeholder="Email">
* *      <button type="submit">Submit</button>
* * </form>
*/
    

document.addEventListener("DOMContentLoaded", function () {
    function setupFormHandler(formId) {
        const form = document.getElementById(formId);
        if (!form) {
            console.error(`Form with ID "${formId}" not found.`);
            return;
        }

        form.addEventListener("submit", async function (event) {
            event.preventDefault(); // Prevent default form submission

            const formData = new FormData(form);
            const url = form.getAttribute("action"); // API endpoint from form action
            const submitButton = form.querySelector("button[type='submit']"); // Get the submit button

            try {
                const response = await fetch(url, {
                    method: "POST",
                    body: formData
                });

                const result = await response.json();

                if (response.ok) {
                    handleSuccess(result, form);
                } else {
                    handleError(result, form);
                }
            } catch (error) {
                console.error(`Submission error for form "${formId}":`, error);
                showMessage(form, "An unexpected error occurred. Please try again.", "error");
            }
        });
    }

    function handleSuccess(data, form) {
        if (data.redirect_url) {
            window.location.href = data.redirect_url;
        } else if (data.message) {
            showMessage(form, data.message, "success");
        }
    }

    function handleError(data, form) {
        const message = data.error || "An error occurred. Please try again.";
        showMessage(form, message, "error");
    }

 function showMessage(form, message, type) {
    if (!form) {
        console.error(`Form element not found.`);
        return;
    }

    // Try to find the submit button inside the form
    const submitButton = form.querySelector("button[type='submit']");

    let toastPosition = { x: 0, y: 50 }; // Default position

    if (submitButton) {
        const buttonRect = submitButton.getBoundingClientRect();
        toastPosition = {
            x: buttonRect.left + window.scrollX, // Account for scrolling
            y: buttonRect.top + window.scrollY + buttonRect.height + 10
        };
    } else {
        console.warn(`Submit button not found in form. Using default position.`);
    }

    Toastify({
        text: message,
        duration: 3000,
        close: true,
        gravity: "top", // Toast position
        position: "center", // Default center positioning
        style: {
            background: type === "success" ? "green" : "red",
        },
        offset: toastPosition // Now safely calculated
    }).showToast();
}


// ✅ Attach to `window` to make it globally available
window.setupFormHandler = setupFormHandler;
});


