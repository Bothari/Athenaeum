<script lang="ts">
	/**
	 * "Unlinked only" filter shared by the books, authors and series lists. The
	 * dashboard's Hardcover-link tiles deep-link into these with ?unlinked=1, so
	 * the value lives in the URL rather than component state.
	 */
	interface Props {
		checked: boolean;
		onchange: (value: boolean) => void;
	}

	let { checked, onchange }: Props = $props();
</script>

<label>
	<input
		type="checkbox"
		{checked}
		onchange={(e) => onchange(e.currentTarget.checked)}
	/>
	Unlinked only
</label>

<style>
	label {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.875rem;
		white-space: nowrap;
		cursor: pointer;
		color: var(--text-dim);
	}

	input {
		cursor: pointer;
	}
</style>
