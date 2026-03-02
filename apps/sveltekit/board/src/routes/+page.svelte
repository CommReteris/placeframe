<script lang="ts">
	import { page } from "$app/state";
	import { pushState, invalidateAll } from "$app/navigation";
	import { resolve } from "$app/paths";
	import type { PageData } from "./$types.js";
	import type { Ticket, Status } from "$lib/tickets.js";
	import Board from "$lib/components/Board.svelte";
	import SearchBar from "$lib/components/SearchBar.svelte";
	import DetailPanel from "$lib/components/DetailPanel.svelte";
	import { STATUSES } from "$lib/tickets.js";

	let { data }: { data: PageData } = $props();

	let searchTerm = $state("");
	let selectedTicket: Ticket | null = $state(null);
	let drawerWidth = $state(672);
	let epicFilter: string | null = $state(page.url.searchParams.get("epic"));

	const filteredColumns = $derived(() => {
		const term = searchTerm.toLowerCase();
		return Object.fromEntries(
			STATUSES.map((status) => [
				status,
				(data.columns[status] ?? []).filter((ticket) => {
					if (epicFilter && ticket.epic !== epicFilter) return false;
					if (term && !ticket.title.toLowerCase().includes(term) && !ticket.id.toLowerCase().includes(term))
						return false;
					return true;
				}),
			]),
		) as Record<Status, Ticket[]>;
	});

	function handleEpicChange(event: Event) {
		const select = event.target as HTMLSelectElement;
		epicFilter = select.value || null;
		const path = (epicFilter ? `/?epic=${encodeURIComponent(epicFilter)}` : "/") as "/";
		pushState(resolve(path), {});
	}

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
		<select
			class="rounded-lg border border-border-subtle bg-surface-800 px-3 py-2 text-sm text-text-primary focus:border-border-default focus:outline-none"
			onchange={handleEpicChange}
			value={epicFilter ?? ""}
			data-testid="epic-filter"
		>
			<option value="">All epics</option>
			{#each data.epics as epic (epic)}
				<option value={epic}>{epic}</option>
			{/each}
		</select>
	</header>

	<main class="flex-1 overflow-auto">
		<Board
			columns={filteredColumns()}
			onselect={handleSelect}
			onstatuschange={handleStatusChange}
		/>
	</main>

	{#if selectedTicket}
		<DetailPanel ticket={selectedTicket} onclose={handleCloseDetail} width={drawerWidth} onwidthchange={(w) => { drawerWidth = w; }} />
	{/if}
</div>
