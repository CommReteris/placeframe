<script lang="ts">
	import type { Ticket, Status } from "$lib/tickets.js";
	import { STATUS_LABELS } from "$lib/tickets.js";
	import Card from "./Card.svelte";

	let {
		status,
		tickets,
		onselect,
		onticketdrop,
	}: {
		status: Status;
		tickets: Ticket[];
		onselect: (ticket: Ticket) => void;
		onticketdrop: (ticketId: string, newStatus: Status) => void;
	} = $props();

	let dragOverCount = $state(0);
	let isDragOver = $derived(dragOverCount > 0);

	const statusColors: Record<Status, string> = {
		blocked: "bg-status-blocked",
		"design-needed": "bg-status-design-needed",
		"plan-needed": "bg-status-plan-needed",
		ready: "bg-status-ready",
		"in-review": "bg-status-in-review",
		done: "bg-status-done",
	};
</script>

<div class="flex min-w-72 flex-1 flex-col">
	<div class="mb-3 flex items-center gap-2">
		<div class="h-2.5 w-2.5 rounded-full {statusColors[status]}"></div>
		<h2 class="text-sm font-semibold text-text-secondary">{STATUS_LABELS[status]}</h2>
		<span class="text-xs text-text-muted">{tickets.length}</span>
	</div>
	<div
		role="listbox"
		tabindex="0"
		aria-label="{STATUS_LABELS[status]} tickets"
		class="flex min-h-16 flex-1 flex-col gap-2 rounded-xl border bg-surface-900 p-2 transition-colors {isDragOver ? 'border-border-default bg-surface-800' : 'border-border-subtle'}"
		ondragover={(event: DragEvent) => {
			event.preventDefault();
			if (event.dataTransfer) event.dataTransfer.dropEffect = "move";
		}}
		ondragenter={(event: DragEvent) => {
			event.preventDefault();
			dragOverCount++;
		}}
		ondragleave={() => {
			dragOverCount--;
		}}
		ondrop={(event: DragEvent) => {
			event.preventDefault();
			dragOverCount = 0;
			const ticketId = event.dataTransfer?.getData("text/plain");
			if (ticketId && !tickets.some((t) => t.id === ticketId)) {
				onticketdrop(ticketId, status);
			}
		}}
	>
		{#each tickets as ticket (ticket.id)}
			<Card {ticket} {onselect} />
		{/each}
	</div>
</div>
