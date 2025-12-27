/* MongoDB Playground - Example Queries for Airline Pairings
 *
 * To run these queries:
 * 1. Make sure you're connected to MongoDB in VS Code
 * 2. Select a query block (or place cursor in it)
 * 3. Press Cmd+Enter (Mac) or Ctrl+Enter (Windows) to execute
 *
 * Or click the "Play" button at the top right
 */

// Select the database
use('airline_pairings');

// ============================================================================
// BASIC QUERIES - Getting Started
// ============================================================================

// 1. Count total documents in each collection
db.bid_periods.countDocuments({});
db.pairings.countDocuments({});
db.legs.countDocuments({});

// 2. View a sample pairing (full document)
db.pairings.findOne({});

// 3. View a sample pairing (just key fields)
db.pairings.findOne(
  {},
  {
    id: 1,
    pairing_category: 1,
    credit_minutes: 1,
    days: 1,
    fleet: 1,
    base: 1
  }
);

// 4. List all unique fleets
db.pairings.distinct('fleet');

// 5. List all unique bases
db.pairings.distinct('base');

// ============================================================================
// LAYOVER QUERIES - Finding Overnight Destinations
// ============================================================================

// 6. Top 10 most common layover cities
db.legs.aggregate([
  {
    $match: { layover_station: { $ne: null } }
  },
  {
    $group: {
      _id: '$layover_station',
      count: { $sum: 1 }
    }
  },
  { $sort: { count: -1 } },
  { $limit: 10 }
]);

// 7. Find all pairings with Denver (DEN) layover
db.pairings.find(
  { 'duty_periods.layover_station': 'DEN' },
  {
    id: 1,
    pairing_category: 1,
    credit_minutes: 1,
    'duty_periods.layover_station': 1,
    'duty_periods.hotel': 1
  }
);

// 8. Hotels used in Los Angeles (LAX) layovers
db.pairings.aggregate([
  { $unwind: '$duty_periods' },
  {
    $match: {
      'duty_periods.layover_station': 'LAX',
      'duty_periods.hotel': { $ne: null }
    }
  },
  {
    $group: {
      _id: '$duty_periods.hotel',
      count: { $sum: 1 }
    }
  },
  { $sort: { count: -1 } }
]);

// 9. Pairings with multiple layovers (3+ day trips)
db.pairings.find(
  {
    days: { $gte: '3' },
    duty_period_count: { $gte: 3 }
  },
  {
    id: 1,
    pairing_category: 1,
    days: 1,
    'duty_periods.layover_station': 1
  }
).limit(10);

// ============================================================================
// CREDIT & VALUE QUERIES - Finding High-Value Pairings
// ============================================================================

// 10. High-value pairings (>20 hours credit)
db.pairings.find(
  { credit_minutes: { $gt: 1200 } }
).sort({ credit_minutes: -1 }).limit(10);

// 11. Average credit by fleet
db.pairings.aggregate([
  {
    $group: {
      _id: '$fleet',
      avg_credit_hours: { $avg: { $divide: ['$credit_minutes', 60] } },
      max_credit_hours: { $max: { $divide: ['$credit_minutes', 60] } },
      count: { $sum: 1 }
    }
  },
  { $sort: { avg_credit_hours: -1 } }
]);

// 12. Best credit-to-days ratio (efficiency)
db.pairings.aggregate([
  {
    $match: {
      days: { $ne: null },
      credit_minutes: { $gt: 0 }
    }
  },
  {
    $project: {
      id: 1,
      pairing_category: 1,
      days: 1,
      credit_hours: { $divide: ['$credit_minutes', 60] },
      days_numeric: { $toInt: '$days' }
    }
  },
  {
    $project: {
      id: 1,
      pairing_category: 1,
      days: 1,
      credit_hours: 1,
      credit_per_day: { $divide: ['$credit_hours', '$days_numeric'] }
    }
  },
  { $sort: { credit_per_day: -1 } },
  { $limit: 20 }
]);

// ============================================================================
// ROUTE QUERIES - Flight Patterns
// ============================================================================

// 13. Most common routes (city pairs)
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
      count: { $sum: 1 },
      avg_flight_time_hours: {
        $avg: { $divide: ['$flight_time_minutes', 60] }
      }
    }
  },
  { $sort: { count: -1 } },
  { $limit: 20 }
]);

// 14. All flights from Chicago (ORD)
db.legs.find(
  { departure_station: 'ORD' },
  {
    departure_station: 1,
    arrival_station: 1,
    equipment: 1,
    flight_time_minutes: 1,
    deadhead: 1
  }
).limit(20);

// 15. Find specific route (ORD to LAX)
db.legs.find({
  departure_station: 'ORD',
  arrival_station: 'LAX'
});

// ============================================================================
// EQUIPMENT QUERIES - Aircraft Types
// ============================================================================

// 16. Equipment usage breakdown
db.legs.aggregate([
  {
    $group: {
      _id: '$equipment',
      total_legs: { $sum: 1 },
      avg_flight_time_hours: {
        $avg: { $divide: ['$flight_time_minutes', 60] }
      }
    }
  },
  { $sort: { total_legs: -1 } }
]);

