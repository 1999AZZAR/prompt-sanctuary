# Economy System

The Prompt Sanctuary economy system provides a comprehensive point-based economy with achievements, rewards, and gamification elements to enhance user engagement and manage API costs.

## Overview

The economy system is designed to:
- **Manage API Costs**: Balance system usage with user engagement
- **Encourage Quality**: Reward thoughtful prompt creation and community participation
- **Gamify Experience**: Make prompt creation fun and rewarding
- **Fair Distribution**: Ensure equitable access to AI resources

## Point System

### Starting Balance
- **New Users**: 80 points upon registration
- **Point Source**: Marked as "original" points that never expire
- **Maximum Balance**: 500 points per user to maintain system balance

### Point Costs by Feature

| Feature | Cost | Description |
|---------|------|-------------|
| **Basic Text Generation** | 1.5 points | Standard text prompt creation |
| **Basic Random Generation** | 0.8 points | Random prompt generation |
| **Basic Image Generation** | 1.5 points | Image prompt creation |
| **Basic Random Image** | 0.8 points | Random image prompt |
| **Basic Reverse Image** | 2.0 points | Reverse image prompt analysis |
| **Advanced Text Generation** | 1.9 points | Advanced text with custom parameters |
| **Advanced Image Generation** | 1.9 points | Advanced image with custom settings |
| **Advanced Reverse Image** | 2.5 points | Advanced reverse image analysis |
| **Prompt Refinement** | 0.5 points | AI-powered prompt optimization |

### Earning Points

#### Daily Login Bonus
- **Amount**: 5-12 random points per day
- **Frequency**: Once per day (24-hour cooldown)
- **Expiration**: 17-30 days (random)
- **Tracking**: Automatic detection of daily logins

#### Achievement Rewards
- **Automatic Unlocking**: Based on user activity patterns
- **Point Rewards**: Varies by achievement (5-200 points)
- **Expiration**: 45 days from award date
- **Categories**: Generation, sharing, consistency, exploration, community

#### API Key Contributions
- **Adding API Key**: 100 points reward
- **Expiration**: 80 days from addition
- **Usage Compensation**: 0.5 points per system use
- **Expiration**: 95 days from each use

#### Community Contributions
- **Sharing Prompts**: Points for community sharing
- **Expiration**: 30 days from sharing
- **Feedback**: Points for helpful feedback

### Point Expiration System

Different point sources have different expiration periods:

| Source | Expiration Period |
|--------|------------------|
| **Original Points** | Never expire |
| **Daily Login Rewards** | 17-30 days (random) |
| **Achievement Points** | 45 days |
| **API Key Addition** | 80 days |
| **API Key Usage** | 95 days |
| **Community Sharing** | 30 days |
| **Prompt Generation** | 15-20 days |

## Achievement System

### Achievement Categories

#### Generation Achievements
- **First Steps**: Generate your first prompt (5 points)
- **Prompt Creator**: Generate 10 prompts (15 points)
- **Productive User**: Generate 50 prompts (25 points)
- **Prompt Master**: Generate 100 prompts (40 points)
- **Generation Legend**: Generate 500 prompts (75 points)

#### Sharing Achievements
- **Community Helper**: Share your first prompt (10 points)
- **Sharing Enthusiast**: Share 10 prompts (20 points)
- **Community Champion**: Share 50 prompts (60 points)
- **Community Legend**: Share 100 prompts (150 points)

#### Consistency Achievements
- **Early Bird**: Login for 3 consecutive days (10 points)
- **Steady User**: Login for 7 consecutive days (20 points)
- **Dedicated User**: Login for 30 consecutive days (50 points)
- **Year Round User**: Login for 365 consecutive days (200 points)

#### Exploration Achievements
- **Feature Explorer**: Try 5 different features (15 points)
- **Advanced User**: Use advanced prompts (20 points)
- **Reverse Engineer**: Use reverse image prompts (15 points)
- **API Key Provider**: Add and validate API key (100 points)

#### Hidden Achievements
- **Early Adopter**: Be among the first 100 users (100 points)
- **Perfectionist**: Create 50 prompt versions (40 points)
- **Innovation Leader**: Create 20 custom templates (60 points)

### Achievement Unlocking

#### Automatic Detection
The system automatically tracks user activity and unlocks achievements based on:
- **Prompt Generation**: Count of prompts created
- **Sharing Activity**: Number of prompts shared
- **Login Streaks**: Consecutive daily logins
- **Feature Usage**: Different features tried
- **Community Engagement**: Interactions with other users

#### Progress Tracking
- **Real-time Updates**: Progress tracked in real-time
- **Visual Indicators**: Progress bars for multi-step achievements
- **Notification System**: Instant notifications when achievements unlock
- **Achievement Gallery**: View all achievements and progress

## Transaction History

### Detailed Tracking
Every point transaction is recorded with:
- **Transaction ID**: Unique identifier
- **Amount**: Points gained or spent
- **Source**: What caused the transaction
- **Description**: Detailed explanation
- **Timestamp**: When the transaction occurred
- **Expiration Date**: When points expire (if applicable)
- **Balance Before/After**: Point balance changes

