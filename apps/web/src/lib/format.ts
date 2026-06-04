export function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

export function formatDate(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium"
  }).format(new Date(`${value}T00:00:00`));
}

export function formatKrw(value: number) {
  return new Intl.NumberFormat("ko-KR").format(value);
}

export function formatDecimal(value: string, minimumFractionDigits = 2, maximumFractionDigits = 6) {
  return new Intl.NumberFormat("ko-KR", {
    minimumFractionDigits,
    maximumFractionDigits
  }).format(Number(value));
}
