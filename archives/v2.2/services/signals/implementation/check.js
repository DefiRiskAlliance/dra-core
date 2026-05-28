/**
 * Checks if a strategy would trigger a "decrease greatly" signal.
 * Uses the strategy score (0–10 numeric scale, v2.1 methodology).
 * Uses in-memory previous/current; replace with DB reads when shared DB is wired.
 * Run: node check.js
 */

/**
 * Determine if a score change should trigger an alert.
 * @param {{ numeric: number }} previous
 * @param {{ numeric: number }} current
 * @returns {{ alert: boolean, reasons: string[] }}
 */
function wouldAlert(previous, current) {
  if (!previous || !current) return { alert: false, reasons: ['missing previous or current score'] };

  const numericDrop = (previous.numeric || 0) - (current.numeric || 0);
  const belowThreshold = current.numeric < 4.0;

  const alert = numericDrop > 2.0 || belowThreshold;
  const reasons = [];
  if (numericDrop > 2.0) reasons.push(`numeric_drop_${numericDrop.toFixed(1)}`);
  if (belowThreshold) reasons.push('below_threshold');
  return { alert, reasons };
}

// Examples on the 0–10 scale
const prev = { numeric: 9.3 };
const curr = { numeric: 7.5 };
console.log('Example (9.3 -> 7.5):', wouldAlert(prev, curr));

const curr2 = { numeric: 3.5 };
console.log('Example (9.3 -> 3.5):', wouldAlert(prev, curr2));

module.exports = { wouldAlert };
