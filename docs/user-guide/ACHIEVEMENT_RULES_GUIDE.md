# Achievement Rules Guide

## Overview

Achievements are unlocked when users reach specific milestones in their financial activities. Each achievement has a target requirement that must be met to unlock it.

## Where Achievement Rules Are Defined

**File:** `api/core/services/achievement_engine.py` (method: `_get_achievement_definitions()` starting at line 518)

## Achievement Categories

### 1. Expense Tracking Achievements

Track expenses and upload receipts to unlock these achievements.

| Achievement | Requirement | Reward XP | Difficulty |
|---|---|---|---|
| First Steps | Track 1 expense | 50 | Bronze |
| Getting Started | Track 10 expenses | 100 | Bronze |
| Expense Enthusiast | Track 50 expenses | 250 | Silver |
| Expense Expert | Track 100 expenses | 500 | Gold |
| Expense Master | Track 500 expenses | 1000 | Platinum |
| Receipt Collector | Upload 10 receipts | 75 | Bronze |
| Receipt Archivist | Upload 50 receipts | 200 | Silver |

**Requirement Type:** `expense_count` and `receipt_count`

### 2. Invoice Management Achievements

Create invoices to unlock these achievements.

| Achievement | Requirement | Reward XP | Difficulty |
|---|---|---|---|
| First Invoice | Create 1 invoice | 75 | Bronze |
| Invoice Professional | Create 10 invoices | 300 | Silver |
| Invoice Expert | Create 100 invoices | 750 | Gold |

**Requirement Type:** `invoice_count`

### 3. Habit Formation Achievements

Build consistent habits and streaks to unlock these achievements.

| Achievement | Requirement | Reward XP | Difficulty |
|---|---|---|---|
| Week Warrior | 7-day expense tracking streak | 150 | Bronze |
| Month Master | 30-day expense tracking streak | 500 | Silver |
| Quarter Champion | 90-day expense tracking streak | 1200 | Gold |
| Year Legend | 365-day expense tracking streak | 3000 | Platinum |
| Perfect Week | Complete all daily tasks for 1 week | 300 | Silver |
| Budget Conscious | Review budget 5 times | 125 | Bronze |

**Requirement Types:** `streak_length`, `perfect_week`, `budget_review_count`

### 4. Financial Health Achievements

Improve your financial health score to unlock these achievements.

**Requirement Type:** `financial_health_score`

### 5. Exploration Achievements

Discover and use various features of the app.

**Requirement Type:** Various feature-specific types

## How Achievement Progress Works

### Progress Calculation

Progress is calculated as a percentage based on current activity vs. target:

```
Progress % = (Current Count / Target) × 100
```

Examples:
- 5 expenses tracked toward "Getting Started" (10 target) = 50% progress
- 25 expenses tracked toward "Expense Enthusiast" (50 target) = 50% progress
- 100 expenses tracked toward "Expense Expert" (100 target) = 100% (unlocked!)

### Achievement Unlocking

Achievements unlock automatically when:
1. User performs a financial action (create expense, invoice, etc.)
2. System updates user statistics
3. Achievement progress reaches 100%
4. Achievement is marked as completed and XP is awarded

## Requirement Types

### expense_count
Tracks the number of expenses created by the user.
```python
{"type": "expense_count", "target": 10}
```

### invoice_count
Tracks the number of invoices created by the user.
```python
{"type": "invoice_count", "target": 10}
```

### receipt_count
Tracks the number of receipt photos uploaded.
```python
{"type": "receipt_count", "target": 10}
```

### budget_review_count
Tracks the number of times user reviews their budget.
```python
{"type": "budget_review_count", "target": 5}
```

### streak_length
Tracks consecutive days of a specific habit.
```python
{"type": "streak_length", "target": 7, "habit_type": "daily_expense_tracking"}
```

### total_xp
Tracks total experience points earned.
```python
{"type": "total_xp", "target": 1000}
```

### level_reached
Tracks user level progression.
```python
{"type": "level_reached", "target": 5}
```

### financial_health_score
Tracks financial health score improvement.
```python
{"type": "financial_health_score", "target": 80}
```

## Difficulty Levels

- **Bronze:** Entry-level achievements, easy to unlock
- **Silver:** Intermediate achievements, requires consistent activity
- **Gold:** Advanced achievements, requires significant effort
- **Platinum:** Expert-level achievements, requires sustained commitment

## How to Modify Achievement Rules

To change achievement requirements or add new achievements:

1. Open `api/core/services/achievement_engine.py`
2. Find the `_get_achievement_definitions()` method (line 518)
3. Modify existing achievement definitions or add new ones
4. Each achievement needs:
   - `achievement_id`: Unique identifier (e.g., "expense_tracker_50")
   - `name`: Display name
   - `description`: What the achievement requires
   - `category`: One of the 5 categories
   - `difficulty`: bronze/silver/gold/platinum
   - `requirements`: List of requirement objects
   - `reward_xp`: Points awarded when unlocked
   - `reward_badge_url`: Optional badge image URL

Example:
```python
{
    "achievement_id": "expense_tracker_25",
    "name": "Expense Tracker",
    "description": "Track 25 expenses",
    "category": AchievementCategory.EXPENSE_TRACKING,
    "difficulty": AchievementDifficulty.BRONZE,
    "requirements": [{"type": "expense_count", "target": 25}],
    "reward_xp": 150,
    "reward_badge_url": "/badges/expense_25.png"
}
```

5. Restart the application - achievements will be initialized on next startup

## Statistics Tracked

User statistics are updated in `profile.statistics` and include:

- `totalActionsCompleted`: Total number of financial actions
- `expensesTracked`: Number of expenses created
- `invoicesCreated`: Number of invoices created
- `receiptsUploaded`: Number of receipts uploaded
- `budgetReviews`: Number of budget reviews
- `longestStreak`: Longest streak achieved
- `achievementsUnlocked`: Total achievements unlocked
- `challengesCompleted`: Total challenges completed

## Key Files

- **Achievement Definitions:** `api/core/services/achievement_engine.py` (line 518)
- **Achievement Progress Calculation:** `api/core/services/achievement_engine.py` (method: `_calculate_achievement_progress`)
- **Achievement Checking:** `api/core/services/achievement_engine.py` (method: `check_achievements`)
- **Statistics Updates:** `api/core/services/gamification_service.py` (method: `_update_user_statistics`)
- **Frontend Display:** `ui/src/components/gamification/AchievementGrid.tsx`

## Testing Achievements

To test achievements locally:

1. Enable gamification for your user
2. Create expenses/invoices to trigger achievement checks
3. View achievements in the Gamification dashboard
4. Check progress bars to see how close you are to unlocking each achievement

## Troubleshooting

### Achievements not unlocking
- Verify gamification is enabled for the user
- Check that statistics are being updated (look for logs in API)
- Ensure achievement definitions are initialized in the database
- Refresh the page to see latest achievement status

### Progress not updating
- Statistics are updated after each financial action
- Profile is refreshed after statistics commit
- Check that the action type matches the requirement type

### Achievement not showing
- Verify the achievement is marked as `is_active: True`
- Check that the achievement category matches the filter you're viewing
- Ensure the achievement definition was properly initialized
