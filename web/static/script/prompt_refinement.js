// Prompt refinement functionality for generated prompts
class PromptRefinement {
    constructor() {
        this.thresholds = {
            short: 100,    // Show "Elaborate" button if < 100 chars
            long: 1000,    // Show "Shorten" button if > 1000 chars
            veryLong: 1500 // Show warning if > 1500 chars
        };
        
        this.init();
    }
    
    init() {
        console.log('Prompt refinement script loaded');
        // No need for input field listeners since we're working with generated prompts
    }
    
    showRefinementButtons() {
        const resultSection = document.getElementById('resultSection');
        const responseDiv = document.getElementById('response');
        
        if (!resultSection || !responseDiv) {
            // Result section or response div not found (normal for pages without refinement)
            return;
        }
        
        // Only show buttons if result section is visible and has content
        if (resultSection.classList.contains('hidden') || !responseDiv.textContent.trim()) {
            this.hideRefinementButtons();
            return;
        }
        
        const promptText = this.extractPromptText(responseDiv);
        const length = promptText.length;
        
        console.log(`Generated prompt length: ${length} characters`);
        
        const shortenBtn = document.getElementById('shorten-prompt-btn');
        const elaborateBtn = document.getElementById('elaborate-prompt-btn');
        
        if (!shortenBtn || !elaborateBtn) {
            // Refinement buttons not found (normal for pages without refinement)
            return;
        }
        
        // Show appropriate buttons based on length
        if (length < this.thresholds.short) {
            // Short prompt - show elaborate button
            elaborateBtn.classList.remove('hidden');
            shortenBtn.classList.add('hidden');
            console.log('Showing elaborate button');
        } else if (length > this.thresholds.long) {
            // Long prompt - show shorten button
            shortenBtn.classList.remove('hidden');
            elaborateBtn.classList.add('hidden');
            console.log('Showing shorten button');
        } else {
            // Medium length - show both buttons
            shortenBtn.classList.remove('hidden');
            elaborateBtn.classList.remove('hidden');
            console.log('Showing both buttons');
        }
        
        // Update status
        this.updateRefinementStatus(length);
    }
    
    hideRefinementButtons() {
        const shortenBtn = document.getElementById('shorten-prompt-btn');
        const elaborateBtn = document.getElementById('elaborate-prompt-btn');
        const statusDiv = document.getElementById('refinement-status');
        
        if (shortenBtn) shortenBtn.classList.add('hidden');
        if (elaborateBtn) elaborateBtn.classList.add('hidden');
        if (statusDiv) statusDiv.classList.add('hidden');
    }
    
    updateRefinementStatus(length) {
        const statusDiv = document.getElementById('refinement-status');
        if (!statusDiv) return;
        
        let message = '';
        let className = 'text-gray-500';
        
        if (length < this.thresholds.short) {
            message = `${length} characters - Consider elaborating for more detail`;
            className = 'text-blue-500';
        } else if (length > this.thresholds.veryLong) {
            message = `${length} characters - Very long prompt, consider shortening`;
            className = 'text-orange-600';
        } else if (length > this.thresholds.long) {
            message = `${length} characters - Long prompt, can be shortened`;
            className = 'text-yellow-600';
        } else {
            message = `${length} characters - Good prompt length`;
            className = 'text-green-500';
        }
        
        statusDiv.textContent = message;
        statusDiv.className = `text-sm mt-3 ${className}`;
        statusDiv.classList.remove('hidden');
    }
    
    extractPromptText(responseDiv) {
        // Extract text content from the response div, handling various HTML structures
        let text = '';
        
        // If response div contains HTML, extract text content
        if (responseDiv.innerHTML) {
            // Create a temporary div to strip HTML tags
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = responseDiv.innerHTML;
            text = tempDiv.textContent || tempDiv.innerText || '';
        } else {
            text = responseDiv.textContent || '';
        }
        
        return text.trim();
    }
    
