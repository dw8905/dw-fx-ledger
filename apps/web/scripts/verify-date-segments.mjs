import {
  combineDateParts,
  isValidDateParts,
  padDateSegment
} from "../src/lib/date-segments.ts";

if (combineDateParts("2025", "03", "06") !== "2025-03-06") {
  throw new Error("Expected YYYY-MM-DD combination");
}

if (padDateSegment("3") !== "03") {
  throw new Error("Expected single digit month/day padding");
}

if (isValidDateParts("2025", "02", "30")) {
  throw new Error("Expected invalid calendar date to be rejected");
}

console.log("date segments ok");
