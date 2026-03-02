<script lang="ts">
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
</script>

<div class="flex gap-6 overflow-x-auto p-4">
	{#each STATUSES as status (status)}
		<Column {status} tickets={columns[status] ?? []} {onselect} onticketdrop={onstatuschange} />
	{/each}
</div>