// 17. Find all 787 pairings
db.pairings.find(
  { fleet: '787' },
  {
    id: 1,
    pairing_category: 1,
    credit_minutes: 1,
    days: 1
  }
).limit(10);

// ============================================================================
// TIME-BASED QUERIES - Departure Times, Schedules
// ============================================================================

// 18. Early morning departures (before 6am)
db.legs.find(
  {
    departure_time_minutes: { $lt: 360 }
  },
  {
    departure_station: 1,
    arrival_station: 1,
    departure_time_formatted: 1,
    equipment: 1
  }
).limit(20);

// 19. Red-eye flights (departing 10pm-6am)
db.legs.find({
  $or: [
    { departure_time_minutes: { $gte: 1320 } }, // After 10pm
    { departure_time_minutes: { $lt: 360 } }     // Before 6am
  ]
}).limit(20);

// 20. Distribution of departures by time of day
db.legs.aggregate([
  {
    $bucket: {
      groupBy: '$departure_time_minutes',
      boundaries: [0, 360, 720, 1080, 1440],
      default: 'Unknown',
      output: {
        count: { $sum: 1 },
        time_period: {
          $literal: ['00-06 (Early Morning)', '06-12 (Morning)', '12-18 (Afternoon)', '18-24 (Evening)']
        }
      }
    }
  }
]);

// ============================================================================
// CATEGORY QUERIES - Pairing Types
// ============================================================================

// 21. Count pairings by category
db.pairings.aggregate([
  {
    $group: {
      _id: '$pairing_category',
      count: { $sum: 1 },
      avg_credit_hours: {
        $avg: { $divide: ['$credit_minutes', 60] }
      }
    }
  },
  { $sort: { count: -1 } },
  { $limit: 20 }
]);

// 22. Find reserve pairings
db.pairings.find(
  {
    pairing_category: { $regex: /RESERVE|RSV|RES/i }
  },
  {
    id: 1,
    pairing_category: 1,
    credit_minutes: 1
  }
).limit(10);

// ============================================================================
// INTERNATIONAL QUERIES
// ============================================================================

// 23. International vs Domestic pairings
db.pairings.aggregate([
  {
    $group: {
      _id: {
        $cond: [
          { $gt: ['$international_flight_time_minutes', 0] },
          'International',
          'Domestic'
        ]
      },
      count: { $sum: 1 },
      avg_credit_hours: {
        $avg: { $divide: ['$credit_minutes', 60] }
      }
    }
  }
]);

// ============================================================================
// DEADHEAD QUERIES - Non-Revenue Positioning
// ============================================================================

// 24. Find pairings with deadhead legs
db.legs.aggregate([
  {
    $match: { deadhead: true }
  },
  {
    $group: {
      _id: '$pairing_id',
      deadhead_count: { $sum: 1 }
    }
  },
  { $sort: { deadhead_count: -1 } },
  { $limit: 10 }
]);

// 25. Most common deadhead routes
db.legs.aggregate([
  {
    $match: { deadhead: true }
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
// COMPLEX QUERIES - Multi-criteria Searches
// ============================================================================

// 26. Perfect pairing finder: 3-4 days, high credit, specific layover
db.pairings.find({
  days: { $in: ['3', '4'] },
  credit_minutes: { $gte: 1000, $lte: 1500 },  // 16-25 hours
  'duty_periods.layover_station': 'LAX'
});

// 27. Quick turns - Short layovers in specific cities
db.pairings.aggregate([
  { $unwind: '$duty_periods' },
  {
    $match: {
      'duty_periods.layover_station': { $in: ['DEN', 'LAX', 'SFO'] }
    }
  },
  {
    $project: {
      id: 1,
      pairing_category: 1,
      layover_station: '$duty_periods.layover_station',
      hotel: '$duty_periods.hotel'
    }
  },
  { $limit: 20 }
]);

// 28. Longest duty periods (by number of legs)
db.pairings.aggregate([
  { $unwind: '$duty_periods' },
  {
    $project: {
      id: 1,
      pairing_category: 1,
      leg_count: { $size: '$duty_periods.legs' },
      layover: '$duty_periods.layover_station'
    }
  },
  { $sort: { leg_count: -1 } },
  { $limit: 10 }
]);

// ============================================================================
// STATISTICAL QUERIES
// ============================================================================

// 29. Overall fleet statistics
db.pairings.aggregate([
  {
    $facet: {
      total_stats: [
        {
          $group: {
            _id: null,
            total_pairings: { $sum: 1 },
            avg_credit: { $avg: '$credit_minutes' },
            max_credit: { $max: '$credit_minutes' },
            min_credit: { $min: '$credit_minutes' }
          }
        }
      ],
      by_fleet: [
        {
          $group: {
            _id: '$fleet',
            count: { $sum: 1 },
            avg_credit: { $avg: '$credit_minutes' }
          }
        },
        { $sort: { count: -1 } }
      ]
    }
  }
]);

// 30. Find a specific pairing by ID
db.pairings.findOne({ id: 'O8001' });

// ============================================================================
// TIP: To run a query:
// 1. Place your cursor anywhere in the query
// 2. Press Cmd+Enter (Mac) or Ctrl+Enter (Windows)
// 3. Results appear in the OUTPUT panel at the bottom
// ============================================================================
