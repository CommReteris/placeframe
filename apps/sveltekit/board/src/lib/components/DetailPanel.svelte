<script lang="ts">
	import { marked } from "marked";
	import type { Ticket } from "$lib/tickets.js";
	import { STATUS_LABELS } from "$lib/tickets.js";

	let { ticket, onclose }: { ticket: Ticket; onclose: () => void } = $props();

	const renderedBody = $derived(marked.parse(ticket.body) as string);
</script>

<aside class="flex h-full w-96 flex-col border-l border-border-default bg-surface-800">
	<div class="flex items-center justify-between border-b border-border-subtle p-4">
		<div>
			<span class="text-xs text-text-muted">{ticket.id}</span>
			<h2 class="text-lg font-semibold text-text-primary">{ticket.title}</h2>
		</div>
		<button
			class="rounded p-1 text-text-muted hover:bg-surface-700 hover:text-text-primary"
			onclick={onclose}
			aria-label="Close detail panel"
		>
			<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<line x1="18" y1="6" x2="6" y2="18"></line>
				<line x1="6" y1="6" x2="18" y2="18"></line>
			</svg>
		</button>
	</div>

	<div class="flex gap-4 border-b border-border-subtle px-4 py-3 text-sm">
		<div>
			<span class="text-text-muted">Status:</span>
			<span class="text-text-primary">{STATUS_LABELS[ticket.status]}</span>
		</div>
		{#if ticket.dependsOn.length > 0}
			<div>
				<span class="text-text-muted">Depends on:</span>
				<span class="text-text-primary">{ticket.dependsOn.join(", ")}</span>
			</div>
		{/if}
	</div>

	<div class="prose prose-invert flex-1 overflow-y-auto p-4 text-sm text-text-secondary">
		<!-- eslint-disable-next-line svelte/no-at-html-tags -- intentional: rendering trusted markdown from local ticket files -->
		{@html renderedBody}
	</div>
</aside>