    async refineGeneratedPrompt(action) {
        const responseDiv = document.getElementById('response');
        const statusDiv = document.getElementById('refinement-status');
        
        if (!responseDiv || !responseDiv.textContent.trim()) {
            showToast('No generated prompt to refine.', 'warning');
            return;
        }
        
        const originalText = this.extractPromptText(responseDiv);
        
        if (!originalText) {
            showToast('No prompt text found to refine.', 'error');
            return;
        }
        
        try {
            // Show loading state
            this.showRefinementStatus('Processing refinement...', 'loading');
            
            // Disable buttons during processing
            this.setButtonsDisabled(true);
            
            // Call the refinement API
            const refinedText = await this.callRefinementAPI(originalText, action);
            
            if (refinedText && refinedText !== originalText) {
                // Update the response div with refined text
                responseDiv.innerHTML = `<div class="rendered">${refinedText.replace(/\n/g, '<br>')}</div>`;
                
                this.showRefinementStatus(`Prompt ${action}ed successfully!`, 'success');
                showToast(`Prompt ${action}ed successfully!`, 'success');
                
                // Re-evaluate which buttons to show
                setTimeout(() => this.showRefinementButtons(), 100);
            } else {
                this.showRefinementStatus('No changes needed or refinement failed', 'error');
                showToast('Refinement completed but no changes were made.', 'info');
            }
        } catch (error) {
            console.error('Refinement error:', error);
            this.showRefinementStatus('Refinement failed. Please try again.', 'error');
            showToast('Failed to refine prompt. Please try again.', 'error');
        } finally {
            this.setButtonsDisabled(false);
        }
    }
    
    async callRefinementAPI(text, action) {
        const formData = new FormData();
        formData.append('text', text);
        formData.append('action', action);
        
        const response = await fetch('/refine_prompt', {
            method: 'POST',
            headers: window.CSRF.getFormHeaders(),
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.text();
        return result.trim();
    }
    
    showRefinementStatus(message, type) {
        const statusDiv = document.getElementById('refinement-status');
        if (!statusDiv) return;
        
        statusDiv.textContent = message;
        statusDiv.className = `text-sm mt-3 refinement-status ${type}`;
        statusDiv.classList.remove('hidden');
        
        // Auto-hide success/error messages after 3 seconds
        if (type === 'success' || type === 'error') {
            setTimeout(() => {
                statusDiv.classList.add('hidden');
            }, 3000);
        }
    }
    
    setButtonsDisabled(disabled) {
        const shortenBtn = document.getElementById('shorten-prompt-btn');
        const elaborateBtn = document.getElementById('elaborate-prompt-btn');
        
        [shortenBtn, elaborateBtn].forEach(btn => {
            if (btn) {
                btn.disabled = disabled;
                btn.style.opacity = disabled ? '0.5' : '1';
                btn.style.cursor = disabled ? 'not-allowed' : 'pointer';
            }
        });
    }
}

// Global function for onclick handlers
function refineGeneratedPrompt(action) {
    if (window.promptRefinement) {
        window.promptRefinement.refineGeneratedPrompt(action);
    }
}

// Function to show refinement buttons (called after generating a prompt)
function showRefinementButtons() {
    if (window.promptRefinement) {
        // Small delay to ensure the result section is fully rendered
        setTimeout(() => {
            window.promptRefinement.showRefinementButtons();
        }, 500);
    }
}

// Function to hide refinement buttons
function hideRefinementButtons() {
    if (window.promptRefinement) {
        window.promptRefinement.hideRefinementButtons();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.promptRefinement = new PromptRefinement();
});

// Monitor for changes in the result section
const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
            const target = mutation.target;
            if (target.id === 'resultSection') {
                if (target.classList.contains('hidden')) {
                    hideRefinementButtons();
                } else {
                    showRefinementButtons();
                }
            }
        }
    });
});

// Start observing when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const resultSection = document.getElementById('resultSection');
    if (resultSection) {
        observer.observe(resultSection, { attributes: true });
    }
});