export function formatDateTime(value: string) {
  /** ISO 날짜/시간 문자열을 한국어 중간 길이 날짜와 짧은 시간으로 표시합니다. */

  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

export function formatDate(value: string) {
  /** 날짜만 필요한 화면에서 2026. 6. 7. 형태로 표시합니다. */

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
  /** FX 원장처럼 좁은 칸에서 날짜를 YYMMDD 형태로 표시합니다. */

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
  /** 원화 숫자를 통화 기호 없이 천 단위 콤마만 붙여 표시합니다. */

  return new Intl.NumberFormat("ko-KR").format(value);
}

export function formatKrwCurrency(value: number) {
  /** 원화 숫자 앞에 ₩ 기호를 붙여 금액으로 표시합니다. */

  return `₩${formatKrw(value)}`;
}

export function formatUsdCurrency(value: string | number) {
  /** USD 금액을 소수점 둘째 자리까지 고정해 표시합니다. */

  return `$${new Intl.NumberFormat("ko-KR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(Number(value))}`;
}

export function formatForeignCurrency(value: string | number, currencyCode: string) {
  /** USD/JPY 같은 외화 금액을 통화 기호와 적절한 소수 자릿수로 표시합니다. */

  const isJpy = currencyCode === "JPY";
  const symbol = isJpy ? "¥" : "$";
  return `${symbol}${new Intl.NumberFormat("ko-KR", {
    minimumFractionDigits: isJpy ? 0 : 2,
    maximumFractionDigits: isJpy ? 0 : 2
  }).format(Number(value))}`;
}

export function formatKrwRate(value: string | number) {
  /** 환율을 원화 기호와 소수점 둘째 자리로 표시합니다. */

  return `₩${new Intl.NumberFormat("ko-KR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(Number(value))}`;
}

export function formatDecimal(value: string, minimumFractionDigits = 2, maximumFractionDigits = 6) {
  /** Decimal 문자열을 화면 용도에 맞는 소수 자릿수로 포맷합니다. */

  return new Intl.NumberFormat("ko-KR", {
    minimumFractionDigits,
    maximumFractionDigits
  }).format(Number(value));
}
