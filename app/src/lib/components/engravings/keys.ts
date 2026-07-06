/** Illustration keys available in the brush-ink set. Kept as plain TS so
 * domain tests can verify coverage without importing Svelte components. */
export const INK_KEYS = ['v60', 'switch', 'aeropress', 'chemex'] as const;

export type InkKey = (typeof INK_KEYS)[number];
