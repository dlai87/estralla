# Production-Quality Code Examples Generation Prompt

## Objective

Generate production-ready code examples for technical curriculum that demonstrate best practices, include comprehensive error handling, and provide educational value for learners.

---

## Context

You are creating code examples for a technical training module. These examples will be used by learners to understand concepts and implement real-world solutions. The code must be:
- Production-quality (not toy examples)
- Educational (well-commented and explained)
- Complete (runnable without modifications)
- Secure (no vulnerabilities)
- Following current best practices

---

## Input Requirements

Provide the following information:

1. **Topic**: What concept does this example demonstrate?
2. **Programming Language**: Python, JavaScript, Go, etc.
3. **Complexity Level**: Beginner, Intermediate, Advanced
4. **Learning Objectives**: What should learners understand after studying this example?
5. **Context/Scenario**: Real-world use case this addresses
6. **Constraints**: Any specific requirements (libraries, versions, etc.)

---

## Output Format

For each code example, generate:

### 1. Context Comment Block

```python
"""
Context: [When and why to use this pattern]
Use Case: [Specific problem this solves]
Prerequisites: [What learners need to know first]
Concepts Demonstrated: [Key concepts shown in this example]

Learning Objectives:
1. [Objective 1]
2. [Objective 2]
3. [Objective 3]

Real-World Application:
[How this is used in production environments]
"""
```

### 2. Imports with Comments

```python
# Core Python libraries
import os
import sys
from typing import Dict, List, Optional

# Third-party libraries (with version requirements)
import requests  # requests>=2.31.0
from pydantic import BaseModel, Field, validator  # pydantic>=2.0.0

# Project-specific imports
from .config import Settings
from .utils import logger
```

### 3. Type Definitions (if applicable)

```python
class UserData(BaseModel):
    """
    Data model for user information.

    Attributes:
        user_id: Unique identifier for the user
        email: User's email address (validated)
        created_at: Timestamp of user creation

    Example:
        >>> user = UserData(user_id=123, email="user@example.com")
    """
    user_id: int = Field(..., description="Unique user identifier", gt=0)
    email: str = Field(..., description="User email address")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('email')
    def validate_email(cls, v):
        """Validate email format."""
        if '@' not in v:
            raise ValueError('Invalid email address')
        return v.lower()
```

### 4. Main Implementation

```python
def process_user_data(
    user_id: int,
    data: Dict[str, Any],
    timeout: int = 30,
    retry_count: int = 3
) -> Optional[UserData]:
    """
    Process user data with validation and error handling.

    This function demonstrates:
    - Input validation
    - Error handling with retries
    - Logging for debugging
    - Type safety
    - Production-ready patterns

    Args:
        user_id: The unique identifier for the user
        data: Dictionary containing user data to process
        timeout: Request timeout in seconds (default: 30)
        retry_count: Number of retries on failure (default: 3)

    Returns:
        UserData object if successful, None if processing fails

    Raises:
        ValueError: If user_id is invalid
        ValidationError: If data doesn't match expected schema

    Example:
        >>> data = {"email": "user@example.com", "name": "John"}
        >>> result = process_user_data(123, data)
        >>> print(result.email)
        'user@example.com'

    Production Considerations:
        - Add rate limiting for API calls
        - Implement exponential backoff for retries
        - Monitor processing time and errors
        - Add circuit breaker for external dependencies
    """
    # Input validation
    if user_id <= 0:
        logger.error(f"Invalid user_id: {user_id}")
        raise ValueError("user_id must be positive")

    logger.info(f"Processing data for user {user_id}")

    # Retry logic with exponential backoff
    for attempt in range(retry_count):
        try:
            # Validate data structure
            user = UserData(user_id=user_id, **data)

            # Process the validated data
            # [Implementation details]

            logger.info(f"Successfully processed user {user_id}")
            return user

        except ValidationError as e:
            logger.error(f"Validation failed for user {user_id}: {e}")
            raise

        except requests.exceptions.RequestException as e:
            # Transient error - retry
            wait_time = 2 ** attempt  # Exponential backoff
            logger.warning(
                f"Request failed for user {user_id} (attempt {attempt + 1}/{retry_count}): {e}"
            )

            if attempt < retry_count - 1:
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"All retries exhausted for user {user_id}")
                return None

        except Exception as e:
            # Unexpected error - log and fail
            logger.exception(f"Unexpected error processing user {user_id}: {e}")
            return None

    return None
```

