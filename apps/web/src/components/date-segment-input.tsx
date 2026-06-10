"use client";

import { KeyboardEvent, useEffect, useRef, useState } from "react";
import { combineDateParts, isValidDateParts, padDateSegment } from "../lib/date-segments";

type DateSegmentInputProps = {
  /** 연/월/일을 분리 입력하되 부모에는 YYYY-MM-DD 문자열 하나로 전달합니다. */
  id?: string;
  label: string;
  value: string;
  required?: boolean;
  onChange: (value: string) => void;
};

function onlyDigits(value: string, maxLength: number) {
  /** 사용자가 붙여 넣은 값에서 숫자만 남기고 입력 칸 길이에 맞게 자릅니다. */

  return value.replace(/\D/g, "").slice(0, maxLength);
}

function splitDate(value: string) {
  /** YYYY-MM-DD 문자열을 연/월/일 상태값으로 나눕니다. */

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
  /** 날짜를 세 칸으로 입력받아 자리수 이동과 유효성 표시를 처리합니다. */

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
    /** 세 칸의 현재 값을 합쳐 유효한 날짜일 때만 부모 onChange로 전달합니다. */

    onChange(combineDateParts(nextYear, nextMonth, nextDay));
  }

  function handleYearChange(nextValue: string) {
    /** 연도 입력이 4자리가 되면 월 입력으로 포커스를 이동합니다. */

    const nextYear = onlyDigits(nextValue, 4);
    setYear(nextYear);
    emit(nextYear, month, day);
    if (nextYear.length === 4) {
      monthRef.current?.focus();
    }
  }

  function handleMonthChange(nextValue: string) {
    /** 월 입력이 2자리가 되면 일 입력으로 포커스를 이동합니다. */

    const nextMonth = onlyDigits(nextValue, 2);
    setMonth(nextMonth);
    emit(year, nextMonth, day);
    if (nextMonth.length === 2) {
      dayRef.current?.focus();
    }
  }

  function handleDayChange(nextValue: string) {
    /** 일 입력은 숫자 두 자리로 제한하고 부모 값을 갱신합니다. */

    const nextDay = onlyDigits(nextValue, 2);
    setDay(nextDay);
    emit(year, month, nextDay);
  }

  function handleMonthBlur() {
    /** 월 입력에서 벗어나면 한 자리 값을 두 자리로 보정합니다. */

    const padded = padDateSegment(month);
    setMonth(padded);
    setTouched(true);
    emit(year, padded, day);
  }

  function handleDayBlur() {
    /** 일 입력에서 벗어나면 한 자리 값을 두 자리로 보정합니다. */

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
    /** 빈 월/일 칸에서 Backspace를 누르면 이전 칸으로 포커스를 되돌립니다. */

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
