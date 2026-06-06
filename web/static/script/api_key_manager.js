// API Key Management JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const apiKeyStatus = document.getElementById('api-key-status');
    const apiKeyForm = document.getElementById('api-key-form');
    const validateApiKeyForm = document.getElementById('validate-api-key-form');
    const removeApiKeyBtn = document.getElementById('remove-api-key-btn');
    const apiKeyInput = document.getElementById('api_key_input');

    // Load API key status and pool stats on page load
    loadApiKeyStatus();
    loadPoolStats();

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
                <div class="banner banner--success cluster" style="gap: var(--p-sp-3);">
                    <i class="fa-solid fa-check-circle" style="font-size: 18px;"></i>
                    <div style="flex: 1; min-width: 0;">
                        <div class="t-body t-strong">API key active</div>
                        <p class="t-body-sm t-muted" style="margin: 2px 0 0;">Using your key: <span class="t-mono">${masked_key}</span></p>
                    </div>
                    <button id="toggle-form-btn" class="btn btn--secondary btn--sm" type="button">
                        <i class="fa-solid fa-pen"></i> Change
                    </button>
                </div>
            `;

            // Show the form but hide the input initially
            apiKeyForm.hidden = false;
            apiKeyInput.hidden = true;
            removeApiKeyBtn.hidden = false;

            // Add toggle button functionality
            document.getElementById('toggle-form-btn').addEventListener('click', function() {
                if (apiKeyInput.hidden) {
                    apiKeyInput.hidden = false;
                    this.innerHTML = '<i class="fa-solid fa-xmark"></i> Cancel';
                } else {
                    apiKeyInput.hidden = true;
                    apiKeyInput.value = '';
                    this.innerHTML = '<i class="fa-solid fa-pen"></i> Change';
                }
            });

        } else if (has_api_key && !is_validated) {
            // User has an API key but it's not validated
            apiKeyStatus.innerHTML = `
                <div class="banner banner--warning cluster" style="gap: var(--p-sp-3);">
                    <i class="fa-solid fa-triangle-exclamation" style="font-size: 18px;"></i>
                    <div style="flex: 1; min-width: 0;">
                        <div class="t-body t-strong">API key not validated</div>
                        <p class="t-body-sm t-muted" style="margin: 2px 0 0;">Please validate your API key to use it.</p>
                    </div>
                </div>
            `;
            apiKeyForm.hidden = false;
            apiKeyInput.hidden = false;
            removeApiKeyBtn.hidden = false;

        } else {
            // User has no API key
            apiKeyStatus.innerHTML = `
                <div class="card card--compact card--sunken cluster" style="gap: var(--p-sp-3);">
                    <i class="fa-solid fa-key" style="color: var(--p-color-text-subdued); font-size: 18px;"></i>
                    <div style="flex: 1; min-width: 0;">
                        <span class="t-body t-strong">No API Key Set</span>
                        <p class="t-body-sm t-muted" style="margin: 2px 0 0;">Add your Gemini API key to avoid point consumption.</p>
                    </div>
                </div>
            `;
            apiKeyForm.hidden = false;
            apiKeyInput.hidden = false;
            removeApiKeyBtn.hidden = true;
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
        submitBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Validating…';
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

                // Reload status and pool stats
                await loadApiKeyStatus();
                await loadPoolStats();
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

    async function loadPoolStats() {
        try {
            const response = await fetch('/api_key/pool_stats');
            const data = await response.json();

            if (data.success) {
                updatePoolStatsDisplay(data.user_stats, data.pool_stats);
            } else {
                console.error('Failed to load pool stats:', data.error);
            }
        } catch (error) {
            console.error('Error loading pool stats:', error);
        }
    }

    function updatePoolStatsDisplay(userStats, poolStats) {
        // Update user statistics
        const userUsageCount = document.getElementById('user-usage-count');
        const userCompensation = document.getElementById('user-compensation');
        
        if (userStats.has_key) {
            userUsageCount.textContent = userStats.usage_count || 0;
            userCompensation.textContent = `${userStats.total_compensation || 0} pts`;
        } else {
            userUsageCount.textContent = 'N/A';
            userCompensation.textContent = 'N/A';
        }

        // Update pool statistics
        const poolActiveKeys = document.getElementById('pool-active-keys');
        const poolTotalUsage = document.getElementById('pool-total-usage');
        const poolAvgUsage = document.getElementById('pool-avg-usage');

        poolActiveKeys.textContent = poolStats.active_keys || 0;
        poolTotalUsage.textContent = poolStats.total_usage || 0;
        poolAvgUsage.textContent = Math.round(poolStats.average_usage || 0);
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
                await loadPoolStats();
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
        // Just route to the global toast — no separate floating widget
        if (typeof showToast === 'function') {
            showToast(message, type === 'error' ? 'error' : 'success');
        }
    }
});
