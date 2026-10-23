/** 18000 -> "₹180", 18050 -> "₹180.50". Display only; totals always come from the backend. */
export function rupees(paise: number): string {
  const whole = Math.floor(paise / 100);
  const rest = paise % 100;
  return `₹${whole.toLocaleString("en-IN")}${rest ? `.${String(rest).padStart(2, "0")}` : ""}`;
}
