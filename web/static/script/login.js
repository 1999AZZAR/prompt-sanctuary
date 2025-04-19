// Function to show error popup
function showErrorPopup(message) {
    alert("Error: " + message);
}

// Function to handle form submission
function handleFormSubmission(form, action) {
    const formData = new FormData(form);

    fetch(action, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                showErrorPopup(data.error || "An error occurred.");
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            handleSuccess(data.redirect); // Redirect on success
        } else {
            showErrorPopup(data.error || "An error occurred.");
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showErrorPopup("An error occurred. Please try again.");
    });
}

// Function to handle success
function handleSuccess(redirectUrl) {
    if (redirectUrl) {
        window.location.href = redirectUrl; // Redirect to the provided URL
    }
}

// Function to validate login form
function validateLoginForm(username, password) {
    if (username.includes(" ")) {
        showErrorPopup("Username cannot contain spaces.");
        return false;
    }

    if (username === password) {
        showErrorPopup("Username cannot be equal to password.");
        return false;
    }

    const restrictedUsernames = ["system", "admin", "consol", "sysadmin", "useradmin"];
    if (restrictedUsernames.includes(username.toLowerCase())) {
        showErrorPopup("Username cannot be one of: system, admin, consol, sysadmin, useradmin.");
        return false;
    }

    return true;
}

// Function to validate signup form
function validateSignupForm(username, password, confirmPassword) {
    if (username.includes(" ")) {
        showErrorPopup("Username cannot contain spaces.");
        return false;
    }

    if (username === password) {
        showErrorPopup("Username cannot be equal to password.");
        return false;
    }

    const restrictedUsernames = ["system", "admin", "consol", "sysadmin", "useradmin"];
    if (restrictedUsernames.includes(username.toLowerCase())) {
        showErrorPopup("Username cannot be one of: system, admin, consol, sysadmin, useradmin.");
        return false;
    }

    if (password !== confirmPassword) {
        showErrorPopup("Passwords do not match.");
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
}

// Function to show loading animation
function showLoadingAnimation(form) {
    const loadingContainer = document.createElement("div");
    loadingContainer.classList.add("loading-container");

    const loadingAnimation = document.createElement("div");
    loadingAnimation.classList.add("loading-animation");

    for (let i = 0; i < 5; i++) {
        const dot = document.createElement("div");
        dot.classList.add("dot");
        loadingAnimation.appendChild(dot);
    }

    const loadingText = document.createElement("div");
    loadingText.textContent = "Loading...";
    loadingContainer.appendChild(loadingAnimation);
    loadingContainer.appendChild(loadingText);

    form.parentNode.insertBefore(loadingContainer, form);
    form.classList.add("hidden");
}

// Event listeners for login and signup forms
document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("loginForm");
    const signupForm = document.getElementById("signupForm");

    // Toggle signup form
    document.getElementById("signupLink").addEventListener("click", function (event) {
        event.preventDefault();
        toggleForms();
        resetLoginForm();
    });

    // Toggle login form
    document.getElementById("loginLink").addEventListener("click", function (event) {
        event.preventDefault();
        toggleForms();
        resetSignupForm();
    });

    // Reset login form
    function resetLoginForm() {
        document.getElementById("usernameLogin").value = "";
        document.getElementById("passwordLogin").value = "";
    }

    // Reset signup form
    function resetSignupForm() {
        document.getElementById("usernameSignup").value = "";
        document.getElementById("passwordSignup").value = "";
        document.getElementById("confirmPassword").value = "";
    }

    // Login form submission
    if (loginForm) {
        loginForm.addEventListener("submit", function (event) {
            event.preventDefault();

            const username = document.getElementById("usernameLogin").value;
            const password = document.getElementById("passwordLogin").value;

            if (validateLoginForm(username, password)) {
                showLoadingAnimation(loginForm);
                handleFormSubmission(loginForm, '/login');
            }
        });
    }

    // Signup form submission
    if (signupForm) {
        signupForm.addEventListener("submit", function (event) {
            event.preventDefault();

            const username = document.getElementById("usernameSignup").value;
            const password = document.getElementById("passwordSignup").value;
            const confirmPassword = document.getElementById("confirmPassword").value;

            if (validateSignupForm(username, password, confirmPassword)) {
                showLoadingAnimation(signupForm);
                handleFormSubmission(signupForm, '/signup');
            }
        });
    }
});