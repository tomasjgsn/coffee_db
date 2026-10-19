import { describe, expect, it } from 'vitest';
import { orderForPicker, splitForPicker } from './bag-picker';

const bag = (id: number, lastBrewedAt: string | null, createdAt = '2026-07-01T09:00:00.000Z') => ({
	bean: { id, createdAt },
	lastBrewedAt
});

describe('orderForPicker', () => {
	it('puts the most recently brewed bag first', () => {
		const ordered = orderForPicker([bag(1, '2026-01-22'), bag(2, '2026-08-04'), bag(3, '2026-07-28')]);
		expect(ordered.map((b) => b.bean.id)).toEqual([2, 3, 1]);
	});

	it('ranks a bag that was never brewed by the day it was added', () => {
		const ordered = orderForPicker([
			bag(1, '2026-08-04'),
			bag(2, null, '2026-10-18T19:30:00.000Z'),
			bag(3, '2026-01-22')
		]);
		expect(ordered.map((b) => b.bean.id)).toEqual([2, 1, 3]);
	});

	it('breaks ties by the newer bag', () => {
		const ordered = orderForPicker([bag(4, '2026-08-04'), bag(9, '2026-08-04')]);
		expect(ordered.map((b) => b.bean.id)).toEqual([9, 4]);
	});
});

describe('splitForPicker', () => {
	const six = [bag(1, '2026-08-06'), bag(2, '2026-08-05'), bag(3, '2026-08-04'), bag(4, '2026-08-03'), bag(5, '2026-08-02'), bag(6, '2026-08-01')];

	it('shows the four most recent bags and folds the rest', () => {
		const { recent, other } = splitForPicker(six, 1);
		expect(recent.map((b) => b.bean.id)).toEqual([1, 2, 3, 4]);
		expect(other.map((b) => b.bean.id)).toEqual([5, 6]);
	});

	it('keeps the selected bag visible even when it is older', () => {
		const { recent, other } = splitForPicker(six, 6);
		expect(recent.map((b) => b.bean.id)).toEqual([1, 2, 3, 4, 6]);
		expect(other.map((b) => b.bean.id)).toEqual([5]);
	});

	it('does not fold a single leftover bag', () => {
		const { recent, other } = splitForPicker(six.slice(0, 5), 1);
		expect(recent).toHaveLength(5);
		expect(other).toHaveLength(0);
	});
});
