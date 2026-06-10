export function isValidDateParts(year: string, month: string, day: string) {
  /** 연/월/일 세 입력값이 실제 존재하는 날짜인지 검증합니다. */

  if (!/^\d{4}$/.test(year) || !/^\d{2}$/.test(month) || !/^\d{2}$/.test(day)) {
    return false;
  }

  const numericYear = Number(year);
  if (numericYear < 1900 || numericYear > 2100) {
    return false;
  }

  const date = new Date(`${year}-${month}-${day}T00:00:00`);
  return (
    date.getFullYear() === numericYear &&
    date.getMonth() + 1 === Number(month) &&
    date.getDate() === Number(day)
  );
}

export function padDateSegment(value: string) {
  /** 월/일 한 자리 입력을 두 자리 문자열로 맞춥니다. */

  return value.length === 1 ? value.padStart(2, "0") : value;
}

export function combineDateParts(year: string, month: string, day: string) {
  /** 유효한 연/월/일 조합이면 API가 받는 YYYY-MM-DD 문자열로 합칩니다. */

  return isValidDateParts(year, month, day) ? `${year}-${month}-${day}` : "";
}
