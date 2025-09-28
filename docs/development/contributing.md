# Contributing to Prompt Sanctuary

Thank you for your interest in contributing to Prompt Sanctuary! This guide will help you get started with contributing to the project.

## Getting Started

### Prerequisites
- **Python 3.8+**: Required for development
- **Git**: For version control
- **Google AI Studio API Key**: For testing AI features
- **Basic Knowledge**: Python, Flask, JavaScript, and HTML/CSS

### Development Setup
1. **Fork the Repository**: Create your own fork on GitHub
2. **Clone Your Fork**: `git clone https://github.com/your-username/prompt-sanctuary.git`
3. **Set Up Environment**: Follow the [Development Setup Guide](setup.md)
4. **Create Branch**: `git checkout -b feature/your-feature-name`

## Contribution Guidelines

### Code of Conduct
We follow a code of conduct that ensures a welcoming environment for all contributors:
- **Be Respectful**: Treat all contributors with respect
- **Be Inclusive**: Welcome contributors from all backgrounds
- **Be Constructive**: Provide helpful feedback and suggestions
- **Be Patient**: Understand that everyone has different skill levels

### Types of Contributions

#### Bug Reports
- **Clear Description**: Provide detailed steps to reproduce
- **Environment Info**: Include Python version, OS, browser
- **Expected vs Actual**: Describe expected and actual behavior
- **Screenshots**: Include screenshots if applicable

#### Feature Requests
- **Problem Statement**: Clearly describe the problem you're solving
- **Proposed Solution**: Outline your proposed solution
- **Use Cases**: Provide real-world use cases
- **Alternative Solutions**: Consider other possible approaches

#### Code Contributions
- **Small Changes**: Prefer smaller, focused changes
- **Clear Commits**: Write clear, descriptive commit messages
- **Tests**: Include tests for new features
- **Documentation**: Update documentation for new features

### Development Workflow

#### Branch Naming
Use descriptive branch names:
```
feature/add-dark-mode
bugfix/fix-mobile-layout
docs/update-api-documentation
refactor/improve-database-queries
```

#### Commit Messages
Follow conventional commit format:
```
feat: add dark mode toggle
fix: resolve mobile layout issues
docs: update user manual
refactor: improve database performance
test: add unit tests for prompt generation
```

#### Pull Request Process
1. **Create Feature Branch**: `git checkout -b feature/new-feature`
2. **Make Changes**: Implement your feature or fix
3. **Test Changes**: Ensure all tests pass
4. **Update Documentation**: Update relevant documentation
5. **Commit Changes**: Use clear, descriptive commit messages
6. **Push Branch**: `git push origin feature/new-feature`
7. **Create PR**: Submit pull request with detailed description

## Coding Standards

### Python Code Style

#### Formatting
- **Black**: Use Black for code formatting
- **Line Length**: Maximum 88 characters per line
- **Imports**: Organize imports (standard, third-party, local)
- **Docstrings**: Include docstrings for functions and classes

#### Example Python Code
```python
def validate_api_key(api_key: str) -> Tuple[bool, str]:
    """
    Validate a Gemini API key by making a test request.
    
    Args:
        api_key: The API key to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not api_key or len(api_key) < 20:
        return False, "Invalid API key format"
    
    try:
        # Test the API key
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Test")
        return True, "API key is valid"
    except Exception as e:
        return False, f"Validation failed: {str(e)}"
```

### JavaScript Code Style

#### Formatting
- **Consistent Indentation**: Use 2 spaces for indentation
- **Camel Case**: Use camelCase for variables and functions
- **Comments**: Include comments for complex logic
- **Error Handling**: Always handle errors gracefully

#### Example JavaScript Code
```javascript
class PromptRefinement {
    constructor() {
        this.thresholds = {
            short: 50,
            long: 200,
            veryLong: 400
        };
        this.init();
    }
    
    async refinePrompt(text, action) {
        try {
            const response = await fetch('/refine_prompt', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCSRFToken()
                },
                body: `text=${encodeURIComponent(text)}&action=${action}`
            });
            
            const data = await response.json();
            return data.success ? data.result : null;
        } catch (error) {
            console.error('Refinement failed:', error);
            return null;
        }
    }
}
```

### CSS Code Style

#### Tailwind CSS Usage
- **Utility Classes**: Use Tailwind utility classes
- **Custom Components**: Create reusable component classes
- **Responsive Design**: Mobile-first approach
- **Accessibility**: Include proper ARIA attributes

#### Example CSS Code
```css
/* Custom component using Tailwind utilities */
.prompt-card {
    @apply bg-white/40 border border-white/30 rounded-xl p-6 shadow-glass;
    @apply hover:bg-white/50 transition-all duration-300;
    @apply backdrop-blur-xl;
}

.prompt-card:hover {
    @apply shadow-lg transform scale-105;
}

/* Responsive design */
@media (max-width: 768px) {
    .prompt-card {
        @apply p-4 text-sm;
    }
}
```

## Testing Guidelines

