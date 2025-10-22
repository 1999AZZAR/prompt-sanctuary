// Function to display error message inline
function displayFormError(form, message) {
    const errorElementId = form.id === "loginForm" ? "loginErrorMessage" : "signupErrorMessage";
    const errorElement = document.getElementById(errorElementId);
    if (errorElement) {
        errorElement.textContent = message;
    }
}

// Function to clear previous error messages
function clearFormError(form) {
    const errorElementId = form.id === "loginForm" ? "loginErrorMessage" : "signupErrorMessage";
    const errorElement = document.getElementById(errorElementId);
    if (errorElement) {
        errorElement.textContent = "";
    }
}

// Function to hide loading animation and show form
function hideLoadingAnimation(form) {
    const loadingContainer = form.parentNode.querySelector(".loading-container");
    if (loadingContainer) {
        loadingContainer.remove();
    }
    form.classList.remove("hidden");
}

// Function to handle form submission
function handleFormSubmission(form, action) {
    clearFormError(form); // Clear previous errors
    const formData = new FormData(form);

    fetch(action, {
        method: 'POST',
        headers: window.CSRF.getFormHeaders(),
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                hideLoadingAnimation(form);
                displayFormError(form, data.error || "An error occurred.");
                if (form.id === "loginForm") {
                    document.getElementById("passwordLogin").value = "";
                } else if (form.id === "signupForm") {
                    document.getElementById("passwordSignup").value = "";
                    document.getElementById("confirmPassword").value = "";
                    const emailEl = document.getElementById("emailSignup");
                    if (emailEl) emailEl.value = "";
                }
                return Promise.reject(data); // Propagate error
            });
        }
        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return response.json();
        } else {
            // If not JSON, it might be HTML (redirect)
            throw new Error('Invalid response format');
        }
    })
    .then(data => {
        if (data.success) {
            // Show welcome message
            showLoginRewards(data);
            handleSuccess(data.redirect);
        } else {
            hideLoadingAnimation(form);
            displayFormError(form, data.error || "An error occurred.");
            if (form.id === "loginForm") {
                document.getElementById("passwordLogin").value = "";
            } else if (form.id === "signupForm") {
                document.getElementById("passwordSignup").value = "";
                document.getElementById("confirmPassword").value = "";
            }
        }
    })
    .catch(error => {
        if (!form.classList.contains("hidden")) {
            hideLoadingAnimation(form);
            // Use toast for general network errors, keep inline for form-specific issues if preferred
            showToast("A network error occurred. Please try again.", 'error');
            // displayFormError(form, "An error occurred. Please try again.");
            if (form.id === "loginForm") {
                document.getElementById("passwordLogin").value = "";
            } else if (form.id === "signupForm") {
                document.getElementById("passwordSignup").value = "";
                document.getElementById("confirmPassword").value = "";
                const emailEl = document.getElementById("emailSignup");
                if (emailEl) emailEl.value = "";
            }
        }
        console.error('Error in handleFormSubmission:', error);
    });
}

// Function to handle success
function handleSuccess(redirectUrl) {
    if (redirectUrl) {
        window.location.href = redirectUrl;
    }
}

// Function to validate login form
function validateLoginForm(form, username, password) {
    clearFormError(form);
    if (username.includes(" ")) {
        displayFormError(form, "Username cannot contain spaces.");
        return false;
    }

    if (username === password) {
        displayFormError(form, "Username cannot be equal to password.");
        return false;
    }

    const restrictedUsernames = ["system", "admin", "consol", "sysadmin", "useradmin"];
    if (restrictedUsernames.includes(username.toLowerCase())) {
        displayFormError(form, "Username cannot be one of: system, admin, consol, sysadmin, useradmin.");
        return false;
    }

    return true;
}

// Function to validate signup form
function validateSignupForm(form, username, password, confirmPassword) {
    clearFormError(form);
    if (username.includes(" ")) {
        displayFormError(form, "Username cannot contain spaces.");
        return false;
    }

    if (username === password) {
        displayFormError(form, "Username cannot be equal to password.");
        return false;
    }

    const restrictedUsernames = ["system", "admin", "consol", "sysadmin", "useradmin"];
    if (restrictedUsernames.includes(username.toLowerCase())) {
        displayFormError(form, "Username cannot be one of: system, admin, consol, sysadmin, useradmin.");
        return false;
    }

    if (password !== confirmPassword) {
        displayFormError(form, "Passwords do not match.");
        return false;
    }

    return true;
}

