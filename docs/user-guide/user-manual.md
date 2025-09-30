# Prompt Sanctuary User Manual

Complete guide to all features and functionality in Prompt Sanctuary.

## Table of Contents

1. [Account Management](#account-management)
2. [Prompt Generation](#prompt-generation)
3. [Personal Library](#personal-library)
4. [Community Features](#community-features)
5. [Economy System](#economy-system)
6. [API Key Management](#api-key-management)
7. [Settings & Preferences](#settings--preferences)
8. [Advanced Features](#advanced-features)

## Account Management

### User Profile
Access your profile by clicking your username in the sidebar or navigating to the profile page.

#### Profile Information
- **Username**: Your unique identifier (can be changed)
- **Email**: Optional email address for account recovery
- **Points Balance**: Current available points
- **Join Date**: When you created your account
- **Achievements**: Unlocked achievements and progress

#### Account Settings
- **Change Username**: Update your display name
- **Update Email**: Add or change email address
- **Change Password**: Update your account password
- **Session Management**: View and revoke active sessions

### Session Management
- **Active Sessions**: View all devices logged into your account
- **Revoke Sessions**: Log out from specific devices
- **Security**: Monitor for unauthorized access

## Prompt Generation

### Basic Generation

#### Text Prompt Generation
1. Navigate to **Generate** from the main menu
2. Enter your prompt idea in the text input field
3. Watch the character counter and refinement suggestions
4. Click **Generate** to create your prompt
5. Review the AI-generated result

#### Random Prompt Generation
1. Click **Generate Random** for surprise prompts
2. Use as inspiration or starting points
3. Modify generated prompts to suit your needs

### Advanced Generation

#### Custom Parameters
- **Use Case**: Specify the intended use of the prompt
- **Knowledge Base**: Add domain-specific information
- **Safety Level**: Adjust content filtering settings
- **Custom Instructions**: Add specific requirements

#### Advanced Options
- **Model Selection**: Choose between different AI models
- **Temperature**: Control creativity vs consistency
- **Max Length**: Set maximum response length
- **Custom Templates**: Use pre-built prompt templates

### Prompt Refinement

#### Dedicated Refinement Interface
Access the comprehensive refinement tool at `/refinement` to optimize prompts from multiple sources:

1. **Select Prompt Source**:
   - **Manual Input**: Type or paste prompts directly
   - **Saved Prompts**: Choose from your personal library
   - **Community Prompts**: Select from community-shared prompts

2. **Choose Refinement Action**:
   - **Shorten**: Make prompts more concise while preserving meaning
   - **Elaborate**: Add details, context, and specificity
   - **Improve**: Enhance overall prompt quality and effectiveness
   - **Fix Grammar**: Correct grammar, spelling, and language issues
   - **Custom Instructions**: Specify exactly how to refine your prompt

3. **Review and Save Results**:
   - Copy refined prompts to clipboard
   - Save with AI-generated smart titles
   - Refine again with different actions

## Personal Library

### Managing Saved Prompts

#### Saving Prompts
1. After generating a prompt, click **Save**
2. Enter a descriptive title
3. Add relevant tags for organization
4. Choose sharing preferences
5. Confirm to save to your library

#### Organization Features
- **Tags**: Categorize prompts by topic, use case, or domain
- **Search**: Find prompts by title, content, or tags
- **Sorting**: Order by date, title, or usage
- **Filtering**: Show only shared, private, or specific types

### Version Control

#### Automatic Versioning
- Every save creates a new version
- Edit operations create version snapshots
- Track changes over time
- Compare different versions

#### Version History
1. Click **History** button on any saved prompt
2. View all previous versions with timestamps
3. Preview content of any version
4. Restore to any previous version
5. Fork from any version to create new variations

#### Version Management
- **Restore**: Revert to a previous version
- **Fork**: Create a new prompt based on an old version
- **Compare**: See differences between versions
- **Delete**: Remove unwanted versions

### Prompt Editing

#### In-Place Editing
1. Click **Edit** on any saved prompt
2. Modify the content in the editor
3. Save changes to create a new version
4. Update title or tags if needed

#### Bulk Operations
- **Duplicate**: Create copies of prompts
- **Archive**: Move prompts to archive
- **Delete**: Remove prompts permanently
- **Export**: Download prompts for backup

## Community Features

### Community Library

#### Browsing Shared Prompts
1. Navigate to **Library** from the main menu
2. Browse featured and popular prompts
3. Use search and filters to find specific types
4. View prompt details and usage statistics

#### Sharing Your Prompts
1. Save a prompt with "Share with Community" enabled
2. Prompt becomes visible to other users
3. Others can copy and use your prompts
4. Earn community recognition and points

#### Community Interactions
- **Copy Prompts**: Use community prompts in your library
- **Rate Prompts**: Provide feedback on shared prompts
- **Follow Users**: Keep track of users who share good prompts
- **Collections**: Organize prompts into themed collections

### Discovery Features

#### Search and Filter
- **Text Search**: Find prompts by content or title
- **Tag Filtering**: Filter by specific tags or categories
- **Sort Options**: Sort by popularity, date, or rating
- **Advanced Filters**: Filter by author, date range, or prompt type

#### Recommendations
- **Similar Prompts**: Find prompts related to your interests
- **Trending**: See what's popular in the community
- **Featured**: Highlighted prompts by the community
- **Personalized**: Recommendations based on your usage

## Economy System

### Point System Overview

#### Earning Points
- **Starting Balance**: 80 points for new users
- **Daily Login**: 5-12 random points per day
- **Achievements**: Bonus points for milestones
- **API Key Contribution**: 100 points for adding your key
- **Community Sharing**: Points for helpful contributions

#### Spending Points
- **Basic Text Generation**: 1.0 points
- **Advanced Text Generation**: 1.0 points
- **Advanced Image Generation**: 1.0 points
- **Advanced Reverse Image**: 1.0 points
- **Prompt Refinement**: 0.5 points
- **AI Title Generation**: 0.2 points

#### Point Management
- **Balance Tracking**: Monitor your current points
- **Transaction History**: View detailed point usage
- **Expiration**: Points expire based on source (17-95 days)
- **Point Cap**: Maximum 500 points per user

### Achievement System

#### Achievement Categories
- **Generation**: Create a certain number of prompts
- **Sharing**: Share prompts with the community
- **Consistency**: Maintain daily login streaks
- **Exploration**: Try different features and tools
- **Community**: Help other users and contribute

#### Unlocking Achievements
- **Automatic Detection**: System tracks your progress
- **Instant Rewards**: Points awarded immediately
- **Progress Tracking**: See progress toward next achievement
- **Hidden Achievements**: Surprise achievements to discover

#### Achievement Benefits
- **Point Rewards**: Earn bonus points for achievements
- **Community Recognition**: Show off your accomplishments
- **Progress Motivation**: Goals to work toward
- **Exclusive Features**: Some features unlock with achievements

## API Key Management

### Personal API Keys

#### Adding Your API Key
1. Go to your **Profile** page
2. Navigate to **API Key Settings**
3. Enter your Gemini API key
4. Click **Validate** to test the key
5. Earn 100 bonus points for successful validation

#### Benefits of Personal API Keys
- **No Point Costs**: Generate prompts, refine prompts, and create titles without spending points
- **Unlimited Usage**: No daily limits or restrictions
- **Priority Access**: Faster response times
- **Community Contribution**: Help other users when your key is used

#### API Key Security
- **Secure Storage**: Keys encrypted and stored safely
- **Validation**: Real-time testing ensures keys work
- **Rotation**: Update keys when needed
- **Revocation**: Remove keys if compromised

### API Key Pool System

#### How Pooling Works
- Validated keys are shared with the community
- Fair rotation ensures equitable usage
- Users earn compensation when their key is used
- System automatically manages key rotation

#### Compensation System
- **Usage Compensation**: 0.5 points per use of your key
- **Fair Distribution**: LRU rotation ensures fairness
- **Usage Tracking**: Monitor how often your key is used
- **Automatic Rewards**: Compensation added automatically

#### Pool Management
- **Health Monitoring**: Track key performance and reliability
- **Automatic Refresh**: Add new keys to the pool
- **Usage Statistics**: View pool performance metrics
- **Key Rotation**: Automatic switching between available keys

## Settings & Preferences

### Language Settings

#### Multilingual Support
- **Available Languages**: English and Indonesian
- **Language Switching**: Instant switching via sidebar buttons
- **Session Persistence**: Language choice saved across sessions
- **Complete Coverage**: All UI elements translated

#### Language Features
- **Default Language**: English (reliable fallback)
- **Browser Detection**: Automatic language detection
- **Manual Override**: Choose your preferred language
- **Real-time Switching**: No page reload required

### Display Preferences

#### Theme Settings
- **Current Theme**: Pastel theme with glassmorphism effects
- **Future Support**: Dark mode toggle planned
- **Responsive Design**: Optimized for all screen sizes
- **Accessibility**: High contrast and readable fonts

#### UI Customization
- **Layout Options**: Choose between different layouts
- **Density Settings**: Adjust spacing and element sizes
- **Animation Preferences**: Control motion and transitions
- **Accessibility Options**: Enhanced accessibility features

### Notification Settings

#### Achievement Notifications
- **Unlock Alerts**: Get notified when achievements unlock
- **Progress Updates**: Track progress toward achievements
- **Milestone Celebrations**: Special notifications for major milestones
- **Customizable Alerts**: Choose which notifications to receive

#### System Notifications
- **Maintenance Alerts**: Scheduled maintenance notifications
- **Feature Updates**: New feature announcements
- **Security Alerts**: Important security information
- **Community Updates**: Community-related announcements

## Advanced Features

### Batch Operations

#### Bulk Prompt Management
- **Select Multiple**: Choose multiple prompts for batch operations
- **Bulk Edit**: Modify multiple prompts at once
- **Bulk Delete**: Remove multiple prompts efficiently
- **Bulk Share**: Share multiple prompts with community

#### Import/Export
- **Export Library**: Download your prompts as JSON or Markdown
- **Import Prompts**: Upload prompts from other sources
- **Backup/Restore**: Create backups of your library
- **Migration Tools**: Move prompts between accounts

### Advanced Search

#### Search Capabilities
- **Full-Text Search**: Search through prompt content
- **Tag-Based Search**: Find prompts by specific tags
- **Author Search**: Find prompts by specific users
- **Date Range**: Filter prompts by creation date

#### Search Filters
- **Content Type**: Filter by prompt type or category
- **Length**: Find prompts of specific lengths
- **Popularity**: Sort by community usage
- **Quality**: Filter by rating or feedback

### Analytics & Insights

#### Usage Analytics
- **Generation Stats**: Track prompts generated over time
- **Popular Tags**: See which tags you use most
- **Success Rate**: Monitor prompt effectiveness
- **Time Patterns**: Understand your usage patterns

#### Community Insights
- **Trending Topics**: See what's popular in the community
- **Your Impact**: Track how your shared prompts perform
- **Community Engagement**: Monitor interactions with your prompts
- **Collaboration Stats**: Track community contributions

## Troubleshooting

### Common Issues

#### Login Problems
- **Forgot Password**: Use email recovery if available
- **Account Locked**: Contact support for assistance
- **Session Issues**: Clear browser cache and cookies
- **Browser Compatibility**: Ensure you're using a supported browser

#### Generation Issues
- **No Response**: Check your internet connection
- **Slow Generation**: Try using your own API key
- **Point Issues**: Verify your point balance
- **Error Messages**: Check the troubleshooting guide

#### Feature Problems
- **Missing Features**: Ensure you're using the latest version
- **UI Issues**: Try refreshing the page
- **Data Loss**: Check if prompts are in your library
- **Performance**: Clear browser cache and restart

### Getting Help

#### Support Resources
1. **Documentation**: Check this manual and feature guides
2. **Community Forums**: Ask questions in community discussions
3. **GitHub Issues**: Report bugs or request features
4. **Email Support**: Contact support for account issues

#### Reporting Issues
- **Bug Reports**: Include steps to reproduce and browser info
- **Feature Requests**: Describe the desired functionality
- **Performance Issues**: Include system specifications
- **Security Concerns**: Report security issues privately

## Best Practices

### Prompt Engineering
1. **Be Specific**: Include clear, detailed instructions
2. **Provide Context**: Set up the situation or domain
3. **Use Examples**: Show what good output looks like
4. **Iterate and Improve**: Use refinement suggestions
5. **Test and Validate**: Verify prompts work as expected

### Library Management
1. **Organize with Tags**: Use consistent tagging system
2. **Descriptive Titles**: Make prompts easy to find
3. **Regular Cleanup**: Remove outdated or unused prompts
4. **Version Control**: Keep track of prompt evolution
5. **Backup Important Prompts**: Export critical prompts

### Community Participation
1. **Share Quality Prompts**: Only share well-tested prompts
2. **Provide Feedback**: Rate and comment on community prompts
3. **Help Others**: Answer questions and provide assistance
4. **Follow Guidelines**: Respect community standards
5. **Give Credit**: Acknowledge sources when appropriate

---

*This manual covers all current features. For the latest updates and new features, check the [release notes](../development/release-notes.md) and [feature documentation](../features/).*
