/**
 * SC Referral Link helper
 *
 * Rotation discontinued 2026-06-28 — all CTAs use the single code below.
 * To wire up a button/link: add the attribute  data-referral-cta  to the element.
 */

const REFERRAL_CODE = 'STAR-GCQJ-N6NC';
const BASE_URL = 'https://www.robertsspaceindustries.com/enlist?referral=';

function getReferralUrl() {
  return BASE_URL + REFERRAL_CODE;
}

function initReferralButtons() {
  const url = getReferralUrl();

  document.querySelectorAll('[data-referral-cta]').forEach(function (el) {
    if (el.tagName === 'A') {
      el.href = url;
      if (!el.hasAttribute('target')) el.setAttribute('target', '_blank');
      el.setAttribute('rel', 'noopener noreferrer');
    } else {
      el.addEventListener('click', function () {
        window.open(url, '_blank', 'noopener,noreferrer');
      });
    }
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initReferralButtons);
} else {
  initReferralButtons();
}
