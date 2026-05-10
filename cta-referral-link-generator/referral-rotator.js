/**
 * SC Referral Link Rotator
 *
 * Round-robin rotates referral codes across page visits using localStorage.
 * All CTA buttons on a given page always share the same code for that visit.
 *
 * To add more codes: append to REFERRAL_CODES below.
 * To wire up a button/link: add the attribute  data-referral-cta  to the element.
 */

const REFERRAL_CODES = [
  'STAR-GCQJ-N6NC', // Your code
  'STAR-CLXM-7VNH', // Jake's code
];

const BASE_URL = 'https://www.robertsspaceindustries.com/enlist?referral=';
const STORAGE_KEY = 'sc_referral_index';

function getReferralUrl() {
  const total = REFERRAL_CODES.length;
  const raw = localStorage.getItem(STORAGE_KEY);
  const index = raw !== null ? parseInt(raw, 10) : 0;
  const code = REFERRAL_CODES[index % total];

  // Advance the counter for the next page visit
  localStorage.setItem(STORAGE_KEY, (index + 1) % total);

  return BASE_URL + code;
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
