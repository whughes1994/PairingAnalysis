/* MongoDB Playground - DEBUG QUERIES
 *
 * This file helps you debug and see console output
 *
 * To run:
 * 1. Select entire file (Cmd+A)
 * 2. Press Cmd+Enter (Mac) or Ctrl+Enter (Windows)
 * 3. Look at OUTPUT panel at bottom AND Playground Result panel
 */

use('airline_pairings');

// ============================================================================
// DEBUG 1: Check Database Stats
// ============================================================================
console.log("="*60);
console.log("DATABASE STATISTICS");
console.log("="*60);

const pairingCount = db.pairings.countDocuments({});
const legCount = db.legs.countDocuments({});
const bidCount = db.bid_periods.countDocuments({});

console.log(`Pairings: ${pairingCount}`);
console.log(`Legs: ${legCount}`);
console.log(`Bid Periods: ${bidCount}`);

// ============================================================================
// DEBUG 2: Sample Pairing (See Structure)
// ============================================================================
console.log("\n" + "="*60);
console.log("SAMPLE PAIRING STRUCTURE");
console.log("="*60);

const sample = db.pairings.findOne({});
console.log("Pairing ID:", sample.id);
console.log("Fleet:", sample.fleet);
console.log("Base:", sample.base);
console.log("Category:", sample.pairing_category);
console.log("Credit (hours):", (sample.credit_minutes / 60).toFixed(2));
console.log("Days:", sample.days);
console.log("Duty Periods:", sample.duty_period_count);

// ============================================================================
// DEBUG 3: Check Layover Station Status (IMPORTANT!)
// ============================================================================
console.log("\n" + "="*60);
console.log("LAYOVER STATION STATUS");
console.log("="*60);

const legSample = db.legs.findOne({});
console.log("Sample leg departure:", legSample.departure_station);
console.log("Sample leg arrival:", legSample.arrival_station);
console.log("Sample leg layover_station:", legSample.layover_station);
console.log("Sample leg origin_station:", legSample.origin_station);

const legsWithLayover = db.legs.countDocuments({ layover_station: { $ne: null } });
const legsTotal = db.legs.countDocuments({});

console.log(`\nLegs with layover_station: ${legsWithLayover} / ${legsTotal}`);

if (legsWithLayover === 0) {
  console.log("\n⚠️  WARNING: No layover stations populated!");
  console.log("You need to run: python3 fix_layover_stations_v2.py");
} else {
  console.log("✅ Layover stations are populated!");
}

// ============================================================================
// DEBUG 4: Fleet Breakdown
// ============================================================================
console.log("\n" + "="*60);
console.log("FLEET BREAKDOWN");
console.log("="*60);

const fleets = db.pairings.distinct('fleet');
console.log("Available fleets:", fleets.join(", "));

const fleetStats = db.pairings.aggregate([
  {
    $group: {
      _id: '$fleet',
      count: { $sum: 1 },
      avg_credit: { $avg: '$credit_minutes' }
    }
  },
  { $sort: { count: -1 } }
]).toArray();

fleetStats.forEach(stat => {
  console.log(`  ${stat._id}: ${stat.count} pairings, avg ${(stat.avg_credit/60).toFixed(1)}h credit`);
});

// ============================================================================
// DEBUG 5: Sample Different Pairings (Not Always Same One)
// ============================================================================
console.log("\n" + "="*60);
console.log("RANDOM SAMPLE PAIRINGS (Different Each Time)");
console.log("="*60);

const randomSamples = db.pairings.aggregate([
  { $sample: { size: 5 } },
  { $project: { id: 1, fleet: 1, pairing_category: 1, credit_minutes: 1 } }
]).toArray();

randomSamples.forEach((p, idx) => {
  console.log(`${idx+1}. ${p.id} - ${p.fleet} - ${p.pairing_category} - ${(p.credit_minutes/60).toFixed(1)}h`);
});

// ============================================================================
// DEBUG 6: If Layovers Exist, Show Top Cities
// ============================================================================
if (legsWithLayover > 0) {
  console.log("\n" + "="*60);
  console.log("TOP 10 LAYOVER CITIES");
  console.log("="*60);

  const topLayovers = db.legs.aggregate([
    { $match: { layover_station: { $ne: null } } },
    { $group: { _id: '$layover_station', count: { $sum: 1 } } },
    { $sort: { count: -1 } },
    { $limit: 10 }
  ]).toArray();

  topLayovers.forEach((city, idx) => {
    console.log(`${idx+1}. ${city._id}: ${city.count} layovers`);
  });
}

// ============================================================================
// DEBUG 7: High-Value Pairings
// ============================================================================
console.log("\n" + "="*60);
console.log("HIGH-VALUE PAIRINGS (>20 hours credit)");
console.log("="*60);

const highValue = db.pairings.find(
  { credit_minutes: { $gt: 1200 } },
  { id: 1, fleet: 1, pairing_category: 1, credit_minutes: 1 }
).sort({ credit_minutes: -1 }).limit(5).toArray();

if (highValue.length > 0) {
  highValue.forEach((p, idx) => {
    console.log(`${idx+1}. ${p.id} - ${p.fleet} - ${(p.credit_minutes/60).toFixed(1)}h - ${p.pairing_category}`);
  });
} else {
  console.log("No high-value pairings found");
}

// ============================================================================
// DEBUG 8: Categories
// ============================================================================
console.log("\n" + "="*60);
console.log("TOP 10 PAIRING CATEGORIES");
console.log("="*60);

const categories = db.pairings.aggregate([
  { $group: { _id: '$pairing_category', count: { $sum: 1 } } },
  { $sort: { count: -1 } },
  { $limit: 10 }
]).toArray();

categories.forEach((cat, idx) => {
  console.log(`${idx+1}. ${cat._id}: ${cat.count} pairings`);
});

// ============================================================================
// DONE
// ============================================================================
console.log("\n" + "="*60);
console.log("✅ DEBUG COMPLETE");
console.log("="*60);
console.log("\nCheck the OUTPUT panel (bottom) for all console.log messages!");
console.log("The Playground Result shows the last query result.");

// Return summary for Playground Result panel
({
  summary: "Debug Complete - Check OUTPUT panel for detailed console logs",
  stats: {
    pairings: pairingCount,
    legs: legCount,
    bid_periods: bidCount,
    layovers_populated: legsWithLayover > 0,
    fleets: fleets
  }
});