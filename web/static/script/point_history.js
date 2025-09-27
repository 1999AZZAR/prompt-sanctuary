/**
 * Point History Modal Management
 * Handles the display and interaction of the point history modal
 */

let pointHistoryData = null;

/**
 * Show the point history modal and load data
 */
function showPointHistory() {
    const modal = document.getElementById('point-history-modal');
    if (!modal) return;
    
    // Show modal
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    
    // Load point history data
    loadPointHistory();
}

/**
 * Hide the point history modal
 */
function hidePointHistory() {
    const modal = document.getElementById('point-history-modal');
    if (!modal) return;
    
    modal.classList.add('hidden');
    document.body.style.overflow = 'auto';
}

/**
 * Load point history data from the server
 */
async function loadPointHistory() {
    const loadingElement = document.getElementById('point-history-loading');
    const itemsElement = document.getElementById('point-history-items');
    const emptyElement = document.getElementById('point-history-empty');
    
    // Show loading state
    loadingElement.classList.remove('hidden');
    itemsElement.classList.add('hidden');
    emptyElement.classList.add('hidden');
    
    try {
        const response = await fetch('/points/history');
        const data = await response.json();
        
        if (data.success) {
            pointHistoryData = data.history;
            displayPointHistory(data.history);
        } else {
            console.error('Failed to load point history:', data.error);
            showErrorState();
        }
    } catch (error) {
        console.error('Error loading point history:', error);
        showErrorState();
    }
}

/**
 * Display the point history data
 */
function displayPointHistory(history) {
    const loadingElement = document.getElementById('point-history-loading');
    const itemsElement = document.getElementById('point-history-items');
    const emptyElement = document.getElementById('point-history-empty');
    
    // Hide loading state
    loadingElement.classList.add('hidden');
    
    if (!history || history.length === 0) {
        emptyElement.classList.remove('hidden');
        return;
    }
    
    // Clear existing items
    itemsElement.innerHTML = '';
    
    // Group history by date
    const groupedHistory = groupHistoryByDate(history);
    
    // Display grouped history
    for (const [date, transactions] of Object.entries(groupedHistory)) {
        const dateGroup = createDateGroup(date, transactions);
        itemsElement.appendChild(dateGroup);
    }
    
    itemsElement.classList.remove('hidden');
}

/**
 * Group history items by date
 */
function groupHistoryByDate(history) {
    const grouped = {};
    
    history.forEach(item => {
        const date = new Date(item.created_at).toDateString();
        if (!grouped[date]) {
            grouped[date] = [];
        }
        grouped[date].push(item);
    });
    
    return grouped;
}

/**
 * Create a date group element
 */
function createDateGroup(date, transactions) {
    const dateGroup = document.createElement('div');
    dateGroup.className = 'mb-6';
    
    // Date header
    const dateHeader = document.createElement('div');
    dateHeader.className = 'flex items-center space-x-2 mb-3 pb-2 border-b border-gray-200';
    
    const dateIcon = document.createElement('i');
    dateIcon.className = 'fas fa-calendar-day text-blue-500';
    
    const dateText = document.createElement('span');
    dateText.className = 'font-medium text-gray-700';
    dateText.textContent = formatDateHeader(date);
    
    dateHeader.appendChild(dateIcon);
    dateHeader.appendChild(dateText);
    
    // Transactions list
    const transactionsList = document.createElement('div');
    transactionsList.className = 'space-y-3';
    
    transactions.forEach(transaction => {
        const transactionElement = createTransactionElement(transaction);
        transactionsList.appendChild(transactionElement);
    });
    
    dateGroup.appendChild(dateHeader);
    dateGroup.appendChild(transactionsList);
    
    return dateGroup;
}

/**
 * Create a transaction element
 */
function createTransactionElement(transaction) {
    const element = document.createElement('div');
    element.className = 'flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors';
    
    // Left side - icon and description
    const leftSide = document.createElement('div');
    leftSide.className = 'flex items-center space-x-3 flex-1';
    
    // Icon based on source
    const icon = document.createElement('i');
    icon.className = getSourceIcon(transaction.source);
    
    // Description
    const description = document.createElement('div');
    const descriptionText = document.createElement('p');
    descriptionText.className = 'font-medium text-gray-900';
    descriptionText.textContent = transaction.description || getDefaultDescription(transaction.source);
    
    const sourceText = document.createElement('p');
    sourceText.className = 'text-sm text-gray-500';
    sourceText.textContent = getSourceDisplayName(transaction.source);
    
    description.appendChild(descriptionText);
    description.appendChild(sourceText);
    
    leftSide.appendChild(icon);
    leftSide.appendChild(description);
    
    // Right side - points and status
    const rightSide = document.createElement('div');
    rightSide.className = 'flex items-center space-x-3';
    
    // Points change
    const pointsChange = document.createElement('div');
    pointsChange.className = 'text-right';
    
    const pointsText = document.createElement('p');
    pointsText.className = `font-semibold ${transaction.points > 0 ? 'text-green-600' : 'text-red-600'}`;
    pointsText.textContent = `${transaction.points > 0 ? '+' : ''}${transaction.points.toFixed(1)} pts`;
    
    const balanceText = document.createElement('p');
    balanceText.className = 'text-xs text-gray-500';
    balanceText.textContent = `${transaction.points_before.toFixed(1)} → ${transaction.points_after.toFixed(1)}`;
    
    pointsChange.appendChild(pointsText);
    pointsChange.appendChild(balanceText);
    
    // Expiration status
    const expirationStatus = createExpirationStatus(transaction);
    
    rightSide.appendChild(pointsChange);
    rightSide.appendChild(expirationStatus);
    
    element.appendChild(leftSide);
    element.appendChild(rightSide);
    
    return element;
}

/**
 * Create expiration status element
 */
function createExpirationStatus(transaction) {
    const statusElement = document.createElement('div');
    statusElement.className = 'text-right';
    
    if (transaction.expires_at) {
        const expirationDate = new Date(transaction.expires_at);
        const now = new Date();
        const daysLeft = Math.ceil((expirationDate - now) / (1000 * 60 * 60 * 24));
        
        if (daysLeft > 0) {
            statusElement.innerHTML = `
                <div class="flex items-center space-x-1 text-xs text-blue-600">
                    <i class="fas fa-clock"></i>
                    <span>${daysLeft} days left</span>
                </div>
            `;
        } else if (transaction.is_expired) {
            statusElement.innerHTML = `
                <div class="flex items-center space-x-1 text-xs text-gray-500">
                    <i class="fas fa-hourglass-end"></i>
                    <span>Expired</span>
                </div>
            `;
        }
    } else {
        statusElement.innerHTML = `
            <div class="flex items-center space-x-1 text-xs text-green-600">
                <i class="fas fa-infinity"></i>
                <span>Never expires</span>
            </div>
        `;
    }
    
    return statusElement;
}

/**
 * Get icon class for a source
 */
function getSourceIcon(source) {
    const iconMap = {
        'original': 'fas fa-star text-yellow-500',
        'daily_login': 'fas fa-calendar-check text-blue-500',
        'achievement': 'fas fa-trophy text-purple-500',
        'api_key_add': 'fas fa-key text-green-500',
        'api_key_usage': 'fas fa-coins text-orange-500',
        'prompt_share': 'fas fa-share-alt text-indigo-500',
        'prompt_unshare': 'fas fa-share-alt-slash text-red-500',
        'prompt_generation': 'fas fa-magic text-blue-500',
        'advance_generation': 'fas fa-wand-magic-sparkles text-purple-500',
        'api_key_remove': 'fas fa-trash text-red-500',
        'legacy': 'fas fa-history text-gray-500'
    };
    
    return iconMap[source] || 'fas fa-coins text-gray-500';
}

/**
 * Get display name for a source
 */
function getSourceDisplayName(source) {
    const nameMap = {
        'original': 'Initial Points',
        'daily_login': 'Daily Login Bonus',
        'achievement': 'Achievement Reward',
        'api_key_add': 'API Key Validation',
        'api_key_usage': 'API Key Usage Compensation',
        'prompt_share': 'Prompt Sharing',
        'prompt_unshare': 'Prompt Unsharing',
        'prompt_generation': 'Prompt Generation',
        'advance_generation': 'Advanced Prompt Generation',
        'api_key_remove': 'API Key Removal',
        'legacy': 'Legacy System'
    };
    
    return nameMap[source] || source;
}

/**
 * Get default description for a source
 */
function getDefaultDescription(source) {
    const descriptionMap = {
        'original': 'Initial account points',
        'daily_login': 'Daily login reward',
        'achievement': 'Achievement unlocked',
        'api_key_add': 'API key validated',
        'api_key_usage': 'System used your API key',
        'prompt_share': 'Shared prompt to community',
        'prompt_unshare': 'Unshared prompt',
        'prompt_generation': 'Generated basic prompt',
        'advance_generation': 'Generated advanced prompt',
        'api_key_remove': 'Removed API key',
        'legacy': 'Legacy point operation'
    };
    
    return descriptionMap[source] || 'Point transaction';
}

/**
 * Format date header
 */
function formatDateHeader(dateString) {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    if (date.toDateString() === today.toDateString()) {
        return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
        return 'Yesterday';
    } else {
        return date.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }
}

/**
 * Show error state
 */
function showErrorState() {
    const loadingElement = document.getElementById('point-history-loading');
    const itemsElement = document.getElementById('point-history-items');
    const emptyElement = document.getElementById('point-history-empty');
    
    loadingElement.classList.add('hidden');
    itemsElement.classList.add('hidden');
    
    // Modify empty state to show error
    const emptyIcon = emptyElement.querySelector('i');
    const emptyText = emptyElement.querySelector('p');
    
    emptyIcon.className = 'fas fa-exclamation-triangle text-4xl text-red-300 mb-4';
    emptyText.textContent = 'Failed to load point history. Please try again.';
    
    emptyElement.classList.remove('hidden');
}

/**
 * Close modal when clicking outside
 */
document.addEventListener('click', function(event) {
    const modal = document.getElementById('point-history-modal');
    if (modal && !modal.classList.contains('hidden')) {
        if (event.target === modal) {
            hidePointHistory();
        }
    }
});

/**
 * Close modal with Escape key
 */
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        hidePointHistory();
    }
});

// Export functions for global access
window.showPointHistory = showPointHistory;
window.hidePointHistory = hidePointHistory;