### 5. Usage Example

```python
if __name__ == "__main__":
    # Example 1: Basic usage
    user_data = {
        "email": "john.doe@example.com",
        "name": "John Doe"
    }

    result = process_user_data(user_id=123, data=user_data)
    if result:
        print(f"✓ User processed: {result.email}")
    else:
        print("✗ Failed to process user")

    # Example 2: Error handling
    try:
        invalid_data = {"email": "invalid-email"}
        process_user_data(user_id=456, data=invalid_data)
    except ValidationError as e:
        print(f"Validation error: {e}")

    # Example 3: Custom configuration
    result = process_user_data(
        user_id=789,
        data=user_data,
        timeout=60,  # Longer timeout
        retry_count=5  # More retries
    )
```

### 6. Expected Output

```python
# Expected output:
# INFO: Processing data for user 123
# INFO: Successfully processed user 123
# ✓ User processed: john.doe@example.com
# ERROR: Validation failed for user 456: Invalid email address
# Validation error: Invalid email address
# INFO: Processing data for user 789
# INFO: Successfully processed user 789
```

### 7. Detailed Explanation

```markdown
## How This Code Works

### 1. Input Validation
The function first validates the `user_id` parameter to ensure it's positive.
This prevents processing invalid data and provides clear error messages.

### 2. Retry Logic with Exponential Backoff
The code implements a retry mechanism for transient failures:
- Attempts the operation up to `retry_count` times
- Uses exponential backoff: waits 1s, 2s, 4s, 8s between retries
- Distinguishes between retryable and non-retryable errors

**Why this matters in production**:
- Network issues are often temporary
- Exponential backoff prevents overwhelming failing services
- Differentiating error types improves reliability

### 3. Comprehensive Error Handling
Three types of errors are handled differently:
- **ValidationError**: Data doesn't match schema (fail fast, don't retry)
- **RequestException**: Network/API errors (retry with backoff)
- **Unexpected errors**: Log and investigate (fail gracefully)

### 4. Logging Strategy
Structured logging at different levels:
- **INFO**: Normal operation progress
- **WARNING**: Retryable errors
- **ERROR**: Failures requiring attention
- **EXCEPTION**: Unexpected errors with stack traces

### 5. Type Safety
Uses type hints and Pydantic models:
- Catches errors at validation time, not runtime
- Provides IDE autocomplete and type checking
- Self-documenting code

## Alternative Approaches

### Approach 1: Async Implementation
For high-throughput scenarios, consider async/await:
```python
async def process_user_data_async(...) -> Optional[UserData]:
    # Use aiohttp instead of requests
    # Process multiple users concurrently
```

**Trade-offs**:
- ✓ Higher throughput
- ✓ Better resource utilization
- ✗ More complex code
- ✗ Requires async ecosystem

### Approach 2: Queue-Based Processing
For decoupled systems:
```python
def queue_user_processing(user_id: int, data: Dict) -> str:
    # Push to message queue (RabbitMQ, SQS, etc.)
    # Return job ID for tracking
```

**Trade-offs**:
- ✓ Decoupled components
- ✓ Handles traffic spikes
- ✓ Enables distributed processing
- ✗ Added infrastructure complexity
- ✗ Eventual consistency

### Approach 3: Circuit Breaker Pattern
For external service dependencies:
```python
from pybreaker import CircuitBreaker

breaker = CircuitBreaker(fail_max=5, timeout_duration=60)

@breaker
def process_user_data(...):
    # Automatically opens circuit after failures
    # Prevents cascade failures
