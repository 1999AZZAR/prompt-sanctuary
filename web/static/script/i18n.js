/* Runtime gettext for the browser.
 *
 * Server embeds window.I18N = {lang: 'id', catalog: {...}} in base.html
 * before any other script, so this module is fully synchronous.
 *
 * Usage:
 *   const msg = _('Saved successfully.');
 *   const msg = _('You have %(count)s items.', { count: 5 });
 *   const msg = _('Hello, %(name)s.', 'Alice');  // single positional %s
 *
 * Falls back to the msgid if the catalog is missing the entry.
 */
(function () {
  const data = (typeof window !== 'undefined' && window.I18N) || { lang: 'en', catalog: {} };
  const catalog = data.catalog || {};
  const activeLang = data.lang || 'en';

  function format(template, params) {
    if (params === undefined || params === null) return template;
    if (typeof params === 'string' || typeof params === 'number') {
      // Single positional: replace all %(...)s with the value
      return template.replace(/%\(([^)]+)\)s/g, function () { return String(params); });
    }
    if (typeof params === 'object') {
      return template.replace(/%\(([^)]+)\)s/g, function (m, k) {
        return Object.prototype.hasOwnProperty.call(params, k) ? String(params[k]) : m;
      });
    }
    return template;
  }

  function _(msgid, params) {
    if (activeLang === 'en' || !msgid) return format(msgid, params);
    const translated = Object.prototype.hasOwnProperty.call(catalog, msgid) ? catalog[msgid] : msgid;
    return format(translated, params);
  }

  function n_(singular, plural, n, params) {
    if (activeLang === 'en' || !singular) {
      const tpl = n === 1 ? singular : plural;
      return format(tpl, Object.assign({ n: n }, params || {}));
    }
    // We don't have proper plural catalog in the runtime, so use the singular/plural
    // based on n. Future: add ICU MessageFormat support.
    const tpl = n === 1 ? singular : plural;
    return format(tpl, Object.assign({ n: n }, params || {}));
  }

  // Expose
  window._ = _;
  window.n_ = n_;
  window.i18n = { lang: activeLang, catalog: catalog };
})();
