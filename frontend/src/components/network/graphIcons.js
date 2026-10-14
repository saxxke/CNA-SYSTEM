/**
 * graphIcons.js — Professional SVG iconography and visual styling for Cytoscape nodes.
 *
 * Replaces generic geometric shapes with crisp, high-resolution vector icons matching
 * Lucide icon paths for investigation entities:
 * - PERSON: User profile icon
 * - PHONE: Smartphone device icon
 * - WHATSAPP / COMMUNICATION: Chat bubble icon
 * - VEHICLE: Car icon
 * - LOCATION: MapPin icon
 * - ORGANIZATION: Building2 icon
 * - BANK_ACCOUNT: CreditCard / Financial instrument icon
 * - CASE: Folder / Dossier icon
 *
 * Generated directly as vector SVG data-URIs for maximum clarity at any canvas zoom level.
 */

// SVG path definitions identical to Lucide React SVG specifications
const ICON_PATHS = {
  PERSON: `
    <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
    <circle cx="12" cy="7" r="4" />
  `,
  PHONE: `
    <rect width="14" height="20" x="5" y="2" rx="2" ry="2" />
    <path d="M12 18h.01" />
  `,
  WHATSAPP: `
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    <path d="M8 10h.01M12 10h.01M16 10h.01" />
  `,
  VEHICLE: `
    <path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2" />
    <circle cx="7" cy="17" r="2" />
    <path d="M9 17h6" />
    <circle cx="17" cy="17" r="2" />
  `,
  LOCATION: `
    <path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0" />
    <circle cx="12" cy="10" r="3" />
  `,
  ORGANIZATION: `
    <path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z" />
    <path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2" />
    <path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2" />
    <path d="M10 6h4" />
    <path d="M10 10h4" />
    <path d="M10 14h4" />
    <path d="M10 18h4" />
  `,
  BANK_ACCOUNT: `
    <rect width="20" height="14" x="2" y="5" rx="2" />
    <line x1="2" x2="22" y1="10" y2="10" />
  `,
  CASE: `
    <path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z" />
  `,
  UNKNOWN: `
    <circle cx="12" cy="12" r="10" />
    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
    <line x1="12" x2="12.01" y1="17" y2="17" />
  `,
};

/**
 * Creates a standalone SVG data URI with specific stroke color and stroke width.
 */
function createSvgUri(pathContent, strokeColor = '#f8fafc', strokeWidth = 2) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="${strokeColor}" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round">${pathContent}</svg>`;
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}

/**
 * Resolves node visual classification without altering underlying backend data or relationship types.
 * Accurately detects WhatsApp / communication channel entities.
 */
export function resolveVisualType(nodeData) {
  if (!nodeData) return 'UNKNOWN';

  const rawType = (nodeData.type || '').toUpperCase();
  const idStr = String(nodeData.id || '').toUpperCase();
  const labelStr = String(nodeData.label || '').toUpperCase();

  // WhatsApp / Communication channel detection
  if (
    rawType === 'WHATSAPP' ||
    rawType === 'COMMUNICATION' ||
    rawType === 'CHANNEL' ||
    idStr.includes('WHATSAPP') ||
    labelStr.includes('WHATSAPP')
  ) {
    return 'WHATSAPP';
  }

  if (rawType === 'PERSON') return 'PERSON';
  if (rawType === 'PHONE') return 'PHONE';
  if (rawType === 'VEHICLE') return 'VEHICLE';
  if (rawType === 'LOCATION') return 'LOCATION';
  if (rawType === 'ORGANIZATION') return 'ORGANIZATION';
  if (rawType === 'BANK_ACCOUNT' || rawType === 'BANK' || rawType === 'ACCOUNT') return 'BANK_ACCOUNT';
  if (rawType === 'CASE' || rawType === 'CASE_RECORD') return 'CASE';

  return 'UNKNOWN';
}

/**
 * Visual styling hierarchy for investigation nodes.
 * Person = primary visual node (size 54, highest zIndex, sky accent)
 * Case = secondary landmark node (size 50, indigo accent)
 * Supporting entities = (size 42-46, distinct iconography & curated dark navy palette)
 */
