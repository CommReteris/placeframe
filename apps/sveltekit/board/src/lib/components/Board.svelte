<script lang="ts">
	import type { DndEvent } from "svelte-dnd-action";
	import type { Ticket, Status } from "$lib/tickets.js";
	import { STATUSES } from "$lib/tickets.js";
	import Column from "./Column.svelte";

	let {
		columns,
		onselect,
		onstatuschange,
	}: {
		columns: Record<Status, Ticket[]>;
		onselect: (ticket: Ticket) => void;
		onstatuschange: (ticketId: string, newStatus: Status) => void;
	} = $props();

	let columnItems: Record<Status, (Ticket & { id: string })[]> = $derived(
		Object.fromEntries(
			STATUSES.map((status) => [status, [...(columns[status] ?? [])]])
		) as Record<Status, (Ticket & { id: string })[]>
	);

	function handleConsider(
		status: Status,
		event: CustomEvent<DndEvent<Ticket & { id: string }>>,
	) {
		columnItems[status] = event.detail.items;
	}

	function handleFinalize(
		status: Status,
		event: CustomEvent<DndEvent<Ticket & { id: string }>>,
	) {
		columnItems[status] = event.detail.items;
		const movedTicket = event.detail.items.find(
			(item: Ticket & { id: string }) => !columns[status]?.some((t: Ticket) => t.id === item.id)
		);
		if (movedTicket) {
			onstatuschange(movedTicket.id, status);
		}
	}
</script>

<div class="flex gap-4 overflow-x-auto p-4">
	{#each STATUSES as status (status)}
		<Column
			{status}
			tickets={columnItems[status] ?? []}
			{onselect}
			onconsider={handleConsider}
			onfinalize={handleFinalize}
		/>
	{/each}
</div>
