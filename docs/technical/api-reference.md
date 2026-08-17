# API Reference

Complete reference for all Prompt Sanctuary API endpoints.

## Base URL

```
Production: https://sanctuary01.pythonanywhere.com/
Development: http://127.0.0.1:5000/
```

## Authentication

Most endpoints require authentication via session cookies. Include CSRF tokens for POST requests.

### CSRF Protection
```javascript
// Get CSRF token
const csrfToken = document.querySelector('meta[name=csrf-token]').getAttribute('content');

// Include in POST requests
fetch('/endpoint', {
    method: 'POST',
    headers: {
        'X-CSRFToken': csrfToken
    },
    body: formData
});
```

## Authentication Endpoints

### Login
```http
POST /login
Content-Type: application/x-www-form-urlencoded

username=your_username&password=your_password&csrf_token=token
```

**Response:**
```json
{
    "success": true,
    "message": "Login successful",
    "redirect": "/home"
}
```

### Signup
```http
POST /signup
Content-Type: application/x-www-form-urlencoded

username=new_user&password=new_password&csrf_token=token
```

**Response:**
```json
{
    "success": true,
    "message": "Account created successfully",
    "redirect": "/login"
}
```

### Logout
```http
POST /logout
```

**Response:**
```json
{
    "success": true,
    "message": "Logged out successfully"
}
```

## Prompt Generation Endpoints

### Basic Text Generation
```http
POST /generate/tprompt
Content-Type: application/x-www-form-urlencoded

user_input_text=Create a story about a robot&csrf_token=token
```

**Response:**
```json
{
    "success": true,
    "result": "Generated prompt text here...",
    "points_used": 1.5,
    "remaining_points": 78.5
}
```

### Streaming Text Generation
```http
POST /generate/tprompt/stream
Content-Type: application/x-www-form-urlencoded

user_input_text=Create a story about a robot&csrf_token=token
```

**Response:** Server-Sent Events stream
```
data: Generated chunk 1

data: Generated chunk 2

data: [DONE]
```

### Random Prompt Generation
```http
POST /generate/trandom
Content-Type: application/x-www-form-urlencoded

csrf_token=token
```

**Response:**
```json
{
    "success": true,
    "result": "Random generated prompt...",
    "points_used": 0.8,
    "remaining_points": 77.7
}
```

### Advanced Generation
```http
POST /advance/generate
Content-Type: application/x-www-form-urlencoded

text_parameter0=Use case here&text_parameter1=Knowledge base&text_parameter2=Safety level&text_parameter3=Custom instructions&csrf_token=token
```

**Response:**
```json
{
    "success": true,
    "result": "Advanced generated prompt...",
    "points_used": 1.9,
    "remaining_points": 75.8
}
```

## Prompt Management Endpoints

### Save Prompt
```http
POST /save_prompt
Content-Type: application/x-www-form-urlencoded

title=My Prompt Title&prompt=Prompt content here&csrf_token=token
```

**Response:**
```json
{
    "success": true,
    "message": "Prompt saved successfully",
    "prompt_id": "abc123"
}
```

### Save Edit
```http
POST /save_edit
Content-Type: application/x-www-form-urlencoded

prompt_id=abc123&title=Updated Title&prompt=Updated content&csrf_token=token
```

**Response:**
```json
{
    "success": true,
    "message": "Prompt updated successfully"
}
```

### Delete Prompt
```http
POST /delete_prompt
Content-Type: application/x-www-form-urlencoded

prompt_id=abc123&csrf_token=token
```

**Response:**
```json
{
    "success": true,
    "message": "Prompt deleted successfully"
}
```

### Get Prompt Versions
```http
GET /versions/abc123
```

**Response:**
```json
{
    "success": true,
    "versions": [
        {
            "version_number": 1,
            "title": "Original Title",
            "prompt": "Original content",
            "created_at": "2025-01-15 10:30:00"
        },
        {
            "version_number": 2,
            "title": "Updated Title",
            "prompt": "Updated content",
            "created_at": "2025-01-15 11:45:00"
        }
    ]
}
```

