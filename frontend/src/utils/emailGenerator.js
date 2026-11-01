/**
 * Work email generation utility for SunPower Solutions SIMS employees.
 * Format: firstname.lastname@companydomain
 */

export const COMPANY_EMAIL_DOMAIN = 'sunpower.com';

export function normalizeNameForEmail(name) {
  if (!name) return '';
  return name
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '');
}

export function generateWorkEmailPreview(firstName, lastName, domain = COMPANY_EMAIL_DOMAIN) {
  const fn = normalizeNameForEmail(firstName);
  const ln = normalizeNameForEmail(lastName);
  if (!fn && !ln) return '';
  const prefix = fn && ln ? `${fn}.${ln}` : fn || ln;
  return `${prefix}@${domain}`;
}
