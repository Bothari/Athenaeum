export type ToastType = 'success' | 'error' | 'info';

export interface Toast {
	id: number;
	message: string;
	type: ToastType;
}

/** Matches v1's 3s auto-dismiss. */
const DISMISS_MS = 3000;

class ToastStore {
	items = $state<Toast[]>([]);
	#nextId = 0;

	show(message: string, type: ToastType = 'success'): void {
		const id = this.#nextId++;
		this.items.push({ id, message, type });
		setTimeout(() => this.dismiss(id), DISMISS_MS);
	}

	success(message: string): void {
		this.show(message, 'success');
	}

	error(message: string): void {
		this.show(message, 'error');
	}

	info(message: string): void {
		this.show(message, 'info');
	}

	dismiss(id: number): void {
		const i = this.items.findIndex((t) => t.id === id);
		if (i !== -1) this.items.splice(i, 1);
	}
}

export const toasts = new ToastStore();
