// web/static/script/point_history.js
(function () {
    'use strict';

    var ICON = {
        original:           'fa-star',
        daily_login:        'fa-calendar-check',
        achievement:        'fa-trophy',
        api_key_add:        'fa-key',
        api_key_usage:      'fa-coins',
        prompt_share:       'fa-share-nodes',
        prompt_unshare:     'fa-share-from-square',
        prompt_generation:  'fa-wand-magic-sparkles',
        advance_generation: 'fa-sliders',
        api_key_remove:     'fa-trash',
        legacy:             'fa-clock-rotate-left'
    };

    var DISPLAY_NAME = {
        original:           'Initial Points',
        daily_login:        'Daily Login Bonus',
        achievement:        'Achievement Reward',
        api_key_add:        'API Key Validation',
        api_key_usage:      'API Key Usage Compensation',
        prompt_share:       'Prompt Sharing',
        prompt_unshare:     'Prompt Unsharing',
        prompt_generation:  'Prompt Generation',
        advance_generation: 'Advanced Prompt Generation',
        api_key_remove:     'API Key Removal',
        legacy:             'Legacy System'
    };

    var DEFAULT_DESC = {
        original:           'Initial account points',
        daily_login:        'Daily login reward',
        achievement:        'Achievement unlocked',
        api_key_add:        'API key validated',
        api_key_usage:      'System used your API key',
        prompt_share:       'Shared prompt to community',
        prompt_unshare:     'Unshared prompt',
        prompt_generation:  'Generated basic prompt',
        advance_generation: 'Generated advanced prompt',
        api_key_remove:     'Removed API key',
        legacy:             'Legacy point operation'
    };

    function escapeHtml(str) {
        if (str == null) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function setVisible(el, visible) {
        if (!el) return;
        if (visible) el.removeAttribute('hidden');
        else el.setAttribute('hidden', '');
    }

    function formatDateHeader(dateStr) {
        var d = new Date(dateStr);
        var now = new Date();
        var yesterday = new Date(now);
        yesterday.setDate(yesterday.getDate() - 1);
        if (d.toDateString() === now.toDateString()) return 'Today';
        if (d.toDateString() === yesterday.toDateString()) return 'Yesterday';
        return d.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    }

    function buildExpiration(transaction) {
        if (!transaction.expires_at) {
            return '<span class="badge badge--success"><i class="fa-solid fa-infinity"></i> Never</span>';
        }
        var exp = new Date(transaction.expires_at);
        var now = new Date();
        var daysLeft = Math.ceil((exp - now) / (1000 * 60 * 60 * 24));
        if (daysLeft > 0) {
            return '<span class="badge"><i class="fa-solid fa-clock"></i> ' + daysLeft + 'd</span>';
        }
        return '<span class="badge badge--critical"><i class="fa-solid fa-hourglass-end"></i> Expired</span>';
    }

    function buildTransaction(transaction) {
        var icon = ICON[transaction.source] || 'fa-coins';
        var source = DISPLAY_NAME[transaction.source] || (transaction.source || 'Transaction');
        var desc = transaction.description || DEFAULT_DESC[transaction.source] || 'Point transaction';
        var pts = Number(transaction.points || 0);
        var ptsStr = (pts > 0 ? '+' : '') + pts.toFixed(1) + ' pts';
        var ptsClass = pts > 0 ? 't-accent' : (pts < 0 ? '' : 't-muted');
        var ptsStyle = pts < 0 ? 'color: var(--p-color-critical);' : '';
        var before = transaction.points_before != null ? Number(transaction.points_before).toFixed(1) : '—';
        var after = transaction.points_after != null ? Number(transaction.points_after).toFixed(1) : '—';
        var color = icon === 'fa-trophy' ? 'var(--p-color-warning)' : 'var(--p-color-primary)';

        return '' +
            '<div class="card card--compact" style="background: var(--p-color-surface-sunken); margin: 0;">' +
            '  <div class="cluster" style="align-items: center; gap: var(--p-sp-3);">' +
            '    <div style="width: 32px; height: 32px; flex-shrink: 0; display: inline-flex; align-items: center; justify-content: center; background: var(--p-color-surface); border: var(--p-border-hair); border-radius: var(--p-r-2); color: ' + color + ';">' +
            '      <i class="fa-solid ' + icon + '"></i>' +
            '    </div>' +
            '    <div style="min-width: 0; flex: 1;">' +
            '      <p class="t-body" style="margin: 0; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">' + escapeHtml(desc) + '</p>' +
            '      <p class="t-body-sm t-muted" style="margin: 2px 0 0;">' + escapeHtml(source) + '</p>' +
            '    </div>' +
            '    <div style="text-align: right; flex-shrink: 0;">' +
            '      <p class="t-mono" style="margin: 0; font-weight: 600; ' + ptsStyle + '">' + escapeHtml(ptsStr) + '</p>' +
            '      <p class="t-body-sm t-muted" style="margin: 2px 0 0;">' + escapeHtml(before) + ' → ' + escapeHtml(after) + '</p>' +
            '    </div>' +
            '    <div style="flex-shrink: 0;">' + buildExpiration(transaction) + '</div>' +
            '  </div>' +
            '</div>';
    }

    function buildDateGroup(date, transactions) {
        var html = '' +
            '<div style="margin-bottom: var(--p-sp-5);">' +
            '  <div class="cluster" style="gap: var(--p-sp-2); margin-bottom: var(--p-sp-2); padding-bottom: var(--p-sp-2); border-bottom: var(--p-border-rule);">' +
            '    <i class="fa-solid fa-calendar-day" style="color: var(--p-color-interactive); font-size: 14px;"></i>' +
            '    <span class="t-body-sm" style="font-weight: 600; color: var(--p-color-text);">' + escapeHtml(formatDateHeader(date)) + '</span>' +
            '  </div>' +
            '  <div class="stack--sm">';
        for (var i = 0; i < transactions.length; i++) {
            html += buildTransaction(transactions[i]);
        }
        html += '  </div></div>';
        return html;
    }

    function groupByDate(history) {
        var groups = {};
        for (var i = 0; i < history.length; i++) {
            var key = new Date(history[i].created_at).toDateString();
            if (!groups[key]) groups[key] = [];
            groups[key].push(history[i]);
        }
        return groups;
    }

    function showError() {
        var loading = document.getElementById('point-history-loading');
        var items = document.getElementById('point-history-items');
        var empty = document.getElementById('point-history-empty');
        setVisible(loading, false);
        setVisible(items, false);
        if (empty) {
            empty.innerHTML = '' +
                '<div class="empty empty--compact">' +
                '  <div class="empty__icon" style="color: var(--p-color-critical);"><i class="fa-solid fa-triangle-exclamation"></i></div>' +
                '  <div class="empty__title">Failed to load point history</div>' +
                '  <p class="empty__body">Please try again.</p>' +
                '</div>';
            setVisible(empty, true);
        }
    }

    function displayHistory(history) {
        var loading = document.getElementById('point-history-loading');
        var items = document.getElementById('point-history-empty');
        var empty = document.getElementById('point-history-empty');
        setVisible(loading, false);

        if (!history || history.length === 0) {
            setVisible(items, false);
            setVisible(empty, true);
            return;
        }

        var groups = groupByDate(history);
        var html = '';
        var keys = Object.keys(groups);
        for (var i = 0; i < keys.length; i++) {
            html += buildDateGroup(keys[i], groups[keys[i]]);
        }
        items.innerHTML = html;
        setVisible(items, true);
        setVisible(empty, false);
    }

    function loadPointHistory() {
        var loading = document.getElementById('point-history-loading');
        var items = document.getElementById('point-history-items');
        var empty = document.getElementById('point-history-empty');
        setVisible(loading, true);
        setVisible(items, false);
        setVisible(empty, false);

        fetch('/points/history')
            .then(function (r) {
                if (!r.ok) throw new Error('HTTP ' + r.status);
                return r.json();
            })
            .then(function (data) {
                if (data && data.success) displayHistory(data.history);
                else showError();
            })
            .catch(function (e) {
                console.error('Error loading point history:', e);
                showError();
            });
    }

    function showPointHistory() {
        var modal = document.getElementById('point-history-modal');
        if (!modal) return;
        modal.hidden = false;
        document.body.style.overflow = 'hidden';
        loadPointHistory();
    }

    function hidePointHistory() {
        var modal = document.getElementById('point-history-modal');
        if (!modal) return;
        modal.hidden = true;
        document.body.style.overflow = '';
    }

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') hidePointHistory();
    });

    document.addEventListener('click', function (e) {
        var modal = document.getElementById('point-history-modal');
        if (modal && !modal.hidden && e.target === modal) hidePointHistory();
    });

    window.showPointHistory = showPointHistory;
    window.hidePointHistory = hidePointHistory;
})();
