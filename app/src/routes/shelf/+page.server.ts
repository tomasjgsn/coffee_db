import { getDb } from '$lib/server/db/instance';
import { shelf } from '$lib/server/brew-views';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = () => {
	return { shelf: shelf(getDb()) };
};
