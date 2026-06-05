export function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

export function formatDate(value: string) {
  return new Intl.DateTimeFormat("ko-KR", { dateStyle: "medium" }).format(new Date(value));
}

export function formatNumber(value: number | string) {
  return new Intl.NumberFormat("ko-KR").format(Number(value));
}

export function formatKrw(value: number) {
  return `${formatNumber(value)}원`;
}

export function formatUsd(value: number | string) {
  return `$${new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 6
  }).format(Number(value))}`;
}
