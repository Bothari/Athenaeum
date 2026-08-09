import type { AuthorCardData, BookCardData, SeriesCardData } from '$lib/types/library';
import type { PageParams, PageResult } from '$lib/types/table';

export const books: BookCardData[] = [
	{
		id: 'b1',
		title: 'A Book With Both Formats Held In The Library',
		authors: [{ name: 'Ann Author' }, { name: 'Bo Coauthor' }],
		cover_url: null,
		formats: [
			{ type: 'audiobook', narrator: 'Nadia Narrator' },
			{ type: 'ebook' }
		]
	},
	{
		id: 'b2',
		title: 'Requested, Not Yet Held',
		author: 'Solo Author',
		cover_url: null,
		formats: [],
		requests: [{ type: 'audiobook', status: 'requested' }]
	},
	{
		id: 'b3',
		title: 'Held In One Format, Requested In The Other',
		author: 'Mixed State',
		cover_url: null,
		formats: [{ type: 'ebook' }],
		// Should NOT render — already held in that format.
		requests: [
			{ type: 'ebook', status: 'requested' },
			{ type: 'audiobook', status: 'failed' }
		]
	},
	{
		id: 'b4',
		title: 'A Very Long Title That Should Clamp To Exactly Two Lines And Then Stop',
		author: 'Overflow Test',
		cover_url: null,
		formats: []
	}
];

export const authors: AuthorCardData[] = [
	{ id: 'a1', name: 'Ann Author', book_count: 12 },
	{ id: 'a2', name: 'Single Book', book_count: 1 },
	{ id: 'a3', name: 'No Books Yet', book_count: 0 }
];

export const series: SeriesCardData[] = [
	{
		id: 's1',
		name: 'Incomplete Series',
		library_count: 3,
		requested_count: 1,
		missing_primary: 2,
		upcoming_primary: 0
	},
	{
		id: 's2',
		name: 'Has Upcoming Only',
		library_count: 5,
		requested_count: 0,
		missing_primary: 0,
		upcoming_primary: 1
	},
	{
		id: 's3',
		name: 'Complete Series',
		library_count: 7,
		requested_count: 0,
		missing_primary: 0,
		upcoming_primary: 0
	},
	{
		id: 's4',
		name: 'Counts Not Computed Yet',
		library_count: 2,
		requested_count: 0,
		missing_primary: null,
		upcoming_primary: null
	}
];

export interface DemoRow {
	title: string;
	author: string;
	year: number;
}

const ROW_COUNT = 137;

const allRows: DemoRow[] = Array.from({ length: ROW_COUNT }, (_, i) => ({
	title: `Demo row ${i + 1}`,
	// Every fifth row carries a long author list so cells wrap to several lines.
	// Uniform short cells hid a row-alignment bug that only appeared on mobile:
	// fixtures must include the ragged case, not just the tidy one.
	author:
		i % 5 === 0
			? `Author ${String.fromCharCode(65 + (i % 26))}, Second Contributor, Third Collaborator`
			: `Author ${String.fromCharCode(65 + (i % 26))}`,
	year: 1970 + (i % 55)
}));

/** Stands in for a real endpoint: sorts, filters and pages over fixture data with
 *  a small delay, so loading states and infinite scroll are genuinely exercised. */
export async function fetchDemoPage(params: PageParams): Promise<PageResult<DemoRow>> {
	await new Promise((r) => setTimeout(r, 250));

	let rows = allRows;
	if (params.q) {
		const q = params.q.toLowerCase();
		rows = rows.filter(
			(r) => r.title.toLowerCase().includes(q) || r.author.toLowerCase().includes(q)
		);
	}

	const key = params.sort as keyof DemoRow;
	rows = [...rows].sort((a, b) => {
		const av = a[key];
		const bv = b[key];
		const cmp = typeof av === 'number' && typeof bv === 'number' ? av - bv : String(av).localeCompare(String(bv));
		return params.dir === 'asc' ? cmp : -cmp;
	});

	return {
		items: rows.slice(params.offset, params.offset + params.limit),
		total: rows.length
	};
}

/** Always rejects, for the table's error state. */
export async function fetchFailingPage(): Promise<PageResult<DemoRow>> {
	await new Promise((r) => setTimeout(r, 250));
	throw new Error('Simulated failure');
}

/** Always empty, for the table's empty state. */
export async function fetchEmptyPage(): Promise<PageResult<DemoRow>> {
	return { items: [], total: 0 };
}
