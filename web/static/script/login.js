// window.onload handler
window.onload = function () {
    const loginForm = document.getElementById("loginForm");
    const signupForm = document.getElementById("signupForm");

    // Toggle signup form
    document.getElementById("signupLink").addEventListener("click", function (event) {
        event.preventDefault();
        loginForm.style.display = "none";
        signupForm.style.display = "block";
        resetLoginForm();
    });

    // Toggle login form 
    document.getElementById("loginLink").addEventListener("click", function (event) {
        event.preventDefault();
        loginForm.style.display = "block";
        signupForm.style.display = "none";
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

    // Add event listener for form submission
    loginForm.addEventListener("submit", function (event) {
        const username = document.getElementById("usernameLogin").value;
        const password = document.getElementById("passwordLogin").value;

        if (username.includes(" ")) {
            event.preventDefault();
            showErrorPopup("Username cannot contain spaces.");
            return;
        }

        if (username === password) {
            event.preventDefault();
            showErrorPopup("Username cannot be equal to password.");
            return;
        }
    });

    // Add event listener for form submission
    signupForm.addEventListener("submit", function (event) {
        const username = document.getElementById("usernameSignup").value;
        const password = document.getElementById("passwordSignup").value;
        const confirmPassword = document.getElementById("confirmPassword").value;

        if (username.includes(" ")) {
            event.preventDefault();
            showErrorPopup("Username cannot contain spaces.");
            return;
        }

        if (username === password) {
            event.preventDefault();
            showErrorPopup("Username cannot be equal to password.");
            return;
        }

        if (password !== confirmPassword) {
            event.preventDefault();
            showErrorPopup("Passwords do not match.");
            return;
        }
    });

    // Show error popup
    function showErrorPopup(message) {
        alert("Error: " + message);
    }
};
