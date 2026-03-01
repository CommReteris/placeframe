<script lang="ts">
	import { dndzone, type DndEvent } from "svelte-dnd-action";
	import type { Ticket, Status } from "$lib/tickets.js";
	import { STATUS_LABELS } from "$lib/tickets.js";
	import Card from "./Card.svelte";

	let {
		status,
		tickets,
		onselect,
		onconsider,
		onfinalize,
	}: {
		status: Status;
		tickets: (Ticket & { id: string })[];
		onselect: (ticket: Ticket) => void;
		onconsider: (status: Status, event: CustomEvent<DndEvent<Ticket & { id: string }>>) => void;
		onfinalize: (status: Status, event: CustomEvent<DndEvent<Ticket & { id: string }>>) => void;
	} = $props();

	const statusColors: Record<Status, string> = {
		blocked: "bg-status-blocked",
		"design-needed": "bg-status-design-needed",
		"plan-needed": "bg-status-plan-needed",
		ready: "bg-status-ready",
		done: "bg-status-done",
	};
</script>

<div class="flex min-w-56 flex-1 flex-col">
	<div class="mb-3 flex items-center gap-2">
		<div class="h-2.5 w-2.5 rounded-full {statusColors[status]}"></div>
		<h2 class="text-sm font-semibold text-text-secondary">{STATUS_LABELS[status]}</h2>
		<span class="text-xs text-text-muted">{tickets.length}</span>
	</div>
	<div
		class="flex min-h-16 flex-1 flex-col gap-2 rounded-xl border border-border-subtle bg-surface-900 p-2"
		use:dndzone={{ items: tickets, dropTargetStyle: {} }}
		onconsider={(event: CustomEvent<DndEvent<Ticket & { id: string }>>) => onconsider(status, event)}
		onfinalize={(event: CustomEvent<DndEvent<Ticket & { id: string }>>) => onfinalize(status, event)}
	>
		{#each tickets as ticket (ticket.id)}
			<Card {ticket} {onselect} />
		{/each}
	</div>
</div>
