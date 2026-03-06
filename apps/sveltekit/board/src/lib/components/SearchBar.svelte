<script lang="ts">
	let { value = $bindable("") }: { value: string } = $props();
</script>

<input
	type="text"
	placeholder="Search tickets..."
	bind:value
	class="w-full max-w-sm rounded-lg border border-border-subtle bg-surface-800 px-3 py-2 text-sm text-text-primary placeholder:text-text-muted transition-colors hover:border-border-default focus:border-border-default focus:outline-none focus-visible:ring-2 focus-visible:ring-white/20"
/>
