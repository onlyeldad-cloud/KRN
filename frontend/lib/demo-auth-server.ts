import { timingSafeEqual } from 'node:crypto';

export function bearerMatchesSecret(
  supplied: string,
  expected: string
): boolean {
  if (!expected || expected.length < 8) {
    return false;
  }
  const a = Buffer.from(supplied);
  const b = Buffer.from(expected);
  if (a.byteLength !== b.byteLength) {
    return false;
  }
  return timingSafeEqual(a, b);
}
