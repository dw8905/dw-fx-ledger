export function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

export function formatDate(value: string) {
  const dateOnly = value.split("T")[0];
  const match = /^(?<year>\d{4})-(?<month>\d{2})-(?<day>\d{2})$/.exec(dateOnly);

  if (match?.groups) {
    const year = Number(match.groups.year);
    const month = Number(match.groups.month);
    const day = Number(match.groups.day);

    return `${year}. ${month}. ${day}.`;
  }

  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium"
  }).format(new Date(value));
}

export function formatCompactDate(value: string) {
  const dateOnly = value.split("T")[0];
  const match = /^(?<year>\d{4})-(?<month>\d{2})-(?<day>\d{2})$/.exec(dateOnly);

  if (match?.groups) {
    return `${match.groups.year.slice(2)}${match.groups.month}${match.groups.day}`;
  }

  const date = new Date(value);
  const year = String(date.getFullYear()).slice(2);
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}${month}${day}`;
}

export function formatKrw(value: number) {
  return new Intl.NumberFormat("ko-KR").format(value);
}

export function formatKrwCurrency(value: number) {
  return `₩${formatKrw(value)}`;
}

export function formatUsdCurrency(value: string | number) {
  return `$${new Intl.NumberFormat("ko-KR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(Number(value))}`;
}

export function formatKrwRate(value: string | number) {
  return `₩${new Intl.NumberFormat("ko-KR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(Number(value))}`;
}

export function formatDecimal(value: string, minimumFractionDigits = 2, maximumFractionDigits = 6) {
  return new Intl.NumberFormat("ko-KR", {
    minimumFractionDigits,
    maximumFractionDigits
  }).format(Number(value));
}