### Interactive History Modal
- **Click Points Display**: Access detailed transaction history
- **Filter Options**: Filter by date, source, or type
- **Search Functionality**: Find specific transactions
- **Export Capability**: Download transaction history
- **Visual Timeline**: Graphical representation of point flow

### Transaction Sources
- **original**: Initial 80 points (never expire)
- **daily_login**: Daily login bonuses
- **achievement**: Achievement rewards
- **api_key_add**: API key addition reward
- **api_key_usage**: API key usage compensation
- **prompt_share**: Community sharing rewards
- **prompt_generation**: Cost for generating prompts
- **prompt_refinement**: Cost for refining prompts

## API Key Integration

### Personal API Key Benefits
- **No Point Costs**: Generate prompts without spending points
- **Unlimited Usage**: No daily limits or restrictions
- **Priority Access**: Faster response times
- **Community Contribution**: Help other users

### API Key Pool System
- **Fair Rotation**: LRU (Least Recently Used) algorithm
- **Usage Compensation**: 0.5 points per use of your key
- **Health Monitoring**: Track key performance and reliability
- **Automatic Management**: System handles key rotation and distribution

### Compensation Tracking
- **Usage Statistics**: Track how often your key is used
- **Automatic Rewards**: Compensation added automatically
- **Fair Distribution**: Prevent key overuse or underuse
- **Performance Metrics**: Monitor pool efficiency

## Economy Balance

### Design Principles
- **Sustainable Usage**: Point costs balance API expenses
- **Fair Access**: All users can participate regardless of API key ownership
- **Engagement Incentives**: Rewards encourage active participation
- **Community Growth**: Sharing and collaboration are rewarded

### Balancing Mechanisms
- **Point Expiration**: Prevents point hoarding
- **Daily Bonuses**: Regular point injection into economy
- **Achievement Rewards**: Milestone-based point distribution
- **API Key Compensation**: Fair reward for resource contribution

### Economic Monitoring
- **Usage Analytics**: Track point usage patterns
- **Balance Distribution**: Monitor point distribution across users
- **Achievement Rates**: Track achievement unlock rates
- **API Key Pool Health**: Monitor pool efficiency and usage

## User Experience

### Point Display
- **Sidebar Counter**: Always visible point balance
- **Click to Expand**: Click points to view detailed history
- **Color Coding**: Visual indicators for point status
- **Real-time Updates**: Instant balance updates

### Achievement Notifications
- **Toast Notifications**: Instant achievement unlock alerts
- **Achievement Popup**: Detailed achievement information
- **Progress Indicators**: Visual progress toward next achievements
- **Celebration Effects**: Visual feedback for milestone achievements

### Gamification Elements
- **Progress Bars**: Visual progress toward goals
- **Badge System**: Achievement badges and icons
- **Leaderboards**: Community recognition (planned)
- **Challenges**: Time-limited achievement opportunities (planned)

## Technical Implementation

### Database Schema
```sql
-- Point transactions table
CREATE TABLE point_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    points REAL NOT NULL,
    source TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_expired INTEGER DEFAULT 0
);

-- Point history tracking
CREATE TABLE point_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    transaction_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    points_before REAL NOT NULL,
    points_after REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Achievement system
CREATE TABLE achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL,
    icon TEXT NOT NULL,
    points_reward REAL NOT NULL,
    category TEXT NOT NULL,
    condition_type TEXT NOT NULL,
    condition_value INTEGER,
    hidden INTEGER DEFAULT 0
);
```

### API Endpoints
```
GET  /get_user_points          # Get current point balance
GET  /points/history           # Get transaction history
POST /points/expire            # Process point expiration
GET  /achievements/user        # Get user achievements
POST /achievements/check       # Check for new achievements
```

### Point Processing
- **Real-time Updates**: Immediate balance updates
- **Batch Processing**: Efficient point expiration handling
- **Transaction Safety**: Atomic operations for point changes
- **Error Recovery**: Robust error handling and rollback

## Future Enhancements

### Planned Features
- **Leaderboards**: Community rankings and competitions
- **Challenges**: Time-limited achievement opportunities
- **Point Trading**: User-to-user point transfers (planned)
- **Premium Features**: Advanced features for premium users
- **Gift System**: Send points to other users

### Advanced Analytics
- **Economic Metrics**: Detailed economy health monitoring
- **User Behavior**: Point usage pattern analysis
- **Achievement Analytics**: Achievement unlock rate tracking
- **Performance Optimization**: Economy balance optimization

### Community Features
- **Team Achievements**: Group-based achievement challenges
- **Community Goals**: Shared community achievement targets
- **Event Rewards**: Special point rewards for community events
- **Seasonal Challenges**: Time-limited seasonal achievements

---

*The economy system is designed to evolve with user feedback and usage patterns. For the latest updates and planned changes, see the [development roadmap](../development/roadmap.md).*
