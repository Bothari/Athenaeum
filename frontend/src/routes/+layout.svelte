<script lang="ts">
	import '../app.css';
	import Toast from '$lib/components/Toast.svelte';
	import { auth } from '$lib/stores/auth.svelte';
	import { covers } from '$lib/stores/covers.svelte';
	import { theme } from '$lib/stores/theme.svelte';

	let { children } = $props();

	// Runs once for the app's lifetime. Every route reads auth state rather than
	// re-fetching it, which is why the guard can be synchronous downstream.
	$effect(() => {
		theme.init();
		auth.load();
		// Cover aspect ratio comes from the ABS library settings.
		covers.init();
	});
</script>

<svelte:head>
	<title>Athenaeum</title>
</svelte:head>

{@render children()}

<Toast />
