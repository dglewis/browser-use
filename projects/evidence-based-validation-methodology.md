# Model Answer Comparison Framework for research_single_question.py

## Overview

This document outlines the methodology for extending our existing `research_single_question.py` script to systematically compare answers from different LLM models to the same question, automatically validate which answer is more accurate, and track efficiency metrics for these comparisons.

> **Note:** For details on the efficiency metrics tracking, see the [Model Comparison: Efficiency Metrics Framework](./evidence-based-validation-efficiency-metrics.md).

## Problem Statement

Our current process with `research_single_question.py` has several key limitations:

1. **Manual Comparison Process**: We run the script multiple times with different models and manually compare results, which is time-consuming and error-prone.

2. **No Systematic Comparison**: When models provide different answers (like the Claude 3.5 vs. Claude 3.7 comparison we just performed), we lack a structured approach to determine which is more accurate.

3. **Redundant Evidence Gathering**: Each model run repeats the same evidence gathering process, wasting computational resources and time.

4. **No Standardized Metrics**: We cannot easily compare efficiency metrics (time, tokens, API calls) between models for the same question.

5. **Subjective Assessment**: Without an automated, evidence-based approach to resolve contradictions, assessments may be influenced by subjective factors.

## Current Implementation Overview

Our existing `research_single_question.py` script:

1. Takes a single model name in the `SaviyntQuestionValidator` constructor
2. Uses browser automation to validate questions against Saviynt documentation
3. Returns validated question results for a single model run
4. Saves results to a model-specific JSON file

## Extension Goals

We need to extend this functionality to:

1. Process the same question with multiple models in a single run
2. Systematically compare the answers for accuracy 
3. Automatically resolve contradictions with evidence-based fact-checking
4. Track and report efficiency metrics for each model
5. Generate comprehensive comparison reports

## Explanation Quality Analysis

When comparing model responses, explanations often differ in style, length, and focus while reaching the same conclusion. Our framework must evaluate explanation quality, not just answer correctness.

### Explanation Quality Metrics
   
| Metric | Description | Measurement |
|--------|-------------|-------------|
| Conciseness | Economy of language while maintaining accuracy | Word/token count |
| Evidence incorporation | How effectively evidence is cited | Reference count & quality |
| Reasoning clarity | Logical flow from evidence to conclusion | Expert evaluation (1-5) |
| Technical precision | Accuracy in technical terminology | Error count |
   
### Example from Claude 3.5 vs 3.7 Comparison (Question 12)
   
In our testing with Question 12 about Saviynt's dynamic attributes for country lists, both models correctly identified that "Multiple select from SQL query" and "Single select from SQL query" are the valid options. However, Claude 3.7 provided a ~20% more concise explanation (122 words vs 152) while maintaining all key points. The 3.7 explanation used more straightforward language and included more specific technical details about the SQL implementation.

While both explanations were technically accurate, this difference in presentation quality is important for user experience and educational value. Our comparison framework should capture these nuances.

## Framework Architecture

### High-Level Components

```
ModelComparisonFramework
├── MultiModelOrchestrator
├── SharedEvidenceRepository
├── AnswerComparisonEngine
└── ComparisonReportGenerator
```

### Component Descriptions

#### MultiModelOrchestrator

Coordinates validation across multiple models:
- Manages multiple `SaviyntQuestionValidator` instances
- Ensures consistent prompting across models
- Optimizes evidence gathering and sharing

```python
class MultiModelOrchestrator:
    def __init__(self, models_config, question, shared_browser=None):
        # Initialize with configuration for multiple models
        
    async def initialize_validators(self):
        # Create validator instances for each model
        
    async def run_validations(self):
        # Execute validations with all configured models
        
    async def compare_results(self):
        # Analyze differences between model answers
```

#### SharedEvidenceRepository

Centralizes evidence collection to avoid redundancy:
- Gathers evidence once for a given question
- Makes evidence available to all model validations
- Tracks evidence provenance for reporting

```python
class SharedEvidenceRepository:
    def __init__(self, browser):
        # Initialize with browser instance
        
    async def gather_evidence(self, question, search_terms):
        # Collect evidence for the question
        
    def get_evidence_for_claim(self, claim):
        # Retrieve relevant evidence for a specific claim
        
    def get_all_evidence(self):
        # Retrieve all gathered evidence
```

#### AnswerComparisonEngine

Core validation engine that compares model answers:
- Extracts claims from each model's answer
- Identifies points of agreement and disagreement
- Validates claims against evidence
- Resolves contradictions with additional fact-checking

```python
class AnswerComparisonEngine:
    def __init__(self, evidence_repository):
        # Initialize with evidence repository
        
    def extract_claims(self, model_answers):
        # Extract claims from multiple model answers
        
    def identify_disagreements(self, model_claims):
        # Identify points of disagreement between models
        
    def validate_claims(self, claims, evidence):
        # Validate claims against evidence
        
    async def fact_check_disagreements(self, disagreements, browser):
        # Perform additional fact-checking for disagreements
```

