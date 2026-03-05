<script lang="ts">
	import { fade, fly } from "svelte/transition";
	import { marked } from "marked";
	import type { Ticket } from "$lib/tickets.js";
	import { STATUS_LABELS } from "$lib/tickets.js";

	const MIN_WIDTH = 320;
	const DEFAULT_WIDTH = 672;

	let { ticket, onclose, width = DEFAULT_WIDTH, onwidthchange }: {
		ticket: Ticket;
		onclose: () => void;
		width?: number;
		onwidthchange?: (width: number) => void;
	} = $props();

	const renderedBody = $derived(marked.parse(ticket.body) as string);

	let activeWidth: number | null = $state(null);
	let dragging = $state(false);
	const displayWidth = $derived(activeWidth ?? width);

	function handlePointerDown(event: PointerEvent) {
		dragging = true;
		activeWidth = width;
		(event.target as HTMLElement).setPointerCapture(event.pointerId);
		event.preventDefault();
	}

	function handlePointerMove(event: PointerEvent) {
		if (!dragging) return;
		activeWidth = Math.max(MIN_WIDTH, window.innerWidth - event.clientX);
	}

	function handlePointerUp() {
		dragging = false;
		if (activeWidth !== null) onwidthchange?.(activeWidth);
		activeWidth = null;
	}
</script>

<svelte:window onkeydown={(e) => { if (e.key === "Escape") onclose(); }} />

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="fixed inset-0 z-50 flex">
	<!-- Backdrop -->
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<div
		class="absolute inset-0 bg-black/40 backdrop-blur-sm"
		transition:fade={{ duration: 200 }}
		onclick={onclose}
	></div>

	<!-- Drawer panel -->
	<aside
		class="relative ml-auto flex h-full flex-col bg-surface-800 shadow-xl"
		style="width: min({displayWidth}px, 100vw)"
		transition:fly={{ x: DEFAULT_WIDTH, duration: 300 }}
	>
		<!-- Resize handle -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div
			class="absolute inset-y-0 left-0 w-1.5 cursor-col-resize transition-colors hover:bg-accent/50 {dragging ? 'bg-accent/50' : ''}"
			onpointerdown={handlePointerDown}
			onpointermove={handlePointerMove}
			onpointerup={handlePointerUp}
		></div>
		<div class="flex items-center justify-between border-b border-border-subtle p-4">
			<div>
				<span class="text-xs text-text-muted">{ticket.id}</span>
				<h2 class="text-lg font-semibold text-text-primary">{ticket.title}</h2>
			</div>
			<button
				class="rounded p-1 text-text-muted transition-colors hover:bg-surface-700 hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/20 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-800"
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

		<div class="prose prose-invert max-w-none flex-1 overflow-y-auto p-4 text-sm text-text-secondary">
			<!-- eslint-disable-next-line svelte/no-at-html-tags -- intentional: rendering trusted markdown from local ticket files -->
			{@html renderedBody}
		</div>
	</aside>
</div>
