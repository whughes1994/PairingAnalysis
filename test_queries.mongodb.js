// MongoDB Playground - Test Different Queries
// Make sure MongoDB is running and you're connected in VS Code

use('airline_pairings');

// ============================================================================
// QUERY 1: Count all pairings
// ============================================================================
db.pairings.countDocuments({});

// ============================================================================
// QUERY 2: Count by fleet (should show different fleets)
// ============================================================================
db.pairings.aggregate([
  {
    $group: {
      _id: '$fleet',
      count: { $sum: 1 }
    }
  },
  { $sort: { count: -1 } }
]);

// ============================================================================
// QUERY 3: Find multiple 737 pairings (not just one)
// ============================================================================
db.pairings.find(
  { fleet: '737' },
  { id: 1, pairing_category: 1, credit_minutes: 1, fleet: 1 }
).limit(10);

// ============================================================================
// QUERY 4: High-value pairings (different results each time if sorted)
// ============================================================================
db.pairings.find(
  { credit_minutes: { $gt: 1200 } },
  { id: 1, pairing_category: 1, credit_minutes: 1, days: 1 }
).sort({ credit_minutes: -1 }).limit(10);

// ============================================================================
// QUERY 5: Top routes (should show variety)
// ============================================================================
db.legs.aggregate([
  {
    $match: {
      departure_station: { $ne: null },
      arrival_station: { $ne: null }
    }
  },
  {
    $group: {
      _id: {
        from: '$departure_station',
        to: '$arrival_station'
      },
      count: { $sum: 1 }
    }
  },
  { $sort: { count: -1 } },
  { $limit: 10 }
]);

// ============================================================================
// QUERY 6: Random pairings (use $sample to get different results)
// ============================================================================
db.pairings.aggregate([
  { $sample: { size: 5 } },
  {
    $project: {
      id: 1,
      pairing_category: 1,
      credit_minutes: 1,
      fleet: 1
    }
  }
]);

// ============================================================================
// QUERY 7: Check layover_station status (debugging)
// ============================================================================
db.legs.findOne(
  {},
  { layover_station: 1, origin_station: 1, departure_station: 1, arrival_station: 1 }
);

// ============================================================================
// QUERY 8: Count legs with layover_station populated
// ============================================================================
db.legs.countDocuments({ layover_station: { $ne: null } });

// ============================================================================
// QUERY 9: Find pairings with specific ID (to verify different results)
// ============================================================================
db.pairings.findOne({ id: 'O8525' });  // Try different ID

// ============================================================================
// QUERY 10: Pairing categories breakdown
// ============================================================================
db.pairings.aggregate([
  {
    $group: {
      _id: '$pairing_category',
      count: { $sum: 1 }
    }
  },
  { $sort: { count: -1 } },
  { $limit: 15 }
]);