export const TYPE_STYLES = {
  PERSON: {
    label: 'Associated Person',
    color: '#38bdf8',       // sky-400
    bgColor: '#0c2340',     // dark navy sky tint
    shape: 'ellipse',
    size: 54,
    borderWidth: 2.8,
    zIndex: 12,
    iconSvg: createSvgUri(ICON_PATHS.PERSON, '#38bdf8', 2.1),
    iconSvgSelected: createSvgUri(ICON_PATHS.PERSON, '#ffffff', 2.4),
  },
  CASE: {
    label: 'Case Record',
    color: '#818cf8',       // indigo-400
    bgColor: '#171b3c',     // dark navy indigo tint
    shape: 'round-rectangle',
    size: 50,
    borderWidth: 2.5,
    zIndex: 10,
    iconSvg: createSvgUri(ICON_PATHS.CASE, '#818cf8', 2.1),
    iconSvgSelected: createSvgUri(ICON_PATHS.CASE, '#ffffff', 2.4),
  },
  ORGANIZATION: {
    label: 'Organization / Business',
    color: '#f472b6',       // pink-400
    bgColor: '#2a1122',     // dark navy pink tint
    shape: 'round-rectangle',
    size: 46,
    borderWidth: 2.2,
    zIndex: 8,
    iconSvg: createSvgUri(ICON_PATHS.ORGANIZATION, '#f472b6', 2.0),
    iconSvgSelected: createSvgUri(ICON_PATHS.ORGANIZATION, '#ffffff', 2.4),
  },
  WHATSAPP: {
    label: 'WhatsApp / Chat Channel',
    color: '#22c55e',       // green-500
    bgColor: '#082512',     // dark green/navy tint
    shape: 'ellipse',
    size: 44,
    borderWidth: 2.2,
    zIndex: 7,
    iconSvg: createSvgUri(ICON_PATHS.WHATSAPP, '#22c55e', 2.1),
    iconSvgSelected: createSvgUri(ICON_PATHS.WHATSAPP, '#ffffff', 2.4),
  },
  BANK_ACCOUNT: {
    label: 'Bank Account',
    color: '#fbbf24',       // amber-400
    bgColor: '#281c08',     // dark amber tint
    shape: 'round-rectangle',
    size: 44,
    borderWidth: 2.2,
    zIndex: 7,
    iconSvg: createSvgUri(ICON_PATHS.BANK_ACCOUNT, '#fbbf24', 2.0),
    iconSvgSelected: createSvgUri(ICON_PATHS.BANK_ACCOUNT, '#ffffff', 2.4),
  },
  VEHICLE: {
    label: 'Vehicle Asset',
    color: '#c084fc',       // purple-400
    bgColor: '#221133',     // dark purple tint
    shape: 'round-rectangle',
    size: 44,
    borderWidth: 2.2,
    zIndex: 6,
    iconSvg: createSvgUri(ICON_PATHS.VEHICLE, '#c084fc', 2.0),
    iconSvgSelected: createSvgUri(ICON_PATHS.VEHICLE, '#ffffff', 2.4),
  },
  PHONE: {
    label: 'Phone Identifier',
    color: '#34d399',       // emerald-400
    bgColor: '#08261d',     // dark emerald tint
    shape: 'ellipse',
    size: 42,
    borderWidth: 2.2,
    zIndex: 6,
    iconSvg: createSvgUri(ICON_PATHS.PHONE, '#34d399', 2.0),
    iconSvgSelected: createSvgUri(ICON_PATHS.PHONE, '#ffffff', 2.4),
  },
  LOCATION: {
    label: 'Locality / Address',
    color: '#f87171',       // red-400
    bgColor: '#2b1013',     // dark rose tint
    shape: 'ellipse',
    size: 42,
    borderWidth: 2.2,
    zIndex: 6,
    iconSvg: createSvgUri(ICON_PATHS.LOCATION, '#f87171', 2.0),
    iconSvgSelected: createSvgUri(ICON_PATHS.LOCATION, '#ffffff', 2.4),
  },
  UNKNOWN: {
    label: 'Other Entity',
    color: '#94a3b8',       // slate-400
    bgColor: '#0f172a',
    shape: 'ellipse',
    size: 38,
    borderWidth: 1.8,
    zIndex: 1,
    iconSvg: createSvgUri(ICON_PATHS.UNKNOWN, '#94a3b8', 1.8),
    iconSvgSelected: createSvgUri(ICON_PATHS.UNKNOWN, '#ffffff', 2.0),
  },
};

export function getTypeStyle(type) {
  return TYPE_STYLES[type] || TYPE_STYLES.UNKNOWN;
}
