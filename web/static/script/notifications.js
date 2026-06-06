// web/static/script/notifications.js
(function () {
    'use strict';

    var ICON = {
        success: '<i class="fa-solid fa-check" aria-hidden="true"></i>',
        error:   '<i class="fa-solid fa-xmark" aria-hidden="true"></i>',
        info:    '<i class="fa-solid fa-circle-info" aria-hidden="true"></i>',
        warning: '<i class="fa-solid fa-triangle-exclamation" aria-hidden="true"></i>'
    };

    var ACTIVE = { el: null, hideAt: 0, timer: null };

    function hide() {
        if (!ACTIVE.el) return;
        ACTIVE.el.classList.remove('is-visible');
        var el = ACTIVE.el;
        setTimeout(function () {
            if (!el.classList.contains('is-visible')) {
                el.hidden = true;
                el.innerHTML = '';
            }
        }, 220);
        ACTIVE.el = null;
        if (ACTIVE.timer) { clearTimeout(ACTIVE.timer); ACTIVE.timer = null; }
    }

    function show(message, type, duration) {
        var el = document.getElementById('toast');
        if (!el) { console.error('Toast element #toast not found in DOM.'); return; }

        type = type || 'info';
        duration = (typeof duration === 'number' && duration > 0) ? duration : 3200;

        if (ACTIVE.el === el) hide();

        var allowed = ['success', 'error', 'info', 'warning'];
        if (allowed.indexOf(type) === -1) type = 'info';

        el.className = 'toast toast--' + type;
        el.innerHTML = (ICON[type] || '') + '<span class="toast__msg"></span>';
        var msg = el.querySelector('.toast__msg');
        msg.textContent = message == null ? '' : String(message);
        el.hidden = false;
        // force reflow so the transition runs
        void el.offsetWidth;
        el.classList.add('is-visible');

        ACTIVE.el = el;
        ACTIVE.hideAt = Date.now() + duration;
        ACTIVE.timer = setTimeout(hide, duration);
    }

    function showToast(message, type, duration) { show(message, type, duration); }

    function showGlobalLoader() {
        var loader = document.getElementById('global-loader-overlay');
        if (loader) loader.classList.remove('hidden');
    }
    function hideGlobalLoader() {
        var loader = document.getElementById('global-loader-overlay');
        if (loader) loader.style.display = 'none';
    }

    var APP_POPUP_ID = 'app-global-popup';

    function closeAppPopup() {
        var popup = document.getElementById(APP_POPUP_ID);
        if (popup) {
            if (popup._keydownHandler) document.removeEventListener('keydown', popup._keydownHandler);
            popup.remove();
        }
    }

    function showAppPopup(title, contentOrMessage, options) {
        closeAppPopup();
        options = options || {};
        var type = options.type || 'message';
        var buttons = options.buttons || null;
        var onConfirm = options.onConfirm || null;
        var onCancel = options.onCancel || null;
        var copyTargetText = options.copyTargetText || null;
        var size = options.size || 'md';

        var popup = document.createElement('div');
        popup.id = APP_POPUP_ID;
        popup.className = 'modal-backdrop is-open';

        var modal = document.createElement('div');
        modal.className = 'modal';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        modal.setAttribute('aria-labelledby', 'app-popup-title');
        modal.tabIndex = -1;

        if (typeof size === 'string' && (size.indexOf('vw') !== -1 || size.indexOf('%') !== -1 || size.indexOf('px') !== -1 || size.indexOf('rem') !== -1 || size.indexOf('em') !== -1)) {
            modal.style.width = size;
            modal.style.maxWidth = 'calc(100vw - 2rem)';
        } else {
            var widths = { sm: '420px', md: '520px', lg: '720px', xl: '920px', '2xl': '1140px' };
            modal.style.maxWidth = widths[size] || widths.md;
        }
        modal.style.width = '100%';
        modal.style.maxHeight = '90vh';
        modal.style.overflow = 'auto';

        var header = document.createElement('div');
        header.className = 'modal__header';
        var h = document.createElement('h2');
        h.id = 'app-popup-title';
        h.className = 'modal__title';
        h.textContent = title || '';
        header.appendChild(h);
        var closeBtn = document.createElement('button');
        closeBtn.className = 'icon-btn';
        closeBtn.setAttribute('aria-label', 'Close');
        closeBtn.innerHTML = '<i class="fa-solid fa-xmark" aria-hidden="true"></i>';
        closeBtn.onclick = closeAppPopup;
        header.appendChild(closeBtn);
        modal.appendChild(header);

        var body = document.createElement('div');
        body.className = 'modal__body';

        if (type === 'details') {
            body.style.whiteSpace = 'pre-wrap';
            body.classList.add('code-block--inline');
        }
        if (type === 'custom' || (type === 'message' && typeof contentOrMessage === 'string' && contentOrMessage.indexOf('<') !== -1)) {
            body.innerHTML = contentOrMessage;
        } else {
            body.textContent = contentOrMessage;
            if (type !== 'details' && type !== 'custom') body.style.whiteSpace = 'pre-wrap';
        }
        modal.appendChild(body);

        var footer = document.createElement('div');
        footer.className = 'modal__footer';

        function mkBtn(text, className, handler) {
            var b = document.createElement('button');
            b.className = 'btn ' + (className || 'btn--secondary');
            b.type = 'button';
            b.textContent = text;
            b.onclick = handler;
            return b;
        }

        if (type === 'message') {
            footer.appendChild(mkBtn('OK', 'btn--primary', closeAppPopup));
        } else if (type === 'confirmation') {
            footer.appendChild(mkBtn('No', 'btn--secondary', function () {
                if (onCancel) onCancel();
                closeAppPopup();
            }));
            footer.appendChild(mkBtn('Yes', 'btn--primary', function () {
                if (onConfirm) onConfirm();
                closeAppPopup();
            }));
        } else if (type === 'details') {
            footer.appendChild(mkBtn('Copy', 'btn--secondary', function () {
                var text = copyTargetText || contentOrMessage;
                navigator.clipboard.writeText(text)
                    .then(function () { showToast('Copied to clipboard!', 'success'); })
                    .catch(function () { showToast('Failed to copy.', 'error'); });
            }));
            footer.appendChild(mkBtn('Close', 'btn--primary', closeAppPopup));
        } else if (type === 'custom' && Array.isArray(buttons)) {
            buttons.forEach(function (cfg) {
                footer.appendChild(mkBtn(cfg.text || '', cfg.class || 'btn--secondary', function () {
                    if (typeof cfg.action === 'function' && cfg.action() === false) return;
                    closeAppPopup();
                }));
            });
        }

        if (footer.childNodes.length) modal.appendChild(footer);
        popup.appendChild(modal);
        document.body.appendChild(popup);

        popup.addEventListener('click', function (e) { if (e.target === popup) closeAppPopup(); });

        function onKey(e) {
            if (e.key === 'Escape') { e.preventDefault(); closeAppPopup(); }
            else if (e.key === 'Tab') {
                var f = Array.from(modal.querySelectorAll('a[href], button, textarea, input, select, [tabindex]:not([tabindex="-1"])')).filter(function (el) { return !el.hasAttribute('disabled'); });
                if (!f.length) return;
                if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus(); }
                else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
            }
        }
        document.addEventListener('keydown', onKey);
        popup._keydownHandler = onKey;
        setTimeout(function () { var f = modal.querySelector('input, textarea, button'); if (f) f.focus(); else modal.focus(); }, 0);
    }

    // Expose globals used across templates
    window.showToast = showToast;
    window.showGlobalLoader = showGlobalLoader;
    window.hideGlobalLoader = hideGlobalLoader;
    window.showAppPopup = showAppPopup;
    window.closeAppPopup = closeAppPopup;
})();
