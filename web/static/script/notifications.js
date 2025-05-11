// web/static/script/notifications.js
function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container');
    if (!container) {
        console.error('Toast container not found!');
        return;
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    // Animate in
    setTimeout(() => {
        toast.classList.add('show');
    }, 10); // Small delay to ensure CSS transition is applied

    // Auto-dismiss
    setTimeout(() => {
        toast.classList.remove('show');
        // Remove from DOM after animation
        setTimeout(() => {
            if (toast.parentNode === container) {
                 container.removeChild(toast);
            }
        }, 300); // Matches transition duration
    }, duration);
} 

function showGlobalLoader() {
    const loader = document.getElementById('global-loader-overlay');
    if (loader) {
        loader.classList.remove('hidden');
    }
}

function hideGlobalLoader() {
    const loader = document.getElementById('global-loader-overlay');
    if (loader) {
        loader.style.display = 'none';
    }
}

// NEW GLOBAL POPUP SYSTEM

const APP_POPUP_ID = 'app-global-popup';

/**
 * Displays a global application popup with specified title, content, and buttons.
 * Ensures only one popup is visible at a time.
 *
 * @param {string} title - The title of the popup.
 * @param {string} contentOrMessage - The main content of the popup (can be plain text or HTML).
 * @param {object} options - Configuration options for the popup.
 * @param {'message' | 'confirmation' | 'details' | 'custom'} [options.type='message'] - Type of popup:
 *    - 'message': Displays contentOrMessage as text with an "OK" button.
 *    - 'confirmation': Displays contentOrMessage as text with "Yes" and "No" buttons. Requires onConfirm.
 *    - 'details': Displays contentOrMessage as text (meant for detailed view) with "Copy" (copies contentOrMessage) and "Close" buttons.
 *    - 'custom': Displays contentOrMessage as HTML. Requires options.buttons array.
 * @param {Array<{text: string, class?: string, action: function}>} [options.buttons=null] - Custom buttons for 'custom' type.
 * @param {function} [options.onConfirm=null] - Callback for "Yes" button in 'confirmation' type.
 * @param {function} [options.onCancel=null] - Callback for "No" button in 'confirmation' type.
 * @param {string} [options.copyTargetText=null] - Explicit text to copy for 'details' or 'custom' type if contentOrMessage is HTML and copy is needed for a part of it. If null and type is 'details', contentOrMessage is copied.
 */
function showAppPopup(title, contentOrMessage, options = {}) {
    closeAppPopup(); // Close any existing popup first

    const {
        type = 'message',
        buttons = null,
        onConfirm = null,
        onCancel = null,
        copyTargetText = null,
        size = 'md' // NEW: Add size option, default to 'md'
    } = options;

    const popup = document.createElement('div');
    popup.id = APP_POPUP_ID;
    popup.className = 'fixed inset-0 flex items-center justify-center glass z-50 p-4';

    const popupContent = document.createElement('div');
    // Dynamically set max-width based on size option
    let maxWidthClass = 'max-w-md'; // Default
    if (size === 'sm') maxWidthClass = 'max-w-sm'; // Smallest
    if (size === 'lg') maxWidthClass = 'max-w-lg';   // Larger
    if (size === 'xl') maxWidthClass = 'max-w-xl'; // Even larger
    if (size === '2xl') maxWidthClass = 'max-w-2xl'; // Largest standard

    popupContent.className = `glass p-6 md:p-8 rounded-lg w-full ${maxWidthClass} text-white relative shadow-xl`;
    popupContent.style.maxHeight = '90vh';
    popupContent.style.overflowY = 'auto';
    popupContent.style.overflowX = 'hidden';
    // Add custom scrollbar styling if desired (can be a global CSS rule too)
    popupContent.classList.add('custom-scrollbar');


    const closeIcon = document.createElement('button');
    closeIcon.className = 'absolute top-3 right-3 md:top-4 md:right-4 text-white text-2xl leading-none hover:text-gray-300 z-10';
    closeIcon.innerHTML = '&times;';
    closeIcon.onclick = () => closeAppPopup();
    popupContent.appendChild(closeIcon);

    const popupTitle = document.createElement('h2');
    popupTitle.className = 'text-xl md:text-2xl font-bold mb-4 pr-8'; // Added padding-right for close icon
    popupTitle.textContent = title;
    popupContent.appendChild(popupTitle);

    const messageArea = document.createElement('div');
    messageArea.className = 'text-base md:text-lg text-gray-200 mb-6 break-words'; // Default

    if (type === 'details') {
        messageArea.classList.remove('text-gray-200');
        messageArea.classList.add('text-white'); // Brighter text for details view on glass
        messageArea.style.whiteSpace = 'pre-wrap'; // Ensure pre-wrap for prompt text in details
    }

     if (type === 'custom' || type === 'message' && contentOrMessage.includes('<')) { // if custom or message might be html
        messageArea.innerHTML = contentOrMessage;
    } else {
        messageArea.textContent = contentOrMessage;
        // pre-wrap for 'details' is now handled above, ensure others that need it get it
        if (type !== 'details' && type !== 'custom') { 
            messageArea.style.whiteSpace = 'pre-wrap';
        }
    }
    popupContent.appendChild(messageArea);

    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'flex flex-col sm:flex-row justify-end space-y-2 sm:space-y-0 sm:space-x-3'; // Responsive buttons

    // Default button styling
    const baseButtonClass = 'px-5 py-2.5 rounded-lg transition duration-200 text-sm font-medium w-full sm:w-auto';
    const primaryButtonClass = `bg-blue-500 hover:bg-blue-600 text-white ${baseButtonClass}`;
    const secondaryButtonClass = `bg-gray-600 hover:bg-gray-700 text-white ${baseButtonClass}`;


    if (type === 'message') {
        const okButton = document.createElement('button');
        okButton.className = primaryButtonClass;
        okButton.textContent = 'OK';
        okButton.onclick = () => closeAppPopup();
        buttonContainer.appendChild(okButton);
    } else if (type === 'confirmation') {
        const yesButton = document.createElement('button');
        yesButton.className = primaryButtonClass;
        yesButton.textContent = 'Yes';
        yesButton.onclick = () => {
            if (onConfirm) onConfirm();
            closeAppPopup();
        };

        const noButton = document.createElement('button');
        noButton.className = secondaryButtonClass;
        noButton.textContent = 'No';
        noButton.onclick = () => {
            if (onCancel) onCancel();
            closeAppPopup();
        };
        buttonContainer.appendChild(noButton); // No typically first on right
        buttonContainer.appendChild(yesButton);
    } else if (type === 'details') {
        const copyBtn = document.createElement('button');
        copyBtn.className = primaryButtonClass;
        copyBtn.textContent = 'Copy';
        copyBtn.onclick = () => {
            const textToCopy = copyTargetText || contentOrMessage;
            navigator.clipboard.writeText(textToCopy)
                .then(() => showToast('Copied to clipboard!', 'success'))
                .catch(err => {
                    console.error('Failed to copy:', err);
                    showToast('Failed to copy.', 'error');
                });
        };
        const closeBtn2 = document.createElement('button');
        closeBtn2.className = secondaryButtonClass;
        closeBtn2.textContent = 'Close';
        closeBtn2.onclick = () => closeAppPopup();
        buttonContainer.appendChild(copyBtn);
        buttonContainer.appendChild(closeBtn2);
    } else if (type === 'custom' && Array.isArray(buttons)) {
        buttons.forEach(btnConfig => {
            const button = document.createElement('button');
            button.className = btnConfig.class || primaryButtonClass; // Default to primary if no class
            // Ensure base classes are there if a custom class is provided, or make btnConfig.class additive
            if (!btnConfig.class?.includes('px-5')) { // basic check
                 button.className = `${baseButtonClass} ${btnConfig.class || primaryButtonClass}`;
            } else {
                 button.className = btnConfig.class;
            }

            button.textContent = btnConfig.text;
            button.onclick = () => {
                // Allow action to prevent close by returning false
                if (btnConfig.action() !== false) {
                    closeAppPopup();
                }
            };
            buttonContainer.appendChild(button);
        });
    }

    if (buttonContainer.hasChildNodes()) {
        popupContent.appendChild(buttonContainer);
    }

    popup.appendChild(popupContent);
    document.body.appendChild(popup);
    popupContent.focus(); // For accessibility, focus the popup content
}

function closeAppPopup() {
    const popup = document.getElementById(APP_POPUP_ID);
    if (popup) {
        popup.remove();
    }
} 