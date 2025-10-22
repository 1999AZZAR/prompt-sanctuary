# API Key Migration Guide

This document outlines the migration from the coin/point system to a mandatory API key system in Prompt Sanctuary.

## Overview of Changes

### What Changed
- **Removed**: Point/coin system, achievements, daily bonuses, point transactions
- **Added**: Mandatory API key requirement for all users
- **Updated**: User interface to focus on API key management instead of points

### Why This Change
1. **Simplified User Experience**: No more point management or complex economy
2. **Unlimited Usage**: Users can generate as many prompts as they want with their own API key
3. **Cost Control**: Users have direct control over their API costs
4. **Reduced Complexity**: Eliminates the need for point tracking, expiration, and complex transaction logic

## Database Changes

### Tables Removed
- `point_transactions` - All point transaction history
- `point_history` - Detailed point change logs  
- `user_logins` - Daily login bonus tracking
- `achievements` - Achievement system
- `user_achievements` - User achievement unlocks

### Schema Updates
- `users` table: 
  - Removed `points` column
  - Made `gemini_api_key` NOT NULL with default ''
  - Made `api_key_validated` NOT NULL with default 0

## New User Flow

### Registration
1. User creates account (username/password)
2. **Immediately redirected to API key setup**
3. Must enter and validate Gemini API key
4. Only then can access the application

### Login
1. User logs in
2. System checks for valid API key
3. If no API key or invalid: redirect to API key setup
4. If valid: proceed to main application

### API Key Management
- Users can update their API key anytime
- Real-time validation when changing keys
- Clear error messages for invalid keys
- Option to test key before saving

## API Key Requirements

### Getting a Gemini API Key
1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Sign in with Google account
3. Click "Get API Key"
4. Create new project or select existing
5. Copy the API key (starts with "AI")

### Billing Setup Required
- Users must set up billing in Google Cloud Console
- Required even for free tier usage
- Link payment method to project

## Migration Process

### For Existing Users
1. **Database Migration**: Run `migrate_to_api_key_system.py`
   - Backs up existing databases
   - Removes point-related tables
   - Updates user schema
   - Preserves all prompts and user data

2. **User Experience**:
   - Existing users with API keys: marked as validated
   - Existing users without API keys: redirected to setup on next login
   - All point balances and achievements: removed

### Migration Script
```bash
cd web
python migrate_to_api_key_system.py
```

## Updated Features

### Removed Features
- Point system and economy
- Achievement system
- Daily login bonuses
- Point transaction history
- Point-based usage limits

### New Features
- API key validation and testing
- Real-time API key status
- Comprehensive API key setup guide
- API key management interface
- Usage tracking (for user's own API key)

## User Interface Changes

### Profile Page
- **Before**: Shows points, achievements, transaction history
- **After**: Shows API key status, session management, account settings

### Main Interface
- **Before**: Point costs displayed for each action
- **After**: No cost display, unlimited usage with valid API key

### Navigation
- **Before**: Point balance in header
- **After**: API key status indicator

## Technical Implementation

### New Files
- `models_new.py` - Simplified models without point system
- `routes_new.py` - Updated routes with API key validation
- `api_key_setup.html` - API key setup wizard
- `profile_new.html` - Updated profile template
- `migrate_to_api_key_system.py` - Migration script

### Updated Files
- `app.py` - Uses new models and routes
- `api_key_validator.py` - Enhanced validation with better error messages

### Key Functions
- `check_api_key_required()` - Checks if user needs API key
- `validate_gemini_api_key()` - Validates API key with Google
- `get_api_key_info()` - Comprehensive API key analysis
- `required_api_key` decorator - Protects routes requiring API key

## Error Handling

### API Key Validation Errors
- Invalid format (doesn't start with "AI")
- Invalid key (authentication failed)
- Quota exceeded
- Permission denied
- Billing required
- Regional restrictions

### User Guidance
- Clear error messages for each issue
- Step-by-step setup guide
- Links to Google AI Studio and billing setup
- Troubleshooting documentation

## Security Considerations

### API Key Storage
- Keys stored encrypted in database
- Masked display in UI (shows first 8 and last 4 characters)
- Secure validation without exposing keys

### Session Management
- API key status checked on each request
- Automatic redirect to setup if key missing
- Session validation for all protected routes

## Benefits of New System

### For Users
- **Unlimited Usage**: No point limits or restrictions
- **Cost Control**: Direct control over API costs
- **Simplified Experience**: No complex point management
- **Transparency**: Clear understanding of costs

### For Developers
- **Reduced Complexity**: No point system to maintain
- **Better Performance**: No point calculations or transactions
- **Easier Maintenance**: Simpler codebase
- **Clear Requirements**: API key validation is straightforward

## Migration Checklist

- [ ] Run database migration script
- [ ] Update application to use new models/routes
- [ ] Test API key validation flow
- [ ] Update user documentation
- [ ] Test with existing users
- [ ] Monitor for any issues
- [ ] Update deployment scripts if needed

## Support and Documentation

### User Documentation
- [API Key Setup Guide](docs/user-guide/api-key-setup.md)
- Updated user manual
- Troubleshooting guide

### Developer Documentation
- Updated API reference
- Migration guide
- Code documentation

## Rollback Plan

If issues arise, the migration can be rolled back by:
1. Restoring database backups
2. Reverting to old models/routes
3. Restoring point system functionality

However, this is not recommended as the new system provides significant benefits.

## Conclusion

The migration to API key-based system simplifies the user experience while providing unlimited usage capabilities. Users have direct control over their costs and the application is much simpler to maintain and understand.
