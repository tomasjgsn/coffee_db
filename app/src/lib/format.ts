/** Display formatting — presentation only, never feeds calculations. */

const MONTHS = [
	'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
	'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
];
const MONTHS_FULL = [
	'January', 'February', 'March', 'April', 'May', 'June',
	'July', 'August', 'September', 'October', 'November', 'December'
];
const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export function ratioLabel(ratio: number | null | undefined): string {
	if (ratio === null || ratio === undefined) return '—';
	return `1:${trimZeros(ratio.toFixed(1))}`;
}

export function pct(value: number | null | undefined): string {
	if (value === null || value === undefined) return '—';
	return `${value.toFixed(1)}%`;
}

export function score1(value: number | null | undefined): string {
	if (value === null || value === undefined) return '—';
	return value.toFixed(1);
}

export function grams(value: number | null | undefined): string {
	if (value === null || value === undefined) return '—';
	return `${trimZeros(value.toFixed(1))} g`;
}

export function monthHeading(isoDate: string): string {
	const [y, m] = isoDate.split('-').map(Number);
	return `${MONTHS_FULL[m - 1]} ${y}`;
}

export function dayNumber(isoDate: string): string {
	return String(Number(isoDate.split('-')[2]));
}

export function weekdayDay(isoDate: string): string {
	const [y, m, d] = isoDate.split('-').map(Number);
	const date = new Date(Date.UTC(y, m - 1, d));
	return `${WEEKDAYS[date.getUTCDay()]} ${d} ${MONTHS[m - 1]}`;
}

function trimZeros(fixed: string): string {
	return fixed.replace(/\.0$/, '');
}

/** 182 → "3:02". Used for the live timer and time displays. */
export function clock(totalSeconds: number): string {
	const s = Math.max(0, Math.floor(totalSeconds));
	return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}

/** Parse "3:02", "2'30", or bare seconds "45" → seconds. Null when unparseable. */
export function parseClock(value: string): number | null {
	const trimmed = value.trim();
	if (trimmed === '') return null;
	const match = /^(\d{1,3})[:'](\d{1,2})$/.exec(trimmed);
	if (match) {
		const seconds = Number(match[2]);
		if (seconds >= 60) return null;
		return Number(match[1]) * 60 + seconds;
	}
	if (/^\d+$/.test(trimmed)) return Number(trimmed);
	return null;
}
