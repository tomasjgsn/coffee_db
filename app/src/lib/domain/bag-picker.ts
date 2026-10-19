/**
 * The plan's bag picker: the bags in use first, the rest folded away, so
 * logging a brew starts with the bag already in reach.
 */

interface PickerBag {
	bean: { id: number; createdAt: string };
	lastBrewedAt: string | null;
}

/** How many recent bags stay in view before the fold. */
export const RECENT_BAGS = 4;

/** Day the bag was last brewed, or the day it was added if it never was. */
function recency(bag: PickerBag): string {
	return bag.lastBrewedAt ?? bag.bean.createdAt.slice(0, 10);
}

/** Most recently brewed (or added) first; ties go to the newer bag. */
export function orderForPicker<T extends PickerBag>(bags: T[]): T[] {
	return [...bags].sort((a, b) => recency(b).localeCompare(recency(a)) || b.bean.id - a.bean.id);
}

/**
 * Split ordered bags into the ones in view and the folded rest. The bag the
 * plan opened with always stays in view; a single leftover is not folded.
 */
export function splitForPicker<T extends PickerBag>(
	ordered: T[],
	selectedId: number | null,
	count: number = RECENT_BAGS
): { recent: T[]; other: T[] } {
	if (ordered.length <= count + 1) return { recent: ordered, other: [] };
	const recent = ordered.slice(0, count);
	const other = ordered.slice(count);
	const selected = other.find((b) => b.bean.id === selectedId);
	if (!selected) return { recent, other };
	return { recent: [...recent, selected], other: other.filter((b) => b !== selected) };
}
