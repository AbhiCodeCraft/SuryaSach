export const orientations = [
  { label: "South", value: "180" },
  { label: "South-East", value: "135" },
  { label: "South-West", value: "225" },
  { label: "East", value: "90" },
  { label: "West", value: "270" },
  { label: "North", value: "0" },
  { label: "North-East", value: "45" },
  { label: "North-West", value: "315" },
];

export function orientationLabel(value: number | null): string {
  if (value === null) return "Not known";
  const direction = orientations.find((item) => Number(item.value) === value);
  return direction ? `${direction.label} (${value}°)` : `${value}° clockwise from true north`;
}

export function todayInIndia(): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit",
  }).formatToParts(new Date());
  return ["year", "month", "day"].map((type) => parts.find((part) => part.type === type)?.value).join("-");
}
