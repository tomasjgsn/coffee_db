import { getDb } from '$lib/server/db/instance';
import { listBrews } from '$lib/server/brew-views';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = ({ url }) => {
	const beanFilter = url.searchParams.get('bean');
	const methodFilter = url.searchParams.get('method');

	const { items } = listBrews(getDb());

	const beanOptions = [...new Set(items.map((i) => i.beanName).filter((n): n is string => !!n))];
	const methodOptions = [...new Set(items.map((i) => i.method))];

	const filtered = items.filter(
		(i) =>
			(!beanFilter || i.beanName === beanFilter) && (!methodFilter || i.method === methodFilter)
	);

	return {
		brews: filtered,
		total: items.length,
		beanOptions,
		methodOptions,
		beanFilter,
		methodFilter
	};
};
