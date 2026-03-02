<script lang="ts">
	import { SvelteSet } from "svelte/reactivity";
	import type { Ticket, Status } from "$lib/tickets.js";
	import { STATUS_LABELS, groupByEpic } from "$lib/tickets.js";
	import { epicColor } from "$lib/epic-colors.js";
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

	const epicGroups = $derived(groupByEpic(tickets));
	const hasMultipleGroups = $derived(epicGroups.length > 1);

	const collapsedEpics = new SvelteSet<string>();

	function collapseKey(epic: string | null): string {
		return epic ?? "__ungrouped";
	}

	function toggleEpic(epic: string | null): void {
		const key = collapseKey(epic);
		if (collapsedEpics.has(key)) {
			collapsedEpics.delete(key);
		} else {
			collapsedEpics.add(key);
		}
	}

	const statusColors: Record<Status, string> = {
		blocked: "bg-status-blocked",
		"design-needed": "bg-status-design-needed",
		"plan-needed": "bg-status-plan-needed",
		ready: "bg-status-ready",
		"in-review": "bg-status-in-review",
		done: "bg-status-done",
	};
</script>

<div class="flex min-w-72 flex-1 flex-col" data-testid="column-{status}">
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
		{#each epicGroups as group (group.epic)}
			{#if group.epic !== null}
				<button
					class="flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-text-muted hover:bg-surface-700"
					onclick={() => toggleEpic(group.epic)}
					data-testid="epic-section-{group.epic}"
				>
					<span class="inline-block h-2 w-2 rounded-full" style="background-color: {epicColor(group.epic)}"></span>
					<span>{collapsedEpics.has(collapseKey(group.epic)) ? "\u25B6" : "\u25BC"}</span>
					<span>{group.epic}</span>
					<span class="text-text-muted">({group.tickets.length})</span>
				</button>
			{:else if hasMultipleGroups}
				<button
					class="flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-text-muted hover:bg-surface-700"
					onclick={() => toggleEpic(null)}
					data-testid="epic-section-ungrouped"
				>
					<span>{collapsedEpics.has(collapseKey(null)) ? "\u25B6" : "\u25BC"}</span>
					<span>ungrouped</span>
					<span class="text-text-muted">({group.tickets.length})</span>
				</button>
			{/if}
			{#if !collapsedEpics.has(collapseKey(group.epic))}
				{#each group.tickets as ticket (ticket.id)}
					<Card {ticket} {onselect} />
				{/each}
			{/if}
		{/each}
	</div>
</div>
