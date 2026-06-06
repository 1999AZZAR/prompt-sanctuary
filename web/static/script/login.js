// web/static/script/login.js
(function () {
    'use strict';

    function displayFormError(form, message) {
        const errorElementId = form.id === "loginForm" ? "loginErrorMessage" : "signupErrorMessage";
        const errorElement = document.getElementById(errorElementId);
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.hidden = false;
        }
        if (typeof showToast === 'function') showToast(message, 'error');
    }

    function clearFormError(form) {
        const errorElementId = form.id === "loginForm" ? "loginErrorMessage" : "signupErrorMessage";
        const errorElement = document.getElementById(errorElementId);
        if (errorElement) {
            errorElement.textContent = "";
            errorElement.hidden = true;
        }
    }

    function hideLoadingAnimation(form) {
        const loadingContainer = form.parentNode ? form.parentNode.querySelector(".loading-container") : null;
        if (loadingContainer) loadingContainer.remove();
        form.classList.remove("hidden");
    }

    function handleFormSubmission(form, action) {
        clearFormError(form);
        const formData = new FormData(form);

        fetch(action, {
            method: 'POST',
            headers: window.CSRF.getFormHeaders(),
            body: formData
        })
        .then(function (response) {
            if (!response.ok) {
                return response.json().then(function (data) {
                    hideLoadingAnimation(form);
                    displayFormError(form, (data && (data.error || data.message)) || "An error occurred.");
                    if (form.id === "loginForm") {
                        const p = document.getElementById("passwordLogin");
                        if (p) p.value = "";
                    } else if (form.id === "signupForm") {
                        const p = document.getElementById("passwordSignup");
                        if (p) p.value = "";
                        const c = document.getElementById("confirmPassword");
                        if (c) c.value = "";
                        const e = document.getElementById("emailSignup");
                        if (e) e.value = "";
                    }
                    return Promise.reject(data);
                });
            }
            return response.json();
        })
        .then(function (data) {
            if (data.success) {
                if (data.daily_bonus || data.new_achievements) {
                    showLoginRewards(data);
                }
                handleSuccess(data.redirect);
            } else {
                hideLoadingAnimation(form);
                displayFormError(form, (data && (data.error || data.message)) || "An error occurred.");
                if (form.id === "loginForm") {
                    const p = document.getElementById("passwordLogin");
                    if (p) p.value = "";
                } else if (form.id === "signupForm") {
                    const p = document.getElementById("passwordSignup");
                    if (p) p.value = "";
                    const c = document.getElementById("confirmPassword");
                    if (c) c.value = "";
                }
            }
        })
        .catch(function (error) {
            if (!form.classList.contains("hidden")) {
                hideLoadingAnimation(form);
                if (typeof showToast === 'function') showToast("A network error occurred. Please try again.", 'error');
                if (form.id === "loginForm") {
                    const p = document.getElementById("passwordLogin");
                    if (p) p.value = "";
                } else if (form.id === "signupForm") {
                    const p = document.getElementById("passwordSignup");
                    if (p) p.value = "";
                    const c = document.getElementById("confirmPassword");
                    if (c) c.value = "";
                    const e = document.getElementById("emailSignup");
                    if (e) e.value = "";
                }
            }
            console.error('Error in handleFormSubmission:', error);
        });
    }

    function handleSuccess(redirectUrl) {
        if (redirectUrl) window.location.href = redirectUrl;
    }

    function validateLoginForm(form, username, password) {
        clearFormError(form);
        if (!username || !password) {
            displayFormError(form, "Username and password are required.");
            return false;
        }
        if (username.includes(" ")) {
            displayFormError(form, "Username cannot contain spaces.");
            return false;
        }
        if (username === password) {
            displayFormError(form, "Username cannot be equal to password.");
            return false;
        }
        const restricted = ["system", "admin", "consol", "sysadmin", "useradmin"];
        if (restricted.indexOf(username.toLowerCase()) !== -1) {
            displayFormError(form, "Username cannot be one of: system, admin, consol, sysadmin, useradmin.");
            return false;
        }
        return true;
    }

    function validateSignupForm(form, username, password, confirmPassword) {
        clearFormError(form);
        if (!username || !password || !confirmPassword) {
            displayFormError(form, "All fields are required.");
            return false;
        }
        if (username.length < 3 || username.length > 32) {
            displayFormError(form, "Username must be 3 to 32 characters.");
            return false;
        }
        if (!/^[A-Za-z0-9_]+$/.test(username)) {
            displayFormError(form, "Username may only contain letters, numbers, and underscores.");
            return false;
        }
        if (password.length < 6) {
            displayFormError(form, "Password must be at least 6 characters.");
            return false;
        }
        if (password !== confirmPassword) {
            displayFormError(form, "Passwords do not match.");
            return false;
        }
        const restricted = ["system", "admin", "consol", "sysadmin", "useradmin"];
        if (restricted.indexOf(username.toLowerCase()) !== -1) {
            displayFormError(form, "Username cannot be one of: system, admin, consol, sysadmin, useradmin.");
            return false;
        }
        return true;
    }

    function showLoadingAnimation(form) {
        clearFormError(form);
        const loadingContainer = document.createElement("div");
        loadingContainer.className = "loading-container";
        loadingContainer.style.textAlign = "center";
        loadingContainer.style.padding = "var(--p-sp-3) 0";
        loadingContainer.style.color = "var(--p-color-text-subdued)";
        loadingContainer.style.fontSize = "var(--p-fs-body-sm)";
        loadingContainer.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin" aria-hidden="true"></i> Please wait…';
        if (form.parentNode) form.parentNode.insertBefore(loadingContainer, form);
        form.classList.add("hidden");
    }

    function showLoginRewards(data) {
        let message = "Welcome! ";
        if (data.daily_bonus > 0) message += "You earned " + data.daily_bonus + " points for your daily login. ";
        if (data.new_achievements && data.new_achievements.length === 1) {
            message += "You unlocked a new achievement: " + data.new_achievements[0] + "! ";
        } else if (data.new_achievements && data.new_achievements.length > 1) {
            message += "You unlocked " + data.new_achievements.length + " new achievements! ";
        }
        if (data.achievement_points > 0) message += "You earned " + data.achievement_points + " achievement points!";
        if (typeof showToast === 'function') showToast(message.trim(), 'success');
    }

    function attachToggle(linkId, targetFormId, otherFormId) {
        const link = document.getElementById(linkId);
        if (!link) return;
        link.addEventListener("click", function (event) {
            event.preventDefault();
            const t = document.getElementById(targetFormId);
            const o = document.getElementById(otherFormId);
            if (t) t.classList.toggle("hidden");
            if (o) o.classList.toggle("hidden");
            if (t) clearFormError(t);
            if (o) clearFormError(o);
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        const loginForm = document.getElementById("loginForm");
        const signupForm = document.getElementById("signupForm");

        attachToggle("signupLink", "signupForm", "loginForm");
        attachToggle("loginLink", "loginForm", "signupForm");

        if (loginForm) {
            loginForm.addEventListener("submit", function (event) {
                event.preventDefault();
                clearFormError(loginForm);

                const usernameEl = document.getElementById("usernameLogin");
                const passwordEl = document.getElementById("passwordLogin");
                const username = usernameEl ? usernameEl.value : "";
                const password = passwordEl ? passwordEl.value : "";

                if (validateLoginForm(loginForm, username, password)) {
                    showLoadingAnimation(loginForm);
                    handleFormSubmission(loginForm, "/login");
                }
            });
        }

        if (signupForm) {
            signupForm.addEventListener("submit", function (event) {
                event.preventDefault();
                clearFormError(signupForm);

                const u = document.getElementById("usernameSignup");
                const e = document.getElementById("emailSignup");
                const p = document.getElementById("passwordSignup");
                const c = document.getElementById("confirmPassword");
                const username = u ? u.value : "";
                const email = e ? e.value : "";
                const password = p ? p.value : "";
                const confirmPassword = c ? c.value : "";

                if (validateSignupForm(signupForm, username, password, confirmPassword)) {
                    showLoadingAnimation(signupForm);
                    handleFormSubmission(signupForm, "/signup");
                }
            });
        }
    });
})();
