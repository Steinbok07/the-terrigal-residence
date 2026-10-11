/* The Terrigal Residence: measurement (Google Ads conversions and optional Google Analytics 4).
 *
 * IDs come from site-config.js. While they're empty, nothing from Google loads and
 * contact actions are only recorded locally in dataLayer.
 *
 * Privacy controls:
 *  - A visitor can switch measurement off on the privacy page. That choice is kept in
 *    this browser and stops Google's tag loading at all.
 *  - Visitors in the EEA, UK and Switzerland default to "denied" (Google Consent Mode),
 *    so no advertising or analytics cookies are set for them.
 *
 * Actions:
 *  - enquiry: fired by thank-you/ only when it carries a one-time token that the form sets
 *    after the provider confirms delivery. Reloading or visiting the page directly counts
 *    nothing, and the token doubles as the conversion's transaction_id so Google can
 *    discard any duplicate.
 *  - phone / email: any click on a tel: or mailto: link. These are interactions, not proof
 *    that a call or email took place.
 */
(function () {
  'use strict';

  var cfg = window.SITE_CONFIG || {};
  var ads = cfg.googleAds || {};
  var labels = ads.labels || {};
  var ga = (cfg.googleAnalytics || {}).measurementId || '';
  var OPT_OUT = 'tr-measurement-off';

  function optedOut() { try { return localStorage.getItem(OPT_OUT) === '1'; } catch (e) { return false; } }

  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }

  var tagIds = [ads.conversionId, ga].filter(Boolean);
  var live = tagIds.length > 0 && !optedOut();

  if (live) {
    // Consent Mode defaults: denied where opt-in consent is the norm, granted elsewhere.
    gtag('consent', 'default', {
      ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied', analytics_storage: 'denied',
      region: ['AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'HU', 'IS', 'IE', 'IT', 'LV',
               'LI', 'LT', 'LU', 'MT', 'NL', 'NO', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE', 'GB', 'CH']
    });
    gtag('consent', 'default', {
      ad_storage: 'granted', ad_user_data: 'granted', ad_personalization: 'granted', analytics_storage: 'granted'
    });
    if (!document.querySelector('script[src*="googletagmanager.com/gtag/js"]')) { // never install the tag twice
      var s = document.createElement('script');
      s.async = true;
      s.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(tagIds[0]);
      document.head.appendChild(s);
    }
    gtag('js', new Date());
    tagIds.forEach(function (id) { gtag('config', id); });
  }

  /* Record an action. eventName goes to dataLayer and Google Analytics. The matching Google Ads
     label (if set) is sent as a conversion. opts.transactionId removes duplicates in Google Ads. */
  function track(action, eventName, opts) {
    opts = opts || {};
    window.dataLayer.push({ event: eventName, transaction_id: opts.transactionId });
    if (!live) return;
    if (ga) gtag('event', eventName, opts.transactionId ? { transaction_id: opts.transactionId } : {});
    if (ads.conversionId && labels[action]) {
      var p = { send_to: ads.conversionId + '/' + labels[action] };
      if (opts.transactionId) p.transaction_id = opts.transactionId;
      gtag('event', 'conversion', p);
    }
  }

  // Phone and email clicks, on any page that loads this file
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href^="tel:"], a[href^="mailto:"]');
    if (!a) return;
    if (a.getAttribute('href').indexOf('tel:') === 0) track('phone', 'phone_click');
    else track('email', 'email_click');
  });

  /* Ad-click details for the enquiry email. When a visitor lands from an ad, the click ID (gclid,
     gbraid or wbraid) and any utm_ campaign tags are kept for this browser session, so the enquiry
     can say it came from Google Ads. Google's own conversion cookie (_gcl_aw, set by the tag
     above) still carries the click for attribution, whatever page the visitor lands on. */
  var LANDING = 'tr-landing';
  try {
    var q = new URLSearchParams(location.search), found = {};
    ['gclid', 'gbraid', 'wbraid', 'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'].forEach(function (k) {
      var v = q.get(k);
      if (v) found[k] = v.slice(0, 200);
    });
    if (Object.keys(found).length) sessionStorage.setItem(LANDING, JSON.stringify(found));
  } catch (e) { /* storage blocked */ }

  function adSource() {
    var d = {};
    try { d = JSON.parse(sessionStorage.getItem(LANDING) || '{}'); } catch (e) { /* storage blocked */ }
    if (!d.gclid) { // returning visitor: fall back to Google's conversion cookie (GCL.<time>.<gclid>)
      var m = document.cookie.match(/(?:^|;\s*)_gcl_aw=GCL\.\d+\.([^;]+)/);
      if (m) d.gclid = decodeURIComponent(m[1]);
    }
    var click = d.gclid || d.gbraid || d.wbraid;
    var parts = [];
    if (click) parts.push('Google Ads click');
    if (d.utm_source || d.utm_medium) parts.push([d.utm_source, d.utm_medium].filter(Boolean).join(' / '));
    if (d.utm_campaign) parts.push('campaign: ' + d.utm_campaign);
    if (d.utm_term) parts.push('keyword: ' + d.utm_term);
    if (click) parts.push((d.gclid ? 'gclid' : d.gbraid ? 'gbraid' : 'wbraid') + ': ' + click);
    return parts.join(' · ');
  }

  window.TR_TRACKING = {
    adSource: adSource,
    track: track,
    live: function () { return live; },
    optedOut: optedOut,
    setOptOut: function (off) {
      try { if (off) localStorage.setItem(OPT_OUT, '1'); else localStorage.removeItem(OPT_OUT); } catch (e) { /* storage blocked */ }
    }
  };
})();
