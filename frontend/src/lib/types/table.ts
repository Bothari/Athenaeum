export interface Column {
	key: string;
	label: string;
	/** Defaults to true, matching v1 where sortable was opt-out. */
	sortable?: boolean;
	width?: string;
}

export interface PageParams {
	q: string;
	sort: string;
	dir: 'asc' | 'desc';
	limit: number;
	offset: number;
}

export interface PageResult<T> {
	items: T[];
	total: number;
}