#### ComparisonReportGenerator

Creates detailed comparison reports:
- Generates structured model comparison reports
- Includes accuracy assessments with evidence
- Incorporates efficiency metrics
- Provides clear recommendations

```python
class ComparisonReportGenerator:
    def __init__(self, model_results, comparison_results, metrics):
        # Initialize with results and metrics
        
    def generate_comparison_report(self):
        # Create comprehensive comparison report
        
    def generate_summary(self):
        # Create executive summary of findings
        
    def format_evidence_citations(self, evidence):
        # Format evidence citations for the report
```

## Implementation Strategy

### Phase 1: Extending Data Structures

1. **Define Model Configuration Format**
   - Create structure for specifying multiple models
   - Support model-specific parameters
   - Include configuration for fact-checking

2. **Design Comparison Results Format**
   - Define structure for comparing model answers
   - Include evidence mapping
   - Support disagreement resolution

### Phase 2: Core Functionality

3. **Create Evidence Repository**
   - Implement shared evidence gathering
   - Develop evidence indexing and retrieval
   - Add support for fact-check-specific evidence

4. **Build Model Orchestrator**
   - Implement multi-model validation coordination
   - Create browser instance sharing
   - Manage validation lifecycle

### Phase 3: Comparison Capabilities

5. **Develop Answer Comparison Engine**
   - Implement claim extraction
   - Create disagreement detection
   - Develop evidence-based resolution

6. **Create Report Generator**
   - Design comparison report format
   - Implement evidence citation system
   - Add recommendation generation

## Validation Process

### Setup Phase

1. **Load Question and Configuration**
   - Load question details
   - Configure models to compare
   - Set up shared resources

2. **Initialize Validators**
   - Create validator instances for each model
   - Share browser instance when possible
   - Initialize metrics tracking

### Execution Phase

3. **Evidence Gathering**
   - Gather evidence once for the question
   - Store in shared repository
   - Index for efficient retrieval

4. **Model Processing**
   - Process question with each model
   - Collect results and metrics
   - Track model-specific information

### Comparison Phase

5. **Result Analysis**
   - Extract key claims from each answer
   - Identify points of agreement and disagreement
   - Map claims to evidence

6. **Disagreement Resolution**
   - Identify contradictions between models
   - Perform additional fact-checking
   - Determine which model is more accurate

### Example Disagreement Resolution Process

Based on our Claude 3.5 vs Claude 3.7 comparison on Question 12:

1. **Claim Extraction**:
   - Both models claimed "Single select from SQL query" is valid
   - Model A (3.5) claimed "Multiple select from SQL query is not mentioned as an option"
   - Model B (3.7) claimed "Multiple select from SQL query is available as an option"

2. **Evidence Collection**:
   - Documentation explicitly refers to "SQL Enum type (Single Select from SQL Query and Multiple Select from SQL Query)"
   - Documentation includes implementation examples for SQL queries

3. **Automated Resolution**:
   - Evidence directly contradicts Model A's claim
   - Evidence directly supports Model B's claim
   - Resolution: Model B (3.7) is more accurate

### Reporting Phase

7. **Report Generation**
   - Create comprehensive comparison report
   - Include evidence for assessments
   - Incorporate efficiency metrics
   - Provide clear recommendation

## Output Format

### Model Comparison Report

