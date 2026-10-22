import { request } from './client';
import type { PageParams, PageResult } from '$lib/types/table';
import type { AuthorListItem, BookListItem, SeriesListItem } from '$lib/types/library';

/** Every list endpoint takes the same window plus an optional unlinked filter. */
export interface ListQuery extends Partial<PageParams> {
	unlinked?: boolean;
}

function toQuery(params: ListQuery): string {
	const q = new URLSearchParams();
	if (params.q) q.set('q', params.q);
	if (params.sort) q.set('sort', params.sort);
	if (params.dir) q.set('dir', params.dir);
	if (params.limit != null) q.set('limit', String(params.limit));
	if (params.offset != null) q.set('offset', String(params.offset));
	// Only sent when true: the backend defaults it to false, and always sending it
	// would make every URL carry a redundant param.
	if (params.unlinked) q.set('unlinked', '1');
	return q.toString();
}

/** sort: title | author (VALID_BOOK_SORTS in app/routes/books.py) */
export function listBooks(params: ListQuery): Promise<PageResult<BookListItem>> {
	return request<PageResult<BookListItem>>(`/books?${toQuery(params)}`);
}

/** sort: name | book_count */
export function listAuthors(params: ListQuery): Promise<PageResult<AuthorListItem>> {
	return request<PageResult<AuthorListItem>>(`/authors?${toQuery(params)}`);
}

/** sort: name | library_count | missing */
export function listSeries(params: ListQuery): Promise<PageResult<SeriesListItem>> {
	return request<PageResult<SeriesListItem>>(`/series?${toQuery(params)}`);
}
