# Exercise [NUMBER]: [Exercise Title]

**Module**: [Module Number and Name]
**Difficulty**: [Beginner/Intermediate/Advanced]
**Estimated Time**: [X] minutes
**Prerequisites**:
- [Prerequisite 1]
- [Prerequisite 2]

---

## Learning Objectives

By completing this exercise, you will:

1. [Specific, measurable objective 1]
2. [Specific, measurable objective 2]
3. [Specific, measurable objective 3]
4. [Specific, measurable objective 4]

## Skills Practiced

- [Skill 1]
- [Skill 2]
- [Skill 3]
- [Skill 4]

---

## Scenario

[1-2 paragraphs providing realistic context for the exercise]

**Business Context**: [Why this matters in real-world scenarios]

**Technical Context**: [What technical challenges you'll address]

---

## Requirements

### Functional Requirements

1. [Requirement 1 with specific, measurable criteria]
2. [Requirement 2 with specific, measurable criteria]
3. [Requirement 3 with specific, measurable criteria]
4. [Requirement 4 with specific, measurable criteria]

### Non-Functional Requirements

- **Performance**: [Specific performance criteria]
- **Security**: [Security requirements]
- **Reliability**: [Reliability/availability requirements]
- **Maintainability**: [Code quality requirements]

---

## Setup

### Prerequisites Check

Before starting, ensure you have:

```bash
# Check Python version (should be 3.9+)
python --version

# Check [tool] is installed
[tool] --version

# Verify [dependency] is available
which [dependency]
```

### Initial Setup

1. **Create Project Directory**
   ```bash
   mkdir exercise-[number]-[name]
   cd exercise-[number]-[name]
   ```

2. **Set Up Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   # Create requirements.txt
   cat > requirements.txt << EOF
   [package1]==x.y.z
   [package2]==x.y.z
   [package3]==x.y.z
   EOF

   # Install
   pip install -r requirements.txt
   ```

4. **Download Required Files** (if applicable)
   ```bash
   # Download dataset or configuration files
   wget [url] -O [filename]
   ```

---

## Part 1: [First Component] (X minutes)

### Objective

[What you'll accomplish in this part]

### Instructions

#### Step 1: [Specific Task]

[Detailed instructions for this step]

```[language]
# Code template or starting point
[Code with TODOs or placeholders]
```

**What to do**:
1. [Specific action]
2. [Specific action]
3. [Specific action]

**Expected outcome**: [What should happen when done correctly]

---

#### Step 2: [Specific Task]

[Detailed instructions]

```[language]
# Code template
[Code]
```

**Hints**:
- 💡 [Hint 1]
- 💡 [Hint 2]

---

#### Step 3: [Specific Task]

[Continue pattern]

---

### Verification

Check your work:

```bash
# Run this command to verify
[verification command]

# Expected output:
# [What you should see]
```

**Success Criteria**:
- [ ] [Specific criterion 1]
- [ ] [Specific criterion 2]
- [ ] [Specific criterion 3]

---

## Part 2: [Second Component] (X minutes)

### Objective

[What you'll accomplish in this part]

### Instructions

#### Step 1: [Specific Task]

[Instructions]

```[language]
[Code template]
```

---

#### Step 2: [Specific Task]

[Instructions]

---

### Verification

```bash
[Verification command]
```

**Success Criteria**:
- [ ] [Criterion 1]
- [ ] [Criterion 2]

---

## Part 3: [Integration/Testing] (X minutes)

### Objective

[Test the complete implementation]

### Instructions

#### Step 1: [Integration Task]

[Instructions for putting it all together]

```[language]
[Integration code]
```

---

#### Step 2: [Testing]

**Unit Tests**:
```[language]
# test_[component].py
[Test code]
```

**Integration Tests**:
```[language]
# test_integration.py
[Test code]
```

**Run Tests**:
```bash
pytest tests/ -v
```

**Expected Results**:
```
test_[function1] PASSED
test_[function2] PASSED
test_[integration] PASSED
========================== 3 passed in 0.42s ==========================
```

---

### Verification

**Final Check**:
```bash
# Run the complete solution
[final command]

# Check output
[verification steps]
```

**Success Criteria**:
- [ ] All tests pass
- [ ] [Functional criterion 1]
- [ ] [Functional criterion 2]
- [ ] [Performance criterion]
- [ ] [Quality criterion]

---

## Extension Challenges (Optional)

For advanced practice, try these extensions:

### Challenge 1: [Extension Topic] (+20 minutes)

**Objective**: [What to extend]

**Instructions**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Success Criteria**:
- [ ] [Criterion]

---

### Challenge 2: [Extension Topic] (+30 minutes)

[Similar structure]

---

## Common Issues and Solutions

### Issue 1: [Common Problem]

**Symptoms**:
```
[Error message or behavior]
```

**Possible Causes**:
- [Cause 1]
- [Cause 2]

**Solution**:
```bash
# How to fix
[solution steps]
```

---

### Issue 2: [Common Problem]

[Repeat structure]

---

### Issue 3: [Common Problem]

[Repeat structure]

---

## Solution Verification

### Self-Assessment Checklist

Before considering the exercise complete, verify:

**Functionality**:
- [ ] All parts complete
- [ ] All tests pass
- [ ] Solution works as specified
- [ ] Edge cases handled

**Code Quality**:
- [ ] Code is readable and well-organized
- [ ] Functions have clear docstrings
- [ ] Variables have meaningful names
- [ ] No hardcoded values (use config/constants)
- [ ] Error handling implemented

**Best Practices**:
- [ ] Follows language conventions (PEP 8 for Python, etc.)
- [ ] No security vulnerabilities
- [ ] Efficient implementation
- [ ] Proper logging added
- [ ] Configuration externalized

**Documentation**:
- [ ] README.md created
- [ ] Code comments added where needed
- [ ] Usage examples included

---

## Expected Output

### Screenshots/Output Examples

**When running [command]**, you should see:
```
[Expected output]
```

**When checking [metric]**, you should have:
- [Metric 1]: [Expected value]
- [Metric 2]: [Expected value]

---

## Learning Checkpoints

After completing this exercise, you should be able to answer:

1. **[Concept Question]**: [Question testing understanding]
   <details>
   <summary>Answer</summary>
   [Answer explanation]
   </details>

2. **[Technical Question]**: [Question]
   <details>
   <summary>Answer</summary>
   [Answer]
   </details>

3. **[Application Question]**: [Question]
   <details>
   <summary>Answer</summary>
   [Answer]
   </details>

---

## Next Steps

### Continue Learning

1. **Deepen Understanding**:
   - Read: [Resource 1]
   - Watch: [Resource 2]
   - Try: [Resource 3]

2. **Practice More**:
   - Exercise [X+1]: [Next exercise]
   - Build: [Project suggestion]
   - Experiment: [Variation to try]

3. **Connect to Real-World**:
   - Read case study: [Company example]
   - Explore: [Production example]
   - Contribute: [Open source project]

---

## Additional Resources

### Documentation
- [Official docs link] - [What to read]
- [API reference link] - [Relevant sections]

### Tutorials
- [Tutorial link] - [What it covers]

### Examples
- [GitHub repo link] - [Example implementations]

### Community
- [Forum/chat link] - [Where to ask questions]

---

## Solution Reference

> **Note**: Try to complete the exercise without looking at the solution first!

A complete, documented solution is available in the solutions repository:

**Location**: `[solutions-repo-url]/exercises/exercise-[number]/`

**Files**:
- `solution.py` - Complete implementation
- `tests/` - Comprehensive test suite
- `README.md` - Detailed explanation
- `IMPLEMENTATION_GUIDE.md` - Step-by-step walkthrough

**How to use the solution**:
1. ✅ Try the exercise yourself first
2. ❌ Don't copy without understanding
3. 📖 Read the IMPLEMENTATION_GUIDE for detailed explanations
4. 🔬 Compare your approach with the solution
5. 🤔 Understand why certain approaches were chosen
6. 💡 Learn from differences

---

## Instructor Notes

> For instructors/mentors using this exercise

### Common Student Struggles

1. **[Common Issue]**: Students often struggle with [aspect]
   - **Hint to provide**: [Helpful hint without giving away answer]
   - **Teaching point**: This is an opportunity to discuss [concept]

2. **[Common Issue]**: [Description]
   - **Hint**: [Hint]
   - **Teaching point**: [Concept]

### Assessment Rubric

Use this rubric for grading:

| Criteria | Excellent (4) | Good (3) | Satisfactory (2) | Needs Work (1) |
|----------|---------------|----------|------------------|----------------|
| **Functionality** | All requirements met, handles edge cases | All requirements met | Most requirements met | Incomplete |
| **Code Quality** | Clean, well-organized, production-ready | Good structure, readable | Functional but messy | Poor quality |
| **Testing** | Comprehensive tests, >80% coverage | Good test coverage | Basic tests | Minimal/no tests |
| **Documentation** | Excellent docs and comments | Good documentation | Basic docs | Little/no docs |
| **Best Practices** | Exemplary practices | Follows best practices | Some practices | Ignores practices |

**Passing Score**: 10/20 points (Average of 2/4 in each category)
**Target Score**: 15/20 points (Average of 3/4 in each category)

### Time Management Tips

- Most students complete Part 1 in [X] minutes
- Part 2 typically takes [X] minutes
- If students are struggling with [part], suggest [tip]
- Extension challenges can be homework

### Discussion Points

After students complete the exercise, discuss:
1. [Discussion question 1]
2. [Discussion question 2]
3. [Discussion question 3]

---

## Version History

- **v1.0** - [Date] - Initial version
- **v1.1** - [Date] - [Changes made]

---

## Feedback

Help us improve this exercise:
- **Issues**: Report problems via [issue tracker link]
- **Suggestions**: Submit improvements via [contribution guide link]
- **Questions**: Ask in [discussion forum link]

---

**Exercise Template Version**: 1.0
**Success Rate**: [X]% of students complete successfully
**Average Time**: [X] minutes (based on [N] completions)