```json
{
  "question": {
    "id": 12,
    "text": "What options are available to display country lists from a database?"
  },
  "models_compared": ["claude-3.5-sonnet", "claude-3.7-sonnet"],
  "evidence_summary": [
    {
      "source": "https://docs.saviyntcloud.com/bundle/EIC-Admin-v24x/page/Content/...",
      "section": "Defining Datasets",
      "content": "To ensure compatibility of the query with both single and multi-user requests..."
    }
  ],
  "model_results": {
    "claude-3.5-sonnet": {
      "answer": "To display country lists from a database in Saviynt, you can use...",
      "key_claims": [
        "Single select from SQL query is available",
        "Multiple select from SQL query is not mentioned as an option"
      ],
      "evidence_alignment": {
        "supported_claims": 1,
        "contradicted_claims": 1,
        "unsupported_claims": 0
      }
    },
    "claude-3.7-sonnet": {
      "answer": "In Saviynt, there are two main options for displaying country lists...",
      "key_claims": [
        "Single select from SQL query is available",
        "Multiple select from SQL query is available"
      ],
      "evidence_alignment": {
        "supported_claims": 2,
        "contradicted_claims": 0,
        "unsupported_claims": 0
      }
    }
  },
  "disagreements": [
    {
      "topic": "Multiple select from SQL query availability",
      "models": {
        "claude-3.5-sonnet": "Not mentioned as an available option",
        "claude-3.7-sonnet": "Available as an option"
      },
      "evidence": [
        {
          "source": "https://docs.saviyntcloud.com/bundle/EIC-Admin-v24x/page/Content/...",
          "content": "...ensure that the 'IN' keyword is used when defining the 'WHERE' condition for SQL Enum type (Single Select from SQL Query and Multiple Select from SQL Query) dynamic attributes."
        }
      ],
      "resolution": "claude-3.7-sonnet is correct, Multiple select from SQL query is explicitly mentioned in the documentation"
    }
  ],
  "explanation_quality": {
    "claude-3.5-sonnet": {
      "word_count": 152,
      "technical_precision": "High",
      "evidence_incorporation": "Referenced evidence but with less specific details",
      "reasoning_clarity": 4
    },
    "claude-3.7-sonnet": {
      "word_count": 122, 
      "technical_precision": "High",
      "evidence_incorporation": "Incorporated specific SQL implementation details",
      "reasoning_clarity": 5
    },
    "comparison": "Claude 3.7 provided a more concise (19.7% shorter) explanation with better technical detail integration"
  },
  "conclusion": {
    "more_accurate_model": "claude-3.7-sonnet",
    "reasoning": "Claude 3.7 correctly identified both Single select from SQL query and Multiple select from SQL query as available options, which is explicitly confirmed in the documentation. Claude 3.5 incorrectly claimed that Multiple select from SQL query is not mentioned as an option."
  }
}
```

## Real-World Implementation Challenges

Our testing with actual model comparisons has revealed several practical considerations:

### 1. Browser Automation Stability

- **Context Method Issues**: Our script encountered issues with methods like `get_current_page()` on browser contexts
- **Resource Management**: Browser instances and contexts must be properly created and closed to prevent memory leaks
- **Concurrent Sessions**: Running multiple browser sessions requires careful orchestration to avoid performance degradation

### 2. Model Parameter Standardization

- **Parameter Format Differences**: Different models require different parameter formats (e.g., Claude models use different parameter structures)
- **Warning Handling**: The script sometimes generates warnings about parameter usage (e.g., `max_tokens` being passed in `model_kwargs`)
- **Version Compatibility**: New model versions may introduce parameter changes requiring adaptations

### 3. File Path Management

- **Path Resolution Issues**: Questions file path resolution can fail if not properly configured
- **Output File Naming**: Consistent naming conventions for model-specific outputs are essential
- **Environment Differences**: Path handling needs to account for different execution environments

### Implementation Mitigations

1. **Browser Wrapper Class**:
   ```python
   class BrowserManager:
       async def create_shared_browser(self):
           # Create and configure a single browser instance
           
       async def get_page_for_model(self, model_name):
           # Create a new context and page for a specific model
           # Properly handle method availability differences
   ```

2. **Model Parameter Adapter**:
   ```python
   class ModelParameterAdapter:
       @staticmethod
       def adapt_parameters(model_name, common_params):
           # Convert common parameters to model-specific format
           # Handle special cases for different models
   ```

3. **Path Resolver**:
   ```python
   class PathResolver:
       @staticmethod
       def get_absolute_path(relative_path, default_dir="projects"):
           # Resolve paths consistently across environments
   ```

## Integration with Current System

This framework will integrate with our existing `research_single_question.py` script by:

1. **Preserving Core Functionality**:
   - Keep all current validation capabilities
   - Maintain compatibility with existing workflows
   - Support single-model operation for backward compatibility

2. **Extending the API**:
   - Add multi-model support
   - Include comparison functionality
   - Provide metrics tracking

3. **Enhancing Output**:
   - Generate model-specific outputs for compatibility
   - Add comparison reports as a new output type
   - Support metrics visualization

## Challenges & Mitigations

| Challenge | Mitigation Strategy |
|-----------|---------------------|
| Increased complexity | Modular design with clear interfaces |
| Browser resource usage | Share browser instances when possible |
| Subjective evaluations | Evidence-based assessment with clear criteria |
| Handling ambiguous documentation | Report uncertainty and alternative interpretations |
| Balancing detail vs. clarity | Layered reporting with summaries and details |
| Parameter inconsistencies | Model-specific parameter adapters |

## Next Steps

1. **Design Review**
   - Review methodology with the team
   - Refine component interfaces
   - Finalize output formats

2. **Prototype Development**
   - Build minimal implementation
   - Test with known question pairs
   - Validate comparison logic

3. **Evaluation Framework**
   - Develop test cases
   - Create benchmark questions
   - Establish quality metrics

## Conclusion

This Model Answer Comparison Framework will extend our existing `research_single_question.py` script to systematically compare responses from different models to the same question. By automating the comparison process that we currently perform manually, we'll gain objective, evidence-based insights into model performance, efficiency, and accuracy. 