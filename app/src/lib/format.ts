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
