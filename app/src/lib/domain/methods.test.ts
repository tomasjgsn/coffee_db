import { describe, expect, it } from 'vitest';
import { METHODS, RETIRED_DEVICES, methodById, methodForLegacyDevice, methodShortLabel } from './methods';
import { INK_KEYS } from '$lib/components/engravings/keys';

describe('brew method registry', () => {
	it('offers exactly the six methods Tomas brews', () => {
		expect(METHODS.map((m) => m.id)).toEqual([
			'v60',
			'v60-ceramic',
			'hario-switch',
			'aeropress',
			'aeropress-iced',
			'chemex'
		]);
	});

	it('gives every pickable method a brush-ink illustration', () => {
		for (const method of METHODS) {
			expect(INK_KEYS).toContain(method.illustration);
		}
	});

	it('labels an unrecorded method in words', () => {
		expect(methodShortLabel('unknown')).toBe('unrecorded');
	});

	it('keeps retired devices out of the picker entirely', () => {
		for (const retired of RETIRED_DEVICES) {
			expect(methodForLegacyDevice(retired)).toBeUndefined();
			expect(METHODS.some((m) => m.label === retired)).toBe(false);
		}
	});

	it('maps every legacy CSV device string to at most one method', () => {
		const seen = new Map<string, string>();
		for (const method of METHODS) {
			for (const device of method.legacyDevices) {
				expect(seen.has(device), `${device} mapped twice`).toBe(false);
				seen.set(device, method.id);
			}
		}
	});

	it('maps known legacy devices, including the Hoffman top up variant', () => {
		expect(methodForLegacyDevice('V60 ceramic')?.id).toBe('v60-ceramic');
		expect(methodForLegacyDevice('Hoffman top up')?.id).toBe('v60');
		expect(methodForLegacyDevice('Hario Switch')?.id).toBe('hario-switch');
	});

	it('flags only the flash-iced method as iced', () => {
		expect(METHODS.filter((m) => m.iced).map((m) => m.id)).toEqual(['aeropress-iced']);
		expect(methodById('aeropress-iced')?.iced).toBe(true);
	});
});
