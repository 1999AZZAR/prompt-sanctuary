# API Key Management System

The API Key Management system allows users to integrate their own Gemini API keys for unlimited usage while contributing to a community pool that benefits all users.

## Overview

The API Key Management system provides:
- **Personal API Key Integration**: Use your own keys for unlimited prompt generation
- **Community Key Pooling**: Share validated keys for system-wide usage
- **Fair Compensation**: Earn points when your key is used by others
- **Automatic Validation**: Real-time API key testing and validation
- **Health Monitoring**: Track key performance and reliability

## Personal API Keys

### Adding Your API Key

#### Step-by-Step Process
1. **Navigate to Profile**: Go to your profile page
2. **API Key Section**: Find the "API Key Management" section
3. **Enter Key**: Input your Gemini API key
4. **Validate**: Click "Validate" to test the key
5. **Success**: Earn 100 bonus points upon successful validation

#### API Key Requirements
- **Format**: Must start with "AI" and be at least 20 characters
- **Validity**: Must be an active Gemini API key
- **Permissions**: Must have proper API access permissions
- **Quota**: Must have available quota for testing

### Benefits of Personal API Keys

#### Unlimited Usage
- **No Point Costs**: Generate prompts without spending points
- **No Daily Limits**: No restrictions on prompt generation
- **Priority Access**: Faster response times
- **Full Control**: Manage your own API usage and costs

#### Community Contribution
- **Help Others**: Your key helps users without their own keys
- **Fair Compensation**: Earn 0.5 points each time your key is used
- **Community Recognition**: Contribute to the platform's sustainability
- **Achievement Unlock**: "API Key Provider" achievement (100 points)

#### Additional Rewards
- **Initial Bonus**: 100 points for successfully adding a key
- **Usage Tracking**: Monitor how often your key is used
- **Performance Metrics**: Track key reliability and performance
- **Community Impact**: See your contribution to the platform

### API Key Security

#### Secure Storage
- **Encryption**: Keys encrypted before storage
- **Access Control**: Only accessible by the key owner
- **Secure Transmission**: HTTPS for all key-related communications
- **Audit Logging**: Track key access and usage

#### Validation Process
- **Real-time Testing**: Immediate validation upon submission
- **Multiple Checks**: Format, permissions, and quota validation
- **Error Handling**: Clear error messages for validation failures
- **Retry Logic**: Automatic retry for transient failures

#### Key Management
- **Update Keys**: Change keys when needed
- **Remove Keys**: Revoke access (costs 100 points to prevent abuse)
- **Usage Monitoring**: Track key performance and health
- **Security Alerts**: Notifications for unusual activity

## API Key Pool System

### How Pooling Works

#### Key Contribution
- **Automatic Addition**: Validated keys automatically join the pool
- **Health Monitoring**: System tracks key performance and reliability
- **Usage Distribution**: Fair rotation ensures equitable usage
- **Automatic Refresh**: New keys seamlessly integrate into the pool

#### Fair Rotation Algorithm
- **LRU (Least Recently Used)**: Keys used least recently get priority
- **Usage Balancing**: Prevent overuse or underuse of any key
- **Performance Weighting**: More reliable keys get slightly higher priority
- **User Exclusion**: Your own requests don't use your own key

#### Compensation System
- **Per-Use Rewards**: 0.5 points each time your key is used
- **Automatic Distribution**: Compensation added automatically
- **Usage Tracking**: Detailed statistics on key usage
- **Fair Distribution**: Ensures equitable compensation

### Pool Management

#### Health Monitoring
- **Success Rate**: Track successful vs failed requests
- **Response Time**: Monitor key performance metrics
- **Error Tracking**: Log and analyze API errors
- **Quota Monitoring**: Track remaining quota and usage limits

#### Automatic Management
- **Key Rotation**: Automatic switching between available keys
- **Health Checks**: Regular validation of key health
- **Error Recovery**: Automatic retry with different keys
- **Pool Refresh**: Seamless integration of new keys

#### Usage Statistics
- **Pool Size**: Number of active keys in the pool
- **Usage Distribution**: How usage is distributed across keys
- **Performance Metrics**: Average response times and success rates
- **User Impact**: How many users benefit from the pool

## Technical Implementation

### Validation System

#### API Key Validator (`api_key_validator.py`)
```python
def validate_gemini_api_key(api_key: str) -> Tuple[bool, str]:
    """
    Validate a Gemini API key by making a test request.
    
    Args:
        api_key: The API key to validate
        
    Returns:
        Tuple[is_valid, message]
    """
    # Format validation
    if len(api_key) < 20 or not api_key.startswith('AI'):
        return False, "Invalid API key format"
    
    # API test request
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Test message")
        return True, "API key is valid and working"
    except Exception as e:
        return False, f"Validation failed: {str(e)}"
```

#### Validation Process
1. **Format Check**: Verify key format and length
2. **API Test**: Make actual API request to test functionality
3. **Response Validation**: Verify API response is valid
4. **Error Handling**: Provide clear error messages for failures

### Pool Management System

#### API Key Pool (`api_key_pool.py`)
```python
class ApiKeyPool:
    """Manages a pool of user API keys with fair rotation."""
    
    def get_next_key(self, exclude_user: str = None) -> ApiKeyInfo:
        """Get the next API key using LRU rotation."""
        available_keys = self.get_available_keys()
        
        # Filter out user's own key if specified
        if exclude_user:
            available_keys = [k for k in available_keys 
                            if k.username != exclude_user]
        
        # Sort by last_used time for fair rotation
        available_keys.sort(key=lambda k: k.last_used)
        selected_key = available_keys[0]
        
        # Update usage statistics
        selected_key.last_used = time.time()
        selected_key.usage_count += 1
        
        return selected_key
```

#### Pool Features
- **Fair Rotation**: LRU algorithm ensures equitable usage
- **User Exclusion**: Requests don't use the user's own key
- **Usage Tracking**: Monitor usage count and timing
- **Health Monitoring**: Track key performance and reliability

### Database Schema

#### API Key Storage
```sql
-- User API keys table
ALTER TABLE users ADD COLUMN gemini_api_key TEXT;
ALTER TABLE users ADD COLUMN api_key_validated INTEGER DEFAULT 0;

-- API key usage tracking
CREATE TABLE api_key_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    key_used TEXT NOT NULL,
    usage_count INTEGER DEFAULT 1,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0
);
```

#### Usage Tracking
- **Key Identification**: Track which key was used for each request
- **Success/Failure Rates**: Monitor key reliability
- **Usage Frequency**: Track how often each key is used
- **Performance Metrics**: Response times and error rates

## User Interface

### Profile Page Integration

#### API Key Section
- **Status Display**: Shows current API key status
- **Validation Form**: Input field for new API key
- **Usage Statistics**: Display key usage and compensation
- **Management Controls**: Update, remove, or validate keys

#### Visual Indicators
- **Status Icons**: Green checkmark for validated keys
- **Usage Counter**: Shows how many times your key was used
- **Compensation Display**: Points earned from key usage
- **Health Status**: Visual indicator of key performance

### Real-time Updates
- **Instant Validation**: Immediate feedback on key validation
- **Usage Notifications**: Alerts when your key is used
- **Compensation Updates**: Real-time point balance updates
- **Status Changes**: Immediate UI updates for key status

## API Endpoints

### Key Management Endpoints
```
POST /api_key/validate       # Validate and store API key
POST /api_key/remove         # Remove API key (costs 100 points)
GET  /api_key/status         # Get current key status
GET  /api_key/pool_stats     # Get pool statistics
GET  /api_key/usage          # Get usage statistics
```

### Request/Response Examples

#### Validate API Key
```javascript
// Request
POST /api_key/validate
{
    "api_key": "AIzaSyC..."
}

// Response
{
    "success": true,
    "message": "API key validated successfully",
    "points_awarded": 100
}
```

#### Get Pool Statistics
```javascript
// Request
GET /api_key/pool_stats

// Response
{
    "success": true,
    "pool_size": 25,
    "total_usage": 1547,
    "active_keys": 23,
    "average_response_time": 1.2
}
```

## Security Considerations

### Key Protection
- **Encryption at Rest**: Keys encrypted in database
- **Secure Transmission**: HTTPS for all communications
- **Access Control**: Only key owner can access their key
- **Audit Logging**: Track all key-related operations

### Privacy Protection
- **Key Masking**: Display only partial key information
- **Usage Anonymization**: Usage statistics don't reveal personal information
- **Secure Storage**: Keys stored with proper security measures
- **Access Logging**: Track key access and usage

### Abuse Prevention
- **Validation Requirements**: Real API keys only
- **Usage Limits**: Reasonable usage limits per key
- **Monitoring**: Track unusual usage patterns
- **Revocation**: Ability to remove problematic keys

## Benefits for Users

### Individual Benefits
- **Cost Savings**: No point costs for prompt generation
- **Unlimited Usage**: No daily or monthly limits
- **Better Performance**: Faster response times
- **Full Control**: Manage your own API usage

### Community Benefits
- **Shared Resources**: Pool benefits all users
- **Fair Compensation**: Contributors rewarded for sharing
- **Improved Reliability**: Multiple keys provide redundancy
- **Cost Distribution**: Shared API costs across community

### Platform Benefits
- **Sustainability**: Community-funded API usage
- **Reliability**: Multiple keys provide failover
- **Scalability**: Pool scales with community size
- **Cost Management**: Distributed API cost management

## Future Enhancements

### Planned Features
- **Key Analytics**: Detailed usage and performance analytics
- **Custom Limits**: User-defined usage limits for shared keys
- **Key Rotation**: Automatic key rotation for security
- **Advanced Monitoring**: Real-time key health monitoring

### Community Features
- **Key Leaderboards**: Top contributors recognition
- **Usage Transparency**: Public pool statistics
- **Community Goals**: Shared pool size targets
- **Reward Tiers**: Enhanced rewards for heavy contributors

---

*The API Key Management system is designed to evolve with community needs and usage patterns. For the latest updates and planned changes, see the [development roadmap](../development/roadmap.md).*