### Rollback Version
```http
POST /versions/rollback
Content-Type: application/x-www-form-urlencoded

prompt_id=abc123&version_number=1&csrf_token=token
```

**Response:**
```json
{
    "success": true,
    "message": "Rolled back to selected version"
}
```

## Community Endpoints

### Share Prompt
```http
POST /share_prompt
Content-Type: application/x-www-form-urlencoded

prompt_id=abc123&csrf_token=token
```

**Response:**
```json
{
    "success": true,
    "message": "Prompt shared with community",
    "points_awarded": 5.0
}
```

### Unshare Prompt
```http
POST /unshare_prompt
Content-Type: application/x-www-form-urlencoded

prompt_id=abc123&csrf_token=token
```

**Response:**
```json
{
    "success": true,
    "message": "Prompt removed from community"
}
```

## API Key Management Endpoints

### Validate API Key
```http
POST /api_key/validate
Content-Type: application/x-www-form-urlencoded

api_key=AIzaSyC...&csrf_token=token
```

**Response:**
```json
{
    "success": true,
    "message": "API key validated successfully",
    "points_awarded": 100.0
}
```

### Remove API Key
```http
POST /api_key/remove
Content-Type: application/x-www-form-urlencoded

csrf_token=token
```

**Response:**
```json
{
    "success": true,
    "message": "API key removed successfully",
    "points_deducted": 100.0
}
```

### Get API Key Status
```http
GET /api_key/status
```

**Response:**
```json
{
    "success": true,
    "has_api_key": true,
    "is_validated": true,
    "masked_key": "AIzaSyC...****",
    "usage_count": 42,
    "total_compensation": 21.0
}
```

### Get Pool Statistics
```http
GET /api_key/pool_stats
```

**Response:**
```json
{
    "success": true,
    "pool_size": 25,
    "active_keys": 23,
    "total_usage": 1547,
    "average_response_time": 1.2
}
```

## Point System Endpoints

### Get User Points
```http
GET /get_user_points
```

**Response:**
```json
{
    "success": true,
    "points": 85.5,
    "daily_bonus_available": true,
    "next_bonus_time": "2025-01-16 00:00:00"
}
```

### Get Point History
```http
GET /points/history
```

**Response:**
```json
{
    "success": true,
    "transactions": [
        {
            "id": 123,
            "points": 5.0,
            "source": "daily_login",
            "description": "Daily login bonus",
            "created_at": "2025-01-15 10:30:00",
            "expires_at": "2025-02-01 10:30:00"
        }
    ],
    "total_count": 25
}
```

### Process Daily Login
```http
POST /process_daily_login
Content-Type: application/x-www-form-urlencoded

csrf_token=token
```

**Response:**
```json
{
    "success": true,
    "points_awarded": 8.0,
    "new_balance": 93.5,
    "message": "Daily login bonus awarded"
}
```

## Achievement Endpoints

### Get User Achievements
```http
GET /achievements/user
```

**Response:**
```json
{
    "success": true,
    "achievements": [
        {
            "id": 1,
            "name": "First Steps",
            "description": "Generate your first prompt",
            "icon": "fas fa-baby",
            "unlocked_at": "2025-01-15 10:30:00",
            "points_reward": 5.0
        }
    ],
    "total_points_earned": 45.0
}
```

### Check Achievements
```http
POST /achievements/check
Content-Type: application/x-www-form-urlencoded

csrf_token=token
```

**Response:**
```json
{
    "success": true,
    "new_achievements": [
        {
            "name": "Prompt Creator",
            "description": "Generate 10 prompts",
            "points_reward": 15.0
        }
    ],
    "total_points_earned": 15.0
}
```

## Language Endpoints

### Set Language
```http
GET /language/en
```

**Response:**
```json
{
    "success": true,
    "message": "Language changed to English",
    "redirect": "/home"
}
```

## Prompt Refinement Endpoints

### Refine Prompt
```http
POST /refine_prompt
Content-Type: application/x-www-form-urlencoded

prompt_text=Original prompt text&action=shorten&custom_instructions=Optional custom instructions&csrf_token=token
```

**Response:**
```json
{
    "success": true,
    "response": "Refined prompt text here...",
    "points_used": 0.5,
    "remaining_points": 93.0
}
```

### Generate AI Title
```http
POST /generate_title
Content-Type: application/x-www-form-urlencoded

prompt_text=Prompt content&prompt_type=basic&csrf_token=token
```

**Response:**
```json
{
    "success": true,
    "title": "Smart AI-Generated Title",
    "points_used": 0.2,
    "remaining_points": 92.8
}
```

**Supported prompt types:**
- `basic` - Basic text prompts
- `advanced` - Advanced text prompts
- `advanced_image` - Image generation prompts
- `advanced_reverse` - Reverse image prompts
- `refinement` - Refined prompts

## Error Responses

### Standard Error Format
```json
{
    "success": false,
    "error": "Error message here",
    "code": "ERROR_CODE"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `INSUFFICIENT_POINTS` | Not enough points for the action |
| `CSRF_INVALID` | CSRF token validation failed |
| `API_KEY_INVALID` | API key validation failed |
| `PROMPT_NOT_FOUND` | Requested prompt not found |
| `PERMISSION_DENIED` | User doesn't have permission |
| `RATE_LIMITED` | Too many requests |

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `400` | Bad Request |
| `401` | Unauthorized |
| `403` | Forbidden |
| `404` | Not Found |
| `429` | Too Many Requests |
| `500` | Internal Server Error |

## Rate Limiting

### Limits
- **API Calls**: 60 requests per minute per user
- **Generation**: 100 generations per day per user (without API key)
- **Login Attempts**: 5 attempts per 15 minutes per IP

### Headers
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
```

## WebSocket/SSE Endpoints

### Streaming Generation
```http
POST /generate/tprompt/stream
```

**Response:** Server-Sent Events
```
data: Generated chunk 1

data: Generated chunk 2

data: [DONE]
```

## SDK Examples

### JavaScript
```javascript
class PromptSanctuaryAPI {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.csrfToken = this.getCSRFToken();
    }

    getCSRFToken() {
        return document.querySelector('meta[name=csrf-token]').getAttribute('content');
    }

    async generatePrompt(text) {
        const response = await fetch(`${this.baseUrl}/generate/tprompt`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': this.csrfToken
            },
            body: `user_input_text=${encodeURIComponent(text)}&csrf_token=${this.csrfToken}`
        });

        return response.json();
    }

    async savePrompt(title, prompt) {
        const response = await fetch(`${this.baseUrl}/save_prompt`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': this.csrfToken
            },
            body: `title=${encodeURIComponent(title)}&prompt=${encodeURIComponent(prompt)}&csrf_token=${this.csrfToken}`
        });

        return response.json();
    }
}

// Usage
const api = new PromptSanctuaryAPI('https://sanctuary01.pythonanywhere.com');
const result = await api.generatePrompt('Create a story about a robot');
```

### Python
```python
import requests
import json

class PromptSanctuaryAPI:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()

    def login(self, username, password):
        response = self.session.post(f"{self.base_url}/login", data={
            'username': username,
            'password': password
        })
        return response.json()

    def generate_prompt(self, text):
        response = self.session.post(f"{self.base_url}/generate/tprompt", data={
            'user_input_text': text
        })
        return response.json()

    def save_prompt(self, title, prompt):
        response = self.session.post(f"{self.base_url}/save_prompt", data={
            'title': title,
            'prompt': prompt
        })
        return response.json()

# Usage
api = PromptSanctuaryAPI('https://sanctuary01.pythonanywhere.com')
api.login('username', 'password')
result = api.generate_prompt('Create a story about a robot')
```

---

*This API reference covers all current endpoints. For the latest updates and new endpoints, check the [development documentation](../development/).*
