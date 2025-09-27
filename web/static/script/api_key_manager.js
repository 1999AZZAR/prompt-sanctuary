// API Key Management JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const apiKeyStatus = document.getElementById('api-key-status');
    const apiKeyForm = document.getElementById('api-key-form');
    const validateApiKeyForm = document.getElementById('validate-api-key-form');
    const removeApiKeyBtn = document.getElementById('remove-api-key-btn');
    const apiKeyInput = document.getElementById('api_key_input');

    // Load API key status on page load
    loadApiKeyStatus();

    // Handle API key validation form submission
    validateApiKeyForm.addEventListener('submit', function(e) {
        e.preventDefault();
        validateApiKey();
    });

    // Handle remove API key button
    removeApiKeyBtn.addEventListener('click', function() {
        removeApiKey();
    });

    async function loadApiKeyStatus() {
        try {
            const response = await fetch('/api_key/status');
            const data = await response.json();

            if (data.success) {
                updateApiKeyStatusDisplay(data);
            } else {
                showError('Failed to load API key status');
            }
        } catch (error) {
            console.error('Error loading API key status:', error);
            showError('Failed to load API key status');
        }
    }

    function updateApiKeyStatusDisplay(data) {
        const { has_api_key, is_validated, masked_key } = data;

        if (has_api_key && is_validated) {
            // User has a validated API key
            apiKeyStatus.innerHTML = `
                <div class="flex items-center space-x-2 p-3 bg-green-50 rounded-lg border border-green-200">
                    <i class="fas fa-check-circle text-green-500"></i>
                    <div class="flex-1">
                        <span class="text-sm font-medium text-green-700">API Key Active</span>
                        <p class="text-xs text-green-600">Using your key: ${masked_key}</p>
                    </div>
                    <button id="toggle-form-btn" class="text-xs bg-green-100 text-green-700 px-2 py-1 rounded hover:bg-green-200 transition-colors">
                        <i class="fas fa-edit mr-1"></i>Change
                    </button>
                </div>
            `;

            // Show the form but hide the input initially
            apiKeyForm.style.display = 'block';
            apiKeyInput.style.display = 'none';
            removeApiKeyBtn.style.display = 'inline-block';

            // Add toggle button functionality
            document.getElementById('toggle-form-btn').addEventListener('click', function() {
                if (apiKeyInput.style.display === 'none') {
                    apiKeyInput.style.display = 'block';
                    this.innerHTML = '<i class="fas fa-times mr-1"></i>Cancel';
                } else {
                    apiKeyInput.style.display = 'none';
                    apiKeyInput.value = '';
                    this.innerHTML = '<i class="fas fa-edit mr-1"></i>Change';
                }
            });

        } else if (has_api_key && !is_validated) {
            // User has an API key but it's not validated
            apiKeyStatus.innerHTML = `
                <div class="flex items-center space-x-2 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                    <i class="fas fa-exclamation-triangle text-yellow-500"></i>
                    <div class="flex-1">
                        <span class="text-sm font-medium text-yellow-700">API Key Not Validated</span>
                        <p class="text-xs text-yellow-600">Please validate your API key to use it</p>
                    </div>
                </div>
            `;
            apiKeyForm.style.display = 'block';
            apiKeyInput.style.display = 'block';
            removeApiKeyBtn.style.display = 'inline-block';

        } else {
            // User has no API key
            apiKeyStatus.innerHTML = `
                <div class="flex items-center space-x-2 p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <i class="fas fa-key text-slate-500"></i>
                    <div class="flex-1">
                        <span class="text-sm font-medium text-slate-700">No API Key Set</span>
                        <p class="text-xs text-slate-600">Add your Gemini API key to avoid point consumption</p>
                    </div>
                </div>
            `;
            apiKeyForm.style.display = 'block';
            apiKeyInput.style.display = 'block';
            removeApiKeyBtn.style.display = 'none';
        }
    }

    async function validateApiKey() {
        const formData = new FormData(validateApiKeyForm);
        const apiKey = formData.get('api_key');

        if (!apiKey || !apiKey.trim()) {
            showError('Please enter an API key');
            return;
        }

        // Show loading state
        const submitBtn = validateApiKeyForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Validating...';
        submitBtn.disabled = true;

        try {
            const response = await fetch('/api_key/validate', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                showSuccess(data.message);
                
                // Show points awarded if applicable
                if (data.points_awarded) {
                    showNotification(`+${data.points_awarded} points awarded!`, 'success');
                }

                // Show achievements if any
                if (data.new_achievements && data.new_achievements.length > 0) {
                    showNotification(`New achievement unlocked: ${data.new_achievements.join(', ')}`, 'achievement');
                }

                // Reload status
                await loadApiKeyStatus();
                apiKeyInput.value = '';
            } else {
                showError(data.error || 'Failed to validate API key');
            }
        } catch (error) {
            console.error('Error validating API key:', error);
            showError('Failed to validate API key');
        } finally {
            // Reset button state
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }

    async function removeApiKey() {
        if (!confirm('Are you sure you want to remove your API key? You will start consuming points again.')) {
            return;
        }

        const formData = new FormData();
        formData.append('csrf_token', validateApiKeyForm.querySelector('input[name="csrf_token"]').value);

        try {
            const response = await fetch('/api_key/remove', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                showSuccess(data.message);
                await loadApiKeyStatus();
                apiKeyInput.value = '';
            } else {
                showError(data.error || 'Failed to remove API key');
            }
        } catch (error) {
            console.error('Error removing API key:', error);
            showError('Failed to remove API key');
        }
    }

    function showSuccess(message) {
        showNotification(message, 'success');
    }

    function showError(message) {
        showNotification(message, 'error');
    }

    function showNotification(message, type) {
        // Remove any existing notifications
        const existingNotifications = document.querySelectorAll('.api-key-notification');
        existingNotifications.forEach(notification => notification.remove());

        // Create new notification
        const notification = document.createElement('div');
        notification.className = `api-key-notification fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm transition-all duration-300 transform translate-x-full`;
        
        if (type === 'success') {
            notification.className += ' bg-green-500 text-white';
            notification.innerHTML = `<i class="fas fa-check-circle mr-2"></i>${message}`;
        } else if (type === 'error') {
            notification.className += ' bg-red-500 text-white';
            notification.innerHTML = `<i class="fas fa-exclamation-circle mr-2"></i>${message}`;
        } else if (type === 'achievement') {
            notification.className += ' bg-yellow-500 text-white';
            notification.innerHTML = `<i class="fas fa-trophy mr-2"></i>${message}`;
        }

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);

        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }
});
