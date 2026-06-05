import {
  combineDateParts,
  isValidDateParts,
  padDateSegment
} from "../src/lib/date-segments.ts";
import { formatDate } from "../src/lib/format.ts";

if (combineDateParts("2025", "03", "06") !== "2025-03-06") {
  throw new Error("Expected YYYY-MM-DD combination");
}

if (padDateSegment("3") !== "03") {
  throw new Error("Expected single digit month/day padding");
}

if (isValidDateParts("2025", "02", "30")) {
  throw new Error("Expected invalid calendar date to be rejected");
}

if (isValidDateParts("2926", "06", "04")) {
  throw new Error("Expected unrealistic year to be rejected");
}

if (formatDate("2026-06-04") !== "2026. 6. 4.") {
  throw new Error("Expected date-only API value to keep the 2026 year");
}

if (formatDate("2026-06-04T00:00:00Z") !== "2026. 6. 4.") {
  throw new Error("Expected ISO datetime API value to keep the 2026 date");
}

if (formatDate("2026-06-04").startsWith("2926")) {
  throw new Error("Date formatter must not mutate the year");
}

console.log("date segments and format ok");
