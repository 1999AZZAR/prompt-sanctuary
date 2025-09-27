// Global API Key Status Indicator

document.addEventListener('DOMContentLoaded', function() {
    const apiKeyIndicator = document.getElementById('api-key-indicator');
    
    if (apiKeyIndicator) {
        updateApiKeyIndicator();
    }
});

async function updateApiKeyIndicator() {
    const apiKeyIndicator = document.getElementById('api-key-indicator');
    
    if (!apiKeyIndicator) {
        return;
    }

    try {
        const response = await fetch('/api_key/status');
        const data = await response.json();

        if (data.success && data.has_api_key && data.is_validated) {
            apiKeyIndicator.style.display = 'block';
        } else {
            apiKeyIndicator.style.display = 'none';
        }
    } catch (error) {
        console.error('Error updating API key indicator:', error);
        apiKeyIndicator.style.display = 'none';
    }
}
