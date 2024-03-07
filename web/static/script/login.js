window.onload = function() {
    const loginForm = document.getElementById("loginForm");
    const signupForm = document.getElementById("signupForm");

    document.getElementById("signupLink").addEventListener("click", function(event) {
        event.preventDefault();
        loginForm.style.display = "none";
        signupForm.style.display = "block";
        resetLoginForm();
    });

    document.getElementById("loginLink").addEventListener("click", function(event) {
        event.preventDefault();
        loginForm.style.display = "block";
        signupForm.style.display = "none";
        resetSignupForm();
    });

    function resetLoginForm() {
        document.getElementById("usernameLogin").value = "";
        document.getElementById("passwordLogin").value = "";
    }

    function resetSignupForm() {
        document.getElementById("usernameSignup").value = "";
        document.getElementById("passwordSignup").value = "";
        document.getElementById("confirmPassword").value = "";
    }

    function showErrorPopup(message) {
        // Instead of alerting, you can log the error to the console or perform any other action
        console.error("Error:", message);
        resetLoginForm();
        resetSignupForm();
    }

    const errorMessage = '{{ error_message }}';
    if (errorMessage && errorMessage.trim() !== '') {
        showErrorPopup(errorMessage);
    }
};