// Function to toggle between login and signup forms
function toggleForms() {
    const loginForm = document.getElementById("loginForm");
    const signupForm = document.getElementById("signupForm");
    loginForm.classList.toggle("hidden");
    signupForm.classList.toggle("hidden");
    clearFormError(loginForm);
    clearFormError(signupForm);
}

// Function to show loading animation
function showLoadingAnimation(form) {
    clearFormError(form);
    const loadingContainer = document.createElement("div");
    loadingContainer.classList.add("loading-container");
    loadingContainer.style.textAlign = 'center';

    const loadingAnimation = document.createElement("div");
    loadingAnimation.classList.add("loading-animation");
    loadingAnimation.textContent = 'Loading...';
    loadingAnimation.style.padding = '10px';

    const loadingText = document.createElement("div");
    loadingText.textContent = "Please wait...";
    loadingText.style.fontSize = '0.9em';
    loadingText.style.color = '#888';

    loadingContainer.appendChild(loadingAnimation);
    form.parentNode.insertBefore(loadingContainer, form);
    form.classList.add("hidden");
}

// Function to show login success message
function showLoginRewards(data) {
    // Check if this is a signup or login by looking at the current form
    const signupForm = document.getElementById("signupForm");
    const isSignup = signupForm && !signupForm.classList.contains("hidden");
    
    let message = isSignup ? "Welcome! Account created successfully!" : "Welcome back!";
    showToast(message, 'success');
}

// Event listeners for login and signup forms
document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("loginForm");
    const signupForm = document.getElementById("signupForm");

    // Toggle signup form
    const signupLink = document.getElementById("signupLink");
    if (signupLink) {
        signupLink.addEventListener("click", function (event) {
            event.preventDefault();
            toggleForms();
            resetLoginForm();
        });
    }

    // Toggle login form
    const loginLink = document.getElementById("loginLink");
    if (loginLink) {
        loginLink.addEventListener("click", function (event) {
            event.preventDefault();
            toggleForms();
            resetSignupForm();
        });
    }

    // Reset login form
    function resetLoginForm() {
        const usernameLogin = document.getElementById("usernameLogin");
        const passwordLogin = document.getElementById("passwordLogin");
        if (usernameLogin) usernameLogin.value = "";
        if (passwordLogin) passwordLogin.value = "";
        if (loginForm) clearFormError(loginForm);
    }

    // Reset signup form
    function resetSignupForm() {
        const usernameSignup = document.getElementById("usernameSignup");
        const passwordSignup = document.getElementById("passwordSignup");
        const confirmPassword = document.getElementById("confirmPassword");
        const emailEl = document.getElementById("emailSignup");
        
        if (usernameSignup) usernameSignup.value = "";
        if (passwordSignup) passwordSignup.value = "";
        if (confirmPassword) confirmPassword.value = "";
        if (emailEl) emailEl.value = "";
        if (signupForm) clearFormError(signupForm);
    }

    // Login form submission
    if (loginForm) {
        loginForm.addEventListener("submit", function (event) {
            event.preventDefault();
            clearFormError(loginForm);

            const username = document.getElementById("usernameLogin").value;
            const password = document.getElementById("passwordLogin").value;

            if (validateLoginForm(loginForm, username, password)) {
                showLoadingAnimation(loginForm);
                handleFormSubmission(loginForm, '/login');
            }
        });
    }

    // Signup form submission
    if (signupForm) {
        signupForm.addEventListener("submit", function (event) {
            event.preventDefault();
            clearFormError(signupForm);

            const username = document.getElementById("usernameSignup").value;
            const password = document.getElementById("passwordSignup").value;
            const confirmPassword = document.getElementById("confirmPassword").value;

            if (validateSignupForm(signupForm, username, password, confirmPassword)) {
                showLoadingAnimation(signupForm);
                handleFormSubmission(signupForm, '/signup');
            }
        });
    }
});