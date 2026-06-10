export function formatDateTime(value: string) {
  /** 관리자 표에서 ISO 날짜/시간을 한국어 날짜와 짧은 시간으로 표시합니다. */

  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

export function formatDate(value: string) {
  /** 관리자 화면에서 날짜만 필요한 값을 한국어 날짜로 표시합니다. */

  return new Intl.DateTimeFormat("ko-KR", { dateStyle: "medium" }).format(new Date(value));
}

export function formatNumber(value: number | string) {
  /** 숫자 또는 숫자 문자열에 천 단위 콤마를 붙입니다. */

  return new Intl.NumberFormat("ko-KR").format(Number(value));
}

export function formatKrw(value: number) {
  /** 원화 금액을 숫자 콤마와 '원' 단위로 표시합니다. */

  return `${formatNumber(value)}원`;
}

export function formatUsd(value: number | string) {
  /** USD 금액을 달러 기호와 최대 6자리 소수로 표시합니다. */

  return `$${new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 6
  }).format(Number(value))}`;
}