```

**Trade-offs**:
- ✓ Protects against cascade failures
- ✓ Faster failure detection
- ✗ Additional dependency
- ✗ Requires monitoring

## Performance Considerations

### Time Complexity
- Best case: O(1) - Single successful processing
- Worst case: O(n) where n = retry_count
- Expected: O(1) for most cases

### Memory Usage
- Minimal memory footprint
- UserData model is lightweight
- No data accumulation

### Scalability
**Current implementation limits**:
- Synchronous processing: ~100 requests/second
- No connection pooling: Each request creates new connection
- No caching: Repeated lookups inefficient

**Improvements for scale**:
1. Add connection pooling: `requests.Session()`
2. Implement caching: Redis for frequently accessed data
3. Use async: Handle 1000+ requests/second
4. Add load balancing: Distribute across multiple workers

## Security Considerations

### Current Protections
1. **Input Validation**: Prevents injection attacks
2. **Type Safety**: Prevents type confusion vulnerabilities
3. **Error Handling**: Doesn't leak sensitive information
4. **Logging**: Sanitizes sensitive data before logging

### Additional Security Measures
For production deployment:

1. **Rate Limiting**:
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@limiter.limit("100/minute")
def process_user_data(...):
    ...
```

2. **Authentication**:
```python
def process_user_data(
    user_id: int,
    data: Dict,
    api_key: str  # Verify before processing
):
    verify_api_key(api_key)
    ...
```

3. **Data Encryption**:
```python
from cryptography.fernet import Fernet

def encrypt_sensitive_data(data: str) -> bytes:
    key = os.environ['ENCRYPTION_KEY']
    f = Fernet(key)
    return f.encrypt(data.encode())
```

## Common Issues and Solutions

### Issue 1: Timeout Errors
**Symptoms**: Requests fail with timeout after 30 seconds

**Cause**: Downstream service is slow or unresponsive

**Solution**:
```python
# Increase timeout for slow services
result = process_user_data(user_id=123, data=data, timeout=60)

# Or implement async processing
# Or add caching for repeated requests
```

### Issue 2: Memory Leaks with Large Data
**Symptoms**: Memory usage grows over time

**Cause**: Large data objects not garbage collected

**Solution**:
```python
# Use streaming for large data
def process_large_data(file_path: str):
    with open(file_path, 'r') as f:
        for line in f:  # Stream line by line
            process_line(line)
    # File handle closed, memory freed
```

### Issue 3: Retry Storm
**Symptoms**: Failing service overwhelmed with retries

**Cause**: Multiple clients retrying simultaneously

**Solution**:
```python
import random

# Add jitter to retry timing
wait_time = (2 ** attempt) + random.uniform(0, 1)
```

## Testing Strategy

### Unit Tests
```python
import pytest

def test_process_user_data_success():
    """Test successful user data processing."""
    data = {"email": "test@example.com"}
    result = process_user_data(123, data)

    assert result is not None
    assert result.user_id == 123
    assert result.email == "test@example.com"

def test_process_user_data_invalid_email():
    """Test validation catches invalid email."""
    data = {"email": "invalid"}

    with pytest.raises(ValidationError):
        process_user_data(123, data)

@pytest.mark.parametrize("user_id", [-1, 0])
def test_process_user_data_invalid_user_id(user_id):
    """Test validation catches invalid user IDs."""
    data = {"email": "test@example.com"}

    with pytest.raises(ValueError):
        process_user_data(user_id, data)
```

### Integration Tests
```python
def test_process_user_data_with_retries(mock_api):
    """Test retry logic with simulated failures."""
    # Simulate 2 failures then success
    mock_api.side_effect = [
        RequestException("Network error"),
        RequestException("Network error"),
        {"status": "success"}
    ]

    result = process_user_data(123, {"email": "test@example.com"})

    assert result is not None
    assert mock_api.call_count == 3
```

## Deployment Checklist

Before deploying this code to production:

