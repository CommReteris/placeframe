<script lang="ts">
	import { invalidateAll } from "$app/navigation";
	import type { PageData } from "./$types.js";
	import type { Ticket, Status } from "$lib/tickets.js";
	import Board from "$lib/components/Board.svelte";
	import SearchBar from "$lib/components/SearchBar.svelte";
	import DetailPanel from "$lib/components/DetailPanel.svelte";
	import { STATUSES } from "$lib/tickets.js";

	let { data }: { data: PageData } = $props();

	let searchTerm = $state("");
	let selectedTicket: Ticket | null = $state(null);

	const filteredColumns = $derived(() => {
		const term = searchTerm.toLowerCase();
		if (!term) return data.columns;
		return Object.fromEntries(
			STATUSES.map((status) => [
				status,
				(data.columns[status] ?? []).filter(
					(ticket) =>
						ticket.title.toLowerCase().includes(term) ||
						ticket.id.toLowerCase().includes(term),
				),
			]),
		) as Record<Status, Ticket[]>;
	});

	async function handleStatusChange(ticketId: string, newStatus: Status) {
		await fetch(`/api/tickets/${ticketId}`, {
			method: "PATCH",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ status: newStatus }),
		});
		await invalidateAll();
	}

	function handleSelect(ticket: Ticket) {
		selectedTicket = ticket;
	}

	function handleCloseDetail() {
		selectedTicket = null;
	}
</script>

<svelte:head>
	<title>Placeframe Board</title>
</svelte:head>

<div class="flex h-screen flex-col">
	<header class="flex items-center gap-4 border-b border-border-default bg-surface-800 px-4 py-3">
		<h1 class="text-lg font-bold text-text-primary">Placeframe Board</h1>
		<SearchBar bind:value={searchTerm} />
	</header>

	<div class="flex flex-1 overflow-hidden">
		<main class="flex-1 overflow-auto">
			<Board
				columns={filteredColumns()}
				onselect={handleSelect}
				onstatuschange={handleStatusChange}
			/>
		</main>

		{#if selectedTicket}
			<DetailPanel ticket={selectedTicket} onclose={handleCloseDetail} />
		{/if}
	</div>
</div>