### Test Structure
```
tests/
├── unit/                   # Unit tests
│   ├── test_models.py     # Database model tests
│   ├── test_routes.py     # Route handler tests
│   └── test_utils.py      # Utility function tests
├── integration/           # Integration tests
│   ├── test_api.py        # API endpoint tests
│   └── test_auth.py       # Authentication tests
└── e2e/                   # End-to-end tests
    ├── test_generation.py # Prompt generation workflow
    └── test_community.py  # Community features
```

### Writing Tests

#### Unit Tests
```python
import pytest
from web.models import validate_api_key

def test_validate_api_key_valid():
    """Test API key validation with valid key."""
    # Mock the API response
    with patch('web.models.genai') as mock_genai:
        mock_genai.configure.return_value = None
        mock_model = MagicMock()
        mock_model.generate_content.return_value = MagicMock(text="Test")
        mock_genai.GenerativeModel.return_value = mock_model
        
        result = validate_api_key("AIzaSyC...")
        assert result[0] is True
        assert "valid" in result[1]

def test_validate_api_key_invalid():
    """Test API key validation with invalid key."""
    result = validate_api_key("invalid")
    assert result[0] is False
    assert "Invalid" in result[1]
```

#### Integration Tests
```python
def test_prompt_generation(client, authenticated_user):
    """Test prompt generation endpoint."""
    response = client.post('/generate/tprompt', data={
        'user_input_text': 'Create a story about a robot',
        'csrf_token': get_csrf_token()
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'result' in data
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_models.py

# Run with coverage
pytest --cov=web tests/

# Run specific test
pytest tests/unit/test_models.py::test_validate_api_key_valid
```

## Documentation Guidelines

### Documentation Types
- **API Documentation**: Document all API endpoints
- **User Documentation**: Update user guides for new features
- **Technical Documentation**: Document architecture and design decisions
- **Code Documentation**: Include docstrings and comments

### Documentation Standards
- **Clear Language**: Use clear, concise language
- **Examples**: Include code examples where helpful
- **Screenshots**: Add screenshots for UI changes
- **Up-to-date**: Keep documentation current with code changes

### Documentation Structure
```
docs/
├── README.md              # Main documentation index
├── user-guide/            # User documentation
├── features/              # Feature documentation
├── technical/             # Technical documentation
└── development/           # Development documentation
```

## Review Process

### Pull Request Requirements
- **Clear Description**: Detailed description of changes
- **Tests**: Include tests for new features
- **Documentation**: Update relevant documentation
- **Screenshots**: Include screenshots for UI changes
- **Breaking Changes**: Clearly mark any breaking changes

### Review Criteria
- **Code Quality**: Follows coding standards
- **Functionality**: Works as expected
- **Performance**: No performance regressions
- **Security**: No security vulnerabilities
- **Documentation**: Documentation is updated

### Review Process
1. **Automated Checks**: CI/CD pipeline runs tests
2. **Code Review**: Maintainers review code changes
3. **Testing**: Manual testing of changes
4. **Approval**: Maintainer approval required
5. **Merge**: Changes merged to main branch

## Development Tools

### Recommended Tools
- **IDE**: VS Code, PyCharm, or similar
- **Git Client**: GitHub Desktop, SourceTree, or command line
- **API Testing**: Postman or similar for API testing
- **Browser DevTools**: For frontend debugging

### VS Code Extensions
```json
{
    "recommendations": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "ms-python.black-formatter",
        "ms-python.flake8",
        "bradlc.vscode-tailwindcss",
        "esbenp.prettier-vscode"
    ]
}
```

### Git Hooks
```bash
# Pre-commit hook
#!/bin/sh
# Run Black formatter
black web/

# Run flake8 linter
flake8 web/

# Run tests
pytest tests/unit/
```

## Community Guidelines

### Communication
- **GitHub Issues**: Use issues for bug reports and feature requests
- **GitHub Discussions**: Use discussions for questions and ideas
- **Pull Requests**: Use PRs for code contributions
- **Discord/Slack**: Join community channels for real-time chat

### Getting Help
- **Documentation**: Check existing documentation first
- **Search Issues**: Look for similar issues or discussions
- **Ask Questions**: Don't hesitate to ask questions
- **Be Patient**: Maintainers are volunteers with limited time

### Recognition
- **Contributors**: All contributors are recognized
- **Special Thanks**: Major contributors get special recognition
- **Hall of Fame**: Long-term contributors in project documentation
- **Social Media**: Contributions highlighted on social media

## Release Process

### Version Numbering
We use semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Release Schedule
- **Patch Releases**: As needed for bug fixes
- **Minor Releases**: Monthly for new features
- **Major Releases**: As needed for breaking changes

### Release Process
1. **Feature Freeze**: Stop adding new features
2. **Testing**: Comprehensive testing of release
3. **Documentation**: Update all documentation
4. **Release Notes**: Create detailed release notes
5. **Deployment**: Deploy to production
6. **Announcement**: Announce release to community

## License

By contributing to Prompt Sanctuary, you agree that your contributions will be licensed under the same license as the project. See the main project README for license details.

## Questions?

If you have any questions about contributing:
- **Check Documentation**: Look through existing documentation
- **Search Issues**: Look for similar questions or discussions
- **Create Issue**: Create a new issue for your question
- **Join Community**: Join our community channels

Thank you for contributing to Prompt Sanctuary! 🚀