- [ ] All tests pass
- [ ] Error handling covers expected failures
- [ ] Logging is comprehensive but not excessive
- [ ] Sensitive data is not logged
- [ ] Timeouts are configured appropriately
- [ ] Retry logic prevents retry storms
- [ ] Monitoring and alerting configured
- [ ] Load testing completed
- [ ] Security review completed
- [ ] Documentation updated
- [ ] Rollback plan prepared

## Further Reading

- [Python Best Practices](https://docs.python-guide.org/)
- [Error Handling Patterns](https://martinfowler.com/articles/replaceThrowWithNotification.html)
- [Production-Ready Python](https://www.oreilly.com/library/view/production-ready-python/9781492039211/)
- [Retry Strategies](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
```

---

## Quality Criteria

Generated code examples must meet these standards:

### Completeness (Required)
- [ ] All imports included and available
- [ ] No undefined variables or functions
- [ ] Complete function/class definitions
- [ ] Working usage examples provided
- [ ] Expected output documented

### Production Quality (Required)
- [ ] Comprehensive error handling
- [ ] Input validation present
- [ ] Logging statements included
- [ ] Type hints provided (Python 3.9+)
- [ ] Docstrings for all public functions/classes

### Security (Required)
- [ ] No hardcoded credentials or secrets
- [ ] Input validation prevents injection
- [ ] Error messages don't leak sensitive data
- [ ] Security considerations documented
- [ ] Dependencies are current and secure

### Educational Value (Required)
- [ ] Context comment explaining when/why to use
- [ ] Inline comments explain complex logic
- [ ] Detailed explanation section follows code
- [ ] Alternative approaches discussed
- [ ] Common issues and solutions documented

### Style (Required)
- [ ] Follows language best practices
  - Python: PEP 8
  - JavaScript: Airbnb Style Guide
  - Go: Effective Go
- [ ] Meaningful variable and function names
- [ ] Consistent formatting
- [ ] No code smells (long functions, deep nesting, etc.)

### Testing (Required)
- [ ] Code has been tested and works
- [ ] Unit test examples provided
- [ ] Test cases cover edge cases
- [ ] Integration test examples (if applicable)

### Documentation (Required)
- [ ] Performance considerations explained
- [ ] Security implications documented
- [ ] Troubleshooting section included
- [ ] Deployment checklist provided
- [ ] Further reading links included

---

## Example Request

```
Generate a production-quality code example for:

Topic: Database connection pooling
Language: Python
Complexity: Intermediate
Learning Objectives:
1. Understand why connection pooling is necessary
2. Implement connection pooling with SQLAlchemy
3. Handle connection failures gracefully
4. Monitor pool health

Context: Building a web API that makes frequent database queries
Constraints: Use SQLAlchemy 2.0+, PostgreSQL, include async support
```

---

## Example Output Validation

After generating code, verify:

1. **Run the code**: Does it execute without errors?
2. **Test edge cases**: What happens with invalid input?
3. **Check security**: Any vulnerabilities?
4. **Review documentation**: Is explanation clear and complete?
5. **Verify best practices**: Does it follow language conventions?
6. **Assess educational value**: Will learners understand why/how?

---

## Iteration Guidelines

If generated code doesn't meet standards:

### Common Issues and Fixes

**Issue**: Code is too simple / toy example
**Fix**: Add production concerns (error handling, logging, validation)

**Issue**: Missing context/explanation
**Fix**: Add comprehensive comments and explanation section

**Issue**: Incomplete error handling
**Fix**: Add try/except blocks with specific error types

**Issue**: No usage examples
**Fix**: Add 2-3 examples showing different use cases

**Issue**: Security vulnerabilities
**Fix**: Add input validation, remove hardcoded secrets

**Issue**: Missing type hints
**Fix**: Add type annotations for all parameters and returns

---

## Notes

- **Prefer real libraries**: Use actual production libraries, not mock implementations
- **Show trade-offs**: Discuss when to use this approach vs alternatives
- **Include metrics**: Show performance characteristics when relevant
- **Link to resources**: Provide further reading for deeper understanding
- **Keep examples focused**: One concept per example, don't try to show everything
