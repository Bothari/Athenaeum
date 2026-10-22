export interface Column {
	key: string;
	label: string;
	/** Defaults to true, matching v1 where sortable was opt-out. */
	sortable?: boolean;
	width?: string;
	/** Hides the header below 640px. The row snippet must hide its matching cell
	 *  too, or the columns misalign. */
	hideOnMobile?: boolean;
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
