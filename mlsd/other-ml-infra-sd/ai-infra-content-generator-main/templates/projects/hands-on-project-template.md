# Hands-On Project Template

> This template guides the creation of comprehensive hands-on projects for technical curriculum. Projects should provide real-world experience and portfolio-worthy outcomes.

---

## Project Metadata

**Project ID**: [Unique identifier, e.g., `project-001-ml-api`]
**Project Title**: [Clear, descriptive title]
**Module**: [Which module(s) this project relates to]
**Role/Level**: [Target role and experience level]
**Estimated Time**: [Time to complete, e.g., "8-12 hours"]
**Difficulty**: [Beginner / Intermediate / Advanced]
**Prerequisites**: [Required knowledge and completed modules]

**Technologies Used**:
- [Technology 1] ([Version])
- [Technology 2] ([Version])
- [Technology 3] ([Version])

**Skills Developed**:
- [Skill 1]
- [Skill 2]
- [Skill 3]

---

## Project Overview

### What You'll Build

[2-3 paragraphs describing what the learner will create. Be specific and exciting.]

**Example**:
```markdown
You'll build a production-ready machine learning API that serves predictions
for a sentiment analysis model. This API will handle thousands of requests per
second, include authentication, rate limiting, and comprehensive monitoring.

By the end of this project, you'll have a portfolio-worthy application that
demonstrates your ability to deploy ML models to production, handle real-world
scale, and follow industry best practices for API design and operation.

This project simulates what you'd build at companies like Airbnb, Uber, or
Netflix when deploying ML models to serve customer-facing features.
```

### Learning Objectives

By completing this project, you will be able to:

1. [Objective 1 - Active verb + specific skill]
2. [Objective 2 - Active verb + specific skill]
3. [Objective 3 - Active verb + specific skill]
4. [Objective 4 - Active verb + specific skill]
5. [Objective 5 - Active verb + specific skill]
6. [Objective 6 - Active verb + specific skill]
7. [Objective 7 - Active verb + specific skill]
8. [Objective 8 - Active verb + specific skill]

**Example**:
```markdown
1. Design and implement RESTful APIs following industry standards
2. Deploy machine learning models as scalable microservices
3. Implement authentication and authorization for API security
4. Add rate limiting to prevent abuse and ensure fair usage
5. Set up comprehensive monitoring and alerting
6. Write production-quality tests (unit, integration, load)
7. Create clear API documentation using OpenAPI/Swagger
8. Deploy to cloud infrastructure using containers
```

### Why This Project Matters

[2-3 paragraphs explaining the real-world relevance]

**Industry Context**:
- [How this skill is used in production]
- [Companies/scenarios where this is needed]
- [Career value of this skill]

**Example**:
```markdown
Every ML model needs to be deployed to production to deliver business value.
Companies spend $10B+ annually on ML model deployment and serving infrastructure.
The ability to take a model from Jupyter notebook to production API is one of
the most in-demand skills for ML engineers and data scientists.

According to Gartner, 85% of ML projects fail to reach production due to
deployment challenges. This project teaches you the skills to be part of the
15% who successfully deploy models. You'll learn patterns used at companies
like Google, Amazon, and Microsoft to serve billions of predictions per day.

This project directly prepares you for common interview questions and take-home
assignments for ML Engineering and MLOps roles. Many companies use similar
projects to assess candidates' production engineering skills.
```

---

## Project Architecture

### System Overview

[High-level description of the system architecture]

```
[Include ASCII diagram or describe architecture in text]

Example:
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Client    │─────▶│   API Layer  │─────▶│   ML Model  │
│   (HTTP)    │      │  (FastAPI)   │      │  (Pytorch)  │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   Database   │
                     │  (PostgreSQL)│
                     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  Monitoring  │
                     │ (Prometheus) │
                     └──────────────┘
```

### Components

