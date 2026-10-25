const MEMBER_COLORS = ["#2457c5", "#7a4ea3", "#c47b2b", "#b44b5a"];
const EVERYONE = "#6f6256";

export function personColor(memberId: string | null, memberIndex: number): string {
  if (memberId == null) {
    return EVERYONE;
  }
  return MEMBER_COLORS[memberIndex % MEMBER_COLORS.length] ?? MEMBER_COLORS[0];
}
