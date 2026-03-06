const KNOWN_EPIC_COLORS: Record<string, string> = {
	board: "oklch(0.7 0.12 200)",
	ci: "oklch(0.7 0.12 140)",
	zed: "oklch(0.7 0.12 320)",
	specs: "oklch(0.7 0.12 60)",
	"skills-audit": "oklch(0.7 0.12 270)",
};

function hashString(string_: string): number {
	let hash = 0;
	for (let i = 0; i < string_.length; i++) {
		hash = ((hash << 5) - hash + string_.charCodeAt(i)) | 0;
	}
	return Math.abs(hash);
}

export function epicColor(epic: string): string {
	const known = KNOWN_EPIC_COLORS[epic];
	if (known) return known;
	const hue = hashString(epic) % 360;
	return `oklch(0.7 0.12 ${hue})`;
}
