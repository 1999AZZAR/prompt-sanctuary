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

    // Show error popup
    function showErrorPopup(message) {
        console.error("Error:", message);
        resetLoginForm();
        resetSignupForm();
    }

    // Show error if present
    const errorMessage = '{{ error_message }}';
    if (errorMessage && errorMessage.trim() !== '') {
        showErrorPopup(errorMessage);
    }
};