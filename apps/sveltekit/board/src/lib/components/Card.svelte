<script lang="ts">
	import type { Ticket } from "$lib/tickets.js";
	import { epicColor } from "$lib/epic-colors.js";

	let { ticket, onselect }: { ticket: Ticket; onselect: (ticket: Ticket) => void } = $props();
</script>

<button
	data-testid="card-{ticket.id}"
	class="w-full rounded-lg border border-border-subtle bg-surface-800 px-4 py-3 text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-border-default hover:bg-surface-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/20 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-900 active:scale-[0.98] active:duration-75"
	draggable="true"
	ondragstart={(event: DragEvent) => {
		event.dataTransfer?.setData("text/plain", ticket.id);
		if (event.dataTransfer) event.dataTransfer.effectAllowed = "move";
	}}
	onclick={() => onselect(ticket)}
>
	<div class="mb-1 flex items-center gap-2">
		<span class="text-xs font-medium text-text-muted">{ticket.id}</span>
		{#if ticket.epic}
			<span
				class="rounded-full px-2 py-0.5 text-[10px] font-medium leading-tight text-surface-900"
				style="background-color: {epicColor(ticket.epic)}"
				data-testid="epic-chip-{ticket.epic}"
			>
				{ticket.epic}
			</span>
		{/if}
		{#if ticket.dependsOn.length > 0}
			<span class="text-xs text-text-muted" title="Dependencies: {ticket.dependsOn.join(', ')}">
				{ticket.dependsOn.length} dep{ticket.dependsOn.length > 1 ? "s" : ""}
			</span>
		{/if}
	</div>
	<div class="text-base text-text-primary">{ticket.title}</div>
</button>
