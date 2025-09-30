# AI-Powered Title Generation

The AI-powered title generation feature automatically creates intelligent, descriptive titles for saved prompts using advanced AI analysis.

## Overview

This feature analyzes prompt content and context to generate concise, meaningful titles that accurately represent the prompt's purpose and content. It's available across all prompt generation interfaces and provides much better titles than manual parsing.

## Key Features

### Smart Title Generation

- **Context-Aware**: AI understands the prompt's purpose and content
- **Concise Format**: Generates 3-8 word titles for perfect readability
- **Type-Specific**: Different analysis approaches for different prompt types
- **Fallback Protection**: Graceful degradation if AI generation fails

### Multi-Generator Support

- **Basic Generator**: Analyzes simple text prompts
- **Advanced Generator**: Handles complex multi-parameter prompts
- **Image Prompts**: Understands visual content and style
- **Reverse Image**: Analyzes image description prompts
- **Refined Prompts**: Recognizes improvements and enhancements

### Cost-Effective Pricing

- **Standard Cost**: 0.2 points per title generation
- **API Key Users**: Free for users with validated API keys
- **Automatic Fallback**: Uses content-based titles if AI fails

## Implementation Details

### API Integration

- **Endpoint**: `/generate_title`
- **Method**: POST
- **Authentication**: Required (login)
- **Cost**: 0.2 points (if user doesn't have API key)

#### Request Format
```javascript
{
  prompt_text: "Full prompt content",
  prompt_type: "basic" | "advanced" | "advanced_image" | "advanced_reverse" | "refinement"
}
```

#### Response Format
```json
{
  "success": true,
  "title": "Smart AI-Generated Title",
  "points_used": 0.2,
  "remaining_points": 92.8
}
```

### AI Prompt Templates

#### Basic Prompts
```
"Generate a concise, descriptive title (3-8 words) for this basic prompt. Focus on the main purpose or topic:

Prompt content:
{prompt_text}

Title:"
```

#### Advanced Prompts
```
"Generate a concise, descriptive title (3-8 words) for this advanced prompt. Focus on the main purpose or topic:

Prompt content:
{prompt_text}

Title:"
```

#### Image Generation Prompts
```
"Generate a concise, descriptive title (3-8 words) for this image generation prompt. Focus on the visual content or style:

Prompt content:
{prompt_text}

Title:"
```

#### Reverse Image Prompts
```
"Generate a concise, descriptive title (3-8 words) for this reverse image prompt. Focus on the analysis or description:

Prompt content:
{prompt_text}

Title:"
```

#### Refined Prompts
```
"Generate a concise, descriptive title (3-8 words) for this refined prompt. Focus on the improvement or enhancement:

Prompt content:
{prompt_text}

Title:"
```

## User Experience

### Automatic Integration

The title generation is seamlessly integrated into the save process:

1. **User Clicks Save** → Save function called
2. **AI Title Generation** → Request sent to `/generate_title`
3. **Smart Title Created** → AI analyzes content and generates title
4. **Fallback Handling** → Uses content-based title if AI fails
5. **Prompt Saved** → Saved with intelligent title

### Loading States

- **Generation Loading**: Shows loading indicator during AI processing
- **Error Handling**: Graceful fallback to manual title generation
- **Success Feedback**: User sees the AI-generated title before saving

### Fallback System

If AI title generation fails, the system automatically falls back to content-based titles:

#### Basic Generator Fallback
```javascript
const promptPreview = generatedText.trim().substring(0, 40);
title = `Basic: ${promptPreview}${generatedText.length > 40 ? '...' : ''}`;
```

#### Advanced Generator Fallback
```javascript
const promptPreview = generatedText.trim().substring(0, 40);
const imageMode = document.querySelector('input[name="imageMode"]:checked')?.value;
if (imageMode === 'generate') {
    title = `Image: ${promptPreview}${generatedText.length > 40 ? '...' : ''}`;
} else if (imageMode === 'reverse') {
    title = `Reverse: ${promptPreview}${generatedText.length > 40 ? '...' : ''}`;
} else {
    title = `Advanced: ${promptPreview}${generatedText.length > 40 ? '...' : ''}`;
}
```

#### Refinement Fallback
```javascript
const originalTitle = selectedPromptData ? selectedPromptData.title : 'Manual Input';
const action = selectedAction || 'Custom';
title = `${originalTitle} - Refined (${action})`;
```

## Technical Architecture

### Frontend Implementation

#### JavaScript Integration
```javascript
async function saveGeneratedPrompt() {
    const generatedText = document.getElementById('generated-prompt-text').textContent;
    
    // Show loading state
    showLoading();
    
    try {
        // Generate AI title
        const titleResponse = await fetch('/generate_title', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                ...window.CSRF.getFormHeaders()
            },
            body: new URLSearchParams({
                'prompt_text': generatedText.trim(),
                'prompt_type': 'basic' // or 'advanced', 'refinement', etc.
            })
        });
        
        const titleData = await titleResponse.json();
        let title = 'Generated Prompt';
        
        if (titleData.success && titleData.title) {
            title = titleData.title;
        } else {
            // Fallback to content-based title
            title = generateFallbackTitle(generatedText, promptType);
        }
        
        // Save prompt with title
        const response = await fetch('/save_prompt', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                ...window.CSRF.getFormHeaders()
            },
            body: new URLSearchParams({
                'title': title,
                'prompt': generatedText.trim()
            })
        });
        
        // Handle response...
        
    } catch (error) {
        // Error handling...
    }
}
```

### Backend Implementation

#### Flask Route
```python
@main_blueprint.route("/generate_title", methods=["POST"])
@required_login
def generate_title():
    if request.method == "POST":
        prompt_text = request.form.get("prompt_text", "").strip()
        prompt_type = request.form.get("prompt_type", "basic").strip()
        username = session["username"]

        if not prompt_text:
            return jsonify({"success": False, "error": "Prompt text is required."}), 400

        try:
            # Check if user has enough points (title generation costs 0.2 points)
            cost = 0.2
            user_has_api_key = is_api_key_validated(main_blueprint.user_db, username)
            
            if not user_has_api_key:
                if not deduct_user_points_with_source(main_blueprint.user_db, username, cost, 'title_generation', f'Generated title for {prompt_type} prompt'):
                    current_points = get_user_points(main_blueprint.user_db, username)
                    return jsonify({"success": False, "error": f"Insufficient points. You need {cost} points but have {current_points}."}), 402

            # Create title generation prompt based on type
            title_prompts = {
                'basic': "Generate a concise, descriptive title (3-8 words) for this basic prompt. Focus on the main purpose or topic:",
                'advanced': "Generate a concise, descriptive title (3-8 words) for this advanced prompt. Focus on the main purpose or topic:",
                'advanced_image': "Generate a concise, descriptive title (3-8 words) for this image generation prompt. Focus on the visual content or style:",
                'advanced_reverse': "Generate a concise, descriptive title (3-8 words) for this reverse image prompt. Focus on the analysis or description:",
                'refinement': "Generate a concise, descriptive title (3-8 words) for this refined prompt. Focus on the improvement or enhancement:"
            }
            
            title_prompt = title_prompts.get(prompt_type, title_prompts['basic'])
            full_prompt = f"{title_prompt}\n\nPrompt content:\n{prompt_text}\n\nTitle:"

            # Set user API key if available
            user_api_key = get_user_api_key(main_blueprint.user_db, username)
            if user_api_key:
                model.set_user_api_key(user_api_key)

            # Generate title using AI
            title = model._generate_content_with_retry(full_prompt, model.get_effective_api_key(), use_streaming=False)
            
            if title and title.strip():
                # Clean up the title
                clean_title = title.strip()
                # Remove quotes if present
                clean_title = clean_title.strip('"\'')
                # Ensure it's not too long
                if len(clean_title) > 60:
                    clean_title = clean_title[:57] + "..."
                
                return jsonify({"success": True, "title": clean_title})
            else:
                return jsonify({"success": False, "error": "Failed to generate title."}), 500

        except Exception as e:
            logger.error(f"Error generating title for {username}: {e}")
            return jsonify({"success": False, "error": "Failed to generate title."}), 500

    return jsonify({"success": False, "error": "Invalid request method."}), 405
```

## Benefits

### For Users

1. **Better Organization**: Intelligent titles make prompts easier to find and manage
2. **Time Saving**: No need to manually create descriptive titles
3. **Consistency**: Standardized title format across all saved prompts
4. **Context Awareness**: Titles reflect the actual content and purpose

### For Developers

1. **Seamless Integration**: Works across all generation interfaces
2. **Robust Fallbacks**: Graceful degradation if AI fails
3. **Cost Control**: Reasonable pricing with API key exemptions
4. **Type Awareness**: Different approaches for different prompt types

## Example Results

### Basic Prompt Examples

**Original Content**: "Write a Python function that calculates the factorial of a number with error handling and type hints"
**AI Title**: `"Python Factorial Function Guide"`

**Original Content**: "Create a marketing email for a new product launch targeting millennials"
**AI Title**: `"Millennial Product Launch Email"`

### Advanced Prompt Examples

**Original Content**: Complex multi-parameter prompt for image generation
**AI Title**: `"Fantasy Landscape Art Prompt"`

**Original Content**: Reverse image analysis prompt
**AI Title**: `"Image Analysis Description Guide"`

### Refinement Examples

**Original Content**: Refined version of a basic prompt
**AI Title**: `"Enhanced Python Development Guide"`

## Future Enhancements

### Potential Improvements

1. **Multi-Language Support**: Generate titles in different languages
2. **Custom Templates**: User-defined title generation styles
3. **Batch Processing**: Generate titles for multiple prompts at once
4. **Learning System**: Improve based on user feedback and usage patterns

### Integration Opportunities

1. **Tag Generation**: Automatic tag suggestions based on content
2. **Category Detection**: Automatic categorization of prompts
3. **Quality Scoring**: Assess prompt quality and suggest improvements
4. **Trend Analysis**: Identify popular prompt patterns and styles

## Testing

### Test Scenarios

1. **Basic Prompt Titles**: Various types of basic prompts
2. **Advanced Prompt Titles**: Complex multi-parameter prompts
3. **Image Prompt Titles**: Visual content and style analysis
4. **Refinement Titles**: Enhanced and improved prompts
5. **Error Handling**: Network failures and API errors
6. **Fallback System**: AI failure scenarios
7. **Point Deduction**: Users without API keys
8. **Free Usage**: Users with validated API keys

### Quality Assurance

- **Title Relevance**: Ensure titles accurately reflect content
- **Length Validation**: Verify titles are within 3-8 word range
- **Fallback Testing**: Test manual title generation when AI fails
- **Performance Testing**: Ensure quick response times
- **Cost Verification**: Confirm correct point deduction

## Conclusion

The AI-powered title generation feature significantly improves the user experience by providing intelligent, context-aware titles for all saved prompts. This leads to better organization, easier discovery, and more professional prompt libraries.

The implementation is designed to be cost-effective, reliable, and seamlessly integrated into the existing workflow with robust fallback mechanisms.
