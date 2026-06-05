export function isValidDateParts(year: string, month: string, day: string) {
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
  return value.length === 1 ? value.padStart(2, "0") : value;
}

export function combineDateParts(year: string, month: string, day: string) {
  return isValidDateParts(year, month, day) ? `${year}-${month}-${day}` : "";
}