**Component 1: [Name]**
- **Purpose**: [What it does]
- **Technology**: [What it's built with]
- **Key Features**: [Notable capabilities]
- **Interactions**: [How it connects to other components]

**Component 2: [Name]**
- **Purpose**: [What it does]
- **Technology**: [What it's built with]
- **Key Features**: [Notable capabilities]
- **Interactions**: [How it connects to other components]

[Repeat for all major components]

### Data Flow

1. [Step 1]: [What happens]
2. [Step 2]: [What happens]
3. [Step 3]: [What happens]
4. [Step 4]: [What happens]

**Example**:
```markdown
1. Client sends HTTP POST request to `/predict` endpoint with JSON payload
2. API layer validates request, checks authentication, enforces rate limits
3. Request is forwarded to ML model service for inference
4. Model returns prediction, API logs metrics to monitoring system
5. Response is formatted and returned to client with appropriate HTTP status
```

---

## Project Structure

### Directory Layout

```
project-name/
├── README.md                 # Project documentation
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container definition
├── docker-compose.yml       # Multi-container orchestration
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore rules
├── Makefile                # Common commands
│
├── src/                    # Source code
│   ├── __init__.py
│   ├── api/               # API layer
│   │   ├── __init__.py
│   │   ├── main.py        # FastAPI application
│   │   ├── routes/        # API endpoints
│   │   ├── middleware/    # Auth, rate limiting, etc.
│   │   └── schemas/       # Request/response models
│   │
│   ├── models/            # ML model code
│   │   ├── __init__.py
│   │   ├── model.py       # Model loading and inference
│   │   └── preprocessing.py
│   │
│   ├── database/          # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   └── repositories.py
│   │
│   ├── monitoring/        # Observability
│   │   ├── __init__.py
│   │   ├── metrics.py
│   │   └── logging.py
│   │
│   └── config/            # Configuration
│       ├── __init__.py
│       └── settings.py
│
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── load/             # Load tests
│
├── models/                # Trained model artifacts
│   └── sentiment_model.pkl
│
├── data/                  # Data files
│   ├── sample_data.json
│   └── test_data.json
│
├── docs/                  # Documentation
│   ├── API.md            # API documentation
│   ├── DEPLOYMENT.md     # Deployment guide
│   └── ARCHITECTURE.md   # Architecture details
│
└── scripts/               # Utility scripts
    ├── setup.sh          # Environment setup
    ├── train_model.py    # Model training
    └── load_test.py      # Load testing
```

---

## Prerequisites

### Required Knowledge

Before starting this project, you should be comfortable with:

**Technical Skills**:
- [ ] [Skill 1] - [Where to learn if needed]
- [ ] [Skill 2] - [Where to learn if needed]
- [ ] [Skill 3] - [Where to learn if needed]

**Completed Modules**:
- [ ] [Module 1] - [Why it's needed]
- [ ] [Module 2] - [Why it's needed]

**Example**:
```markdown
Technical Skills:
- [ ] Python 3.9+ programming - If needed: Complete Module 1
- [ ] REST API concepts - If needed: Review Module 7
- [ ] Basic Docker knowledge - If needed: Complete Module 5
- [ ] Git version control - If needed: Review Module 3

Completed Modules:
- [ ] Module 4: Machine Learning Basics - Needed for model concepts
- [ ] Module 5: Docker Containers - Needed for containerization
- [ ] Module 7: APIs & Web Services - Needed for API design
```

### Development Environment

**Required Software**:
- [ ] Python 3.9 or higher
- [ ] Docker Desktop 4.0+
- [ ] Git 2.30+
- [ ] Code editor (VS Code recommended)
- [ ] Postman or curl (for API testing)

**Optional but Recommended**:
- [ ] Docker Compose 2.0+
- [ ] Make (for automation)
- [ ] PostgreSQL client

**System Requirements**:
- 8GB RAM minimum (16GB recommended)
- 10GB free disk space
- Internet connection for downloads

---

## Part 1: Environment Setup

### Step 1: Clone and Setup

**Objective**: Set up your development environment

```bash
# Clone the starter repository
git clone https://github.com/[org]/[project-name].git
cd [project-name]

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Run setup script
./scripts/setup.sh
```

**Verify Setup**:
```bash
# Check Python version
python --version  # Should show 3.9+

# Verify installations
docker --version
docker-compose --version

# Run basic tests
pytest tests/unit/
```

**Expected Output**:
```
Python 3.9.7
Docker version 20.10.17
docker-compose version 2.6.1
==================== 15 passed in 2.34s ====================
```

**Troubleshooting**:

If you encounter issues:
- **Python version error**: Install Python 3.9+ from python.org
- **Docker not found**: Install Docker Desktop
- **Permission errors**: Run with appropriate permissions
- **Module not found**: Reinstall requirements: `pip install -r requirements.txt`

---

## Part 2: Core Implementation

### Phase 1: Build the ML Model Service

**Objective**: Create a service that loads and serves predictions from an ML model

**Time Estimate**: 2-3 hours

#### Task 1.1: Model Loading

Create `src/models/model.py`:

```python
"""
ML Model Service

This module handles loading the trained model and making predictions.
Key concepts:
- Lazy loading for performance
- Input validation
- Error handling
- Logging for debugging
"""

import pickle
from typing import List, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SentimentModel:
    """
    Sentiment analysis model service.

    This class demonstrates production patterns for ML model serving:
    - Singleton pattern for model loading
    - Input validation
    - Graceful error handling
    - Structured logging
    """

    def __init__(self, model_path: str):
        """
        Initialize model service.

        Args:
            model_path: Path to serialized model file

        Raises:
            FileNotFoundError: If model file doesn't exist
            ValueError: If model file is invalid
        """
        self.model_path = Path(model_path)
        self._model = None
        self._load_model()

    def _load_model(self):
        """Load the trained model from disk."""
        # Implementation here
        # [Students will implement this]
        pass

    def predict(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Make predictions for a batch of texts.

        Args:
            texts: List of text strings to analyze

        Returns:
            List of predictions with sentiment and confidence

        Raises:
            ValueError: If input is invalid

        Example:
            >>> model = SentimentModel("models/sentiment.pkl")
            >>> results = model.predict(["I love this!", "This is terrible"])
            >>> results[0]["sentiment"]
            'positive'
        """
        # Implementation here
        # [Students will implement this]
        pass
```

**Your Task**:

Implement the following methods:

1. `_load_model()`:
   - Check if model file exists
   - Load model using pickle
   - Log success/failure
   - Handle exceptions gracefully

2. `predict()`:
   - Validate inputs (not empty, correct type)
   - Preprocess texts
   - Get model predictions
   - Format results
   - Return structured predictions

**Success Criteria**:
- [ ] Model loads successfully on initialization
- [ ] Predictions return correct format
- [ ] Invalid inputs raise appropriate errors
- [ ] Errors are logged with context
- [ ] Tests pass: `pytest tests/unit/test_model.py`

**Hints**:
- Use `try/except` for file operations
- Log at INFO level for success, ERROR for failures
- Return predictions as list of dicts with keys: `sentiment`, `confidence`, `text`
- Use `isinstance()` for type checking

---

### Phase 2: Build the API Layer

**Objective**: Create a REST API that exposes the model

**Time Estimate**: 3-4 hours

#### Task 2.1: Create FastAPI Application

Create `src/api/main.py`:

```python
"""
FastAPI Application

Production-ready API with:
- OpenAPI documentation
- Request validation
- Error handling
- CORS support
- Health checks
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List
import logging

from src.models.model import SentimentModel
from src.monitoring.metrics import track_prediction

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sentiment Analysis API",
    description="Production ML API for sentiment prediction",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize model (singleton pattern)
model = None


@app.on_event("startup")
async def startup_event():
    """Load model on application startup."""
    # Implementation here
    # [Students will implement this]
    pass


class PredictionRequest(BaseModel):
    """
    Request schema for predictions.

    Validates input data structure and types.
    """
    texts: List[str] = Field(
        ...,
        description="List of texts to analyze",
        min_items=1,
        max_items=100  # Batch size limit
    )

    @validator('texts')
    def validate_texts(cls, v):
        """Validate text inputs."""
        # Implementation here
        # [Students will implement this]
        pass


class PredictionResponse(BaseModel):
    """
    Response schema for predictions.

    Provides type-safe response structure.
    """
    predictions: List[Dict[str, Any]]
    count: int
    model_version: str


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns service health status.
    """
    # Implementation here
    # [Students will implement this]
    pass


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Prediction endpoint.

    Make sentiment predictions for provided texts.
    """
    # Implementation here
    # [Students will implement this]
    pass
```

**Your Task**:

Implement the following endpoints:

1. `startup_event()`:
   - Load the sentiment model
   - Store in global variable
   - Log startup status

2. `validate_texts()`:
   - Check each text is non-empty
   - Check max length (<10,000 chars)
   - Raise ValueError if invalid

3. `health_check()`:
   - Return status: "healthy"
   - Include model loaded status
   - Return timestamp

4. `predict()`:
   - Validate request
   - Call model.predict()
   - Track metrics
   - Return formatted response
   - Handle errors with appropriate HTTP status

**Success Criteria**:
- [ ] API starts successfully: `uvicorn src.api.main:app`
- [ ] Health endpoint returns 200 OK
- [ ] Predict endpoint accepts valid requests
- [ ] Invalid requests return 400 with clear error message
- [ ] API documentation accessible at `/docs`
- [ ] Tests pass: `pytest tests/integration/test_api.py`

**Testing Your API**:

```bash
# Start the API
uvicorn src.api.main:app --reload

# Test health endpoint
curl http://localhost:8000/health

# Test prediction endpoint
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"texts": ["I love this!", "This is bad"]}'
```

---

### Phase 3: Add Authentication & Rate Limiting

**Objective**: Secure your API and prevent abuse

**Time Estimate**: 2 hours

[Continue with detailed implementation instructions...]

---

### Phase 4: Implement Monitoring

**Objective**: Add observability to track performance and issues

**Time Estimate**: 2 hours

[Continue with detailed implementation instructions...]

---

### Phase 5: Containerization

**Objective**: Package application as Docker container

**Time Estimate**: 1 hour

[Continue with detailed implementation instructions...]

---

## Part 3: Testing

### Unit Tests

[Detailed testing instructions]

### Integration Tests

[Detailed testing instructions]

### Load Tests

[Detailed testing instructions]

---

## Part 4: Deployment

### Local Deployment

[Deployment instructions]

### Cloud Deployment (Optional)

[Cloud deployment instructions]

---

## Part 5: Documentation

### Create API Documentation

[Documentation requirements]

### Write Deployment Guide

[Guide requirements]

---

## Validation Checklist

Before submitting your project, verify:

### Functionality
- [ ] All endpoints work correctly
- [ ] Error handling is comprehensive
- [ ] Edge cases are handled

### Code Quality
- [ ] Code follows style guidelines
- [ ] No security vulnerabilities
- [ ] Environment variables used for config
- [ ] Logging is comprehensive

### Testing
- [ ] Unit tests pass (>80% coverage)
- [ ] Integration tests pass
- [ ] Load tests meet requirements (100 req/sec)

### Documentation
- [ ] README.md is complete
- [ ] API documentation generated
- [ ] Code has docstrings
- [ ] Deployment guide written

### Production Readiness
- [ ] Dockerized successfully
- [ ] Environment-agnostic
- [ ] Monitoring in place
- [ ] Rate limiting works

---

## Extension Challenges

Want to go further? Try these advanced challenges:

### Challenge 1: Advanced Monitoring
- Add Prometheus metrics
- Create Grafana dashboard
- Set up alerting

### Challenge 2: CI/CD Pipeline
- Create GitHub Actions workflow
- Automate testing
- Deploy on merge to main

### Challenge 3: Performance Optimization
- Add Redis caching
- Implement async processing
- Optimize model inference

### Challenge 4: Enhanced Security
- Add JWT authentication
- Implement API key rotation
- Add request signing

---

## Assessment Rubric

Your project will be evaluated on:

| Category | Weight | Criteria |
|----------|--------|----------|
| Functionality | 30% | All features work correctly |
| Code Quality | 25% | Clean, maintainable code |
| Testing | 20% | Comprehensive test coverage |
| Documentation | 15% | Clear, complete documentation |
| Production Readiness | 10% | Follows best practices |

**Grading Scale**:
- **90-100% (A)**: Exceeds requirements, production-ready
- **80-89% (B)**: Meets all requirements
- **70-79% (C)**: Meets most requirements
- **60-69% (D)**: Missing key requirements
- **Below 60% (F)**: Incomplete or non-functional

---

## Submission Guidelines

### What to Submit

1. **Source Code** (GitHub repository link)
2. **Documentation** (README.md, API docs)
3. **Demo Video** (5-10 minutes showing features)
4. **Reflection** (1-2 pages on what you learned)

### Submission Checklist

- [ ] Code pushed to GitHub
- [ ] README.md is complete
- [ ] All tests pass
- [ ] Docker build succeeds
- [ ] Demo video uploaded
- [ ] Reflection written

---

## Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Documentation](https://docs.docker.com/)
- [Pytest Documentation](https://docs.pytest.org/)

### Tutorials
- [Building Production APIs](link)
- [Docker for ML](link)
- [API Security Best Practices](link)

### Example Projects
- [Sample Implementation](link)
- [Advanced Version](link)

---

## Getting Help

### Common Issues
See TROUBLESHOOTING.md for solutions to common problems

### Support Channels
- **Discussion Forum**: [Link]
- **Office Hours**: [Schedule]
- **Email**: [Contact]

### FAQ

**Q: How long should this take?**
A: 8-12 hours for core requirements, 15-20 hours with extensions

**Q: Can I use different technologies?**
A: Check with instructor first, but generally yes if justified

**Q: What if I get stuck?**
A: Post in discussion forum, attend office hours, or email instructor

---

**Good luck! This project will be a great addition to your portfolio.**
