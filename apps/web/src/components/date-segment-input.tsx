"use client";

import { KeyboardEvent, useEffect, useRef, useState } from "react";
import { combineDateParts, isValidDateParts, padDateSegment } from "../lib/date-segments";

type DateSegmentInputProps = {
  id?: string;
  label: string;
  value: string;
  required?: boolean;
  onChange: (value: string) => void;
};

function onlyDigits(value: string, maxLength: number) {
  return value.replace(/\D/g, "").slice(0, maxLength);
}

function splitDate(value: string) {
  const [year = "", month = "", day = ""] = value.split("-");
  return { year, month, day };
}

export function DateSegmentInput({
  id,
  label,
  value,
  required = false,
  onChange
}: DateSegmentInputProps) {
  const yearRef = useRef<HTMLInputElement>(null);
  const monthRef = useRef<HTMLInputElement>(null);
  const dayRef = useRef<HTMLInputElement>(null);
  const { year: initialYear, month: initialMonth, day: initialDay } = splitDate(value);
  const [year, setYear] = useState(initialYear);
  const [month, setMonth] = useState(initialMonth);
  const [day, setDay] = useState(initialDay);
  const [touched, setTouched] = useState(false);

  useEffect(() => {
    if (value === "") {
      return;
    }

    const next = splitDate(value);
    setYear(next.year);
    setMonth(next.month);
    setDay(next.day);
  }, [value]);

  function emit(nextYear: string, nextMonth: string, nextDay: string) {
    onChange(combineDateParts(nextYear, nextMonth, nextDay));
  }

  function handleYearChange(nextValue: string) {
    const nextYear = onlyDigits(nextValue, 4);
    setYear(nextYear);
    emit(nextYear, month, day);
    if (nextYear.length === 4) {
      monthRef.current?.focus();
    }
  }

  function handleMonthChange(nextValue: string) {
    const nextMonth = onlyDigits(nextValue, 2);
    setMonth(nextMonth);
    emit(year, nextMonth, day);
    if (nextMonth.length === 2) {
      dayRef.current?.focus();
    }
  }

  function handleDayChange(nextValue: string) {
    const nextDay = onlyDigits(nextValue, 2);
    setDay(nextDay);
    emit(year, month, nextDay);
  }

  function handleMonthBlur() {
    const padded = padDateSegment(month);
    setMonth(padded);
    setTouched(true);
    emit(year, padded, day);
  }

  function handleDayBlur() {
    const padded = padDateSegment(day);
    setDay(padded);
    setTouched(true);
    emit(year, month, padded);
  }

  function handleBackspace(
    event: KeyboardEvent<HTMLInputElement>,
    currentValue: string,
    target: "year" | "month"
  ) {
    if (event.key !== "Backspace" || currentValue !== "") {
      return;
    }

    if (target === "month") {
      yearRef.current?.focus();
      return;
    }

    monthRef.current?.focus();
  }

  const showError = touched && (required || year || month || day) && !isValidDateParts(year, month, day);

  return (
    <label className="date-segment-field" id={id}>
      {label}
      <span className="date-segment-group">
        <input
          ref={yearRef}
          aria-label={`${label} 연도`}
          inputMode="numeric"
          placeholder="YYYY"
          value={year}
          onBlur={() => setTouched(true)}
          onChange={(event) => handleYearChange(event.target.value)}
        />
        <span>|</span>
        <input
          ref={monthRef}
          aria-label={`${label} 월`}
          inputMode="numeric"
          placeholder="MM"
          value={month}
          onBlur={handleMonthBlur}
          onChange={(event) => handleMonthChange(event.target.value)}
          onKeyDown={(event) => handleBackspace(event, month, "month")}
        />
        <span>|</span>
        <input
          ref={dayRef}
          aria-label={`${label} 일`}
          inputMode="numeric"
          placeholder="DD"
          value={day}
          onBlur={handleDayBlur}
          onChange={(event) => handleDayChange(event.target.value)}
          onKeyDown={(event) => handleBackspace(event, day, "year")}
        />
      </span>
      {showError ? <span className="field-error">올바른 날짜를 입력해주세요.</span> : null}
    </label>
  );
}
