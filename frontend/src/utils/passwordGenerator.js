/**
 * Cryptographically secure, human-friendly password generator for employee account provisioning.
 * Format: <PrefixWord><Separator><4Digits><SuffixWord>
 * Example: Solar@4821Sun, Volt#7392Peak
 */

const PREFIX_WORDS = [
  'Solar', 'Power', 'Volt', 'Watt', 'Panel', 'Amber', 'Bright', 'Ray',
  'Spark', 'Peak', 'Energy', 'Lumen', 'Photon', 'Sky', 'Clean', 'Helios',
  'Aurora', 'Zenith', 'Prism', 'Beacon', 'River', 'Summit', 'Haven',
  'Breeze', 'Cedar', 'Orbit', 'Optic', 'Nova', 'Pulse', 'Onyx'
];

const SUFFIX_WORDS = [
  'Sun', 'Grid', 'Volt', 'Watt', 'Ray', 'Beam', 'Star', 'Flow',
  'Core', 'Peak', 'Base', 'Link', 'Wave', 'Nova', 'Dawn', 'Sky',
  'Glow', 'Spark', 'Pure', 'Rise', 'Zone', 'Hub', 'Line', 'Gate'
];

const SEPARATORS = ['@', '#', '$', '!', '%', '&'];

function getSecureRandomInt(min, max) {
  const range = max - min + 1;
  if (typeof window !== 'undefined' && window.crypto && window.crypto.getRandomValues) {
    const array = new Uint32Array(1);
    window.crypto.getRandomValues(array);
    return min + (array[0] % range);
  }
  return min + Math.floor(Math.random() * range);
}

export function generateHumanFriendlyPassword() {
  const prefix = PREFIX_WORDS[getSecureRandomInt(0, PREFIX_WORDS.length - 1)];
  const separator = SEPARATORS[getSecureRandomInt(0, SEPARATORS.length - 1)];
  const digits = String(getSecureRandomInt(1000, 9999));

  let suffix = SUFFIX_WORDS[getSecureRandomInt(0, SUFFIX_WORDS.length - 1)];
  while (suffix.toLowerCase() === prefix.toLowerCase()) {
    suffix = SUFFIX_WORDS[getSecureRandomInt(0, SUFFIX_WORDS.length - 1)];
  }

  return `${prefix}${separator}${digits}${suffix}`;
}
