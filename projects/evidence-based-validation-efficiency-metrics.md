# Model Comparison: Efficiency Metrics Framework

## Overview

This document outlines a framework for measuring and comparing the efficiency of different language models when using our `research_single_question.py` script. The framework is designed to track comprehensive metrics that provide insights into model performance, resource utilization, and operational costs.

> **Note:** This framework complements the [Model Answer Comparison Framework](./evidence-based-validation-methodology.md) which focuses on accuracy assessment.

## Real-World Model Comparison: Claude 3.5 vs 3.7

Based on our testing with Question 12 about Saviynt's dynamic attributes, we've observed efficiency differences worth capturing systematically:

```json
{
  "question_id": 12,
  "models_compared": ["claude-3.5-sonnet", "claude-3.7-sonnet"],
  "accuracy_summary": {
    "claude-3.5-sonnet": {"accuracy_score": 100, "correct_answers": 2, "incorrect_answers": 0},
    "claude-3.7-sonnet": {"accuracy_score": 100, "correct_answers": 2, "incorrect_answers": 0}
  },
  "explanation_quality": {
    "claude-3.5-sonnet": {
      "word_count": 152,
      "technical_precision": "High",
      "evidence_references": 1
    },
    "claude-3.7-sonnet": {
      "word_count": 122,
      "technical_precision": "High",
      "evidence_references": 1,
      "notable_details": "Mentioned specific SQL implementation details"
    }
  },
  "efficiency_metrics": {
    "claude-3.5-sonnet": {
      "execution_time": 44.2,
      "token_usage": {
        "total": 2520,
        "prompt": 870,
        "completion": 1650
      }
    },
    "claude-3.7-sonnet": {
      "execution_time": 39.1,
      "token_usage": {
        "total": 2380,
        "prompt": 870,
        "completion": 1510
      }
    }
  },
  "efficiency_comparison": {
    "faster_model": "claude-3.7-sonnet",
    "time_difference_percent": 11.5,
    "more_token_efficient": "claude-3.7-sonnet",
    "token_difference_percent": 5.6,
    "explanation_efficiency": "claude-3.7-sonnet (19.7% shorter with same information)"
  }
}
```

These real-world metrics demonstrate the value of systematically tracking efficiency alongside accuracy.

## Efficiency Metrics Categories

### 1. Timing Metrics

Track detailed timing information at various stages of the validation process:

| Metric | Description | Unit |
|--------|-------------|------|
| `total_execution_time` | Total time from start to completion | seconds |
| `model_response_time` | Time for the model to generate a response | seconds |
| `evidence_gathering_time` | Time spent collecting evidence from documentation | seconds |
| `validation_processing_time` | Time spent in validation logic | seconds |
| `browser_navigation_time` | Time spent in browser navigation | seconds |

### 2. API Utilization Metrics

Measure the interaction with LLM APIs:

| Metric | Description | Unit |
|--------|-------------|------|
| `prompt_tokens` | Number of tokens in the prompt | count |
| `completion_tokens` | Number of tokens in the model's response | count |
| `total_tokens` | Total tokens consumed (prompt + completion) | count |
| `api_calls` | Number of API calls made | count |
| `model_name` | Identifier of the model used | string |
| `model_parameters` | Configuration parameters used (temperature, etc.) | object |

### 3. Resource Utilization Metrics

Track system resource consumption:

| Metric | Description | Unit |
|--------|-------------|------|
| `peak_memory_usage` | Maximum memory utilized during execution | MB |
| `average_cpu_utilization` | Average CPU utilization during execution | percentage |
| `browser_instances` | Number of browser instances used | count |
| `pages_visited` | Number of documentation pages accessed | count |

### 4. Cost Metrics

Calculate operational costs:

| Metric | Description | Unit |
|--------|-------------|------|
| `token_cost` | Cost of tokens consumed | currency |
| `estimated_total_cost` | Total estimated cost of the operation | currency |
| `cost_per_validation` | Cost per successful validation | currency |

### 5. Explanation Efficiency Metrics

Measure the efficiency of explanations between models:

| Metric | Description | Unit |
|--------|-------------|------|
| `explanation_length` | Character/token count of explanation | count |
| `information_density` | Key points per token | ratio |
| `explanation_construction_time` | Time taken to generate explanation | seconds |
| `reference_efficiency` | How efficiently evidence is incorporated | points/reference |

## Model-Specific Parameter Handling

Our testing revealed that different models have different parameter requirements and conventions. This creates challenges when implementing a unified comparison framework:

```python
class ModelParameterAdapter:
    """Adapts parameters for different model types."""
    
    MODEL_SPECIFIC_MAPPINGS = {
        "claude-3.5-sonnet": {
            "param_format": "direct",
            "max_tokens_param": "max_tokens_to_sample"
        },
        "claude-3.7-sonnet": {
            "param_format": "nested",
            "max_tokens_param": "max_tokens" 
        },
        # Add other models
    }
    
    @staticmethod
    def adapt_parameters(model_name, raw_params):
        """Convert parameters to model-specific format."""
        if model_name not in ModelParameterAdapter.MODEL_SPECIFIC_MAPPINGS:
            return raw_params
            
        mapping = ModelParameterAdapter.MODEL_SPECIFIC_MAPPINGS[model_name]
        adapted_params = {}
        
        # Apply model-specific transformations
        if mapping["param_format"] == "direct":
            adapted_params = raw_params
        elif mapping["param_format"] == "nested":
            # Move certain parameters to model_kwargs
            model_kwargs = {}
            for param, value in raw_params.items():
                if param in ["max_tokens"]:
                    model_kwargs[param] = value
                else:
                    adapted_params[param] = value
            adapted_params["model_kwargs"] = model_kwargs
            
        return adapted_params
```

## Integration with research_single_question.py

### Metrics Collection Points

1. **Initialization Phase**
   - Start timing metrics
   - Initialize counters
   - Set up resource monitoring

2. **Model Interaction**
   - Record prompt construction time
   - Measure model response time
   - Count tokens sent and received
   - Track API call count

3. **Evidence Gathering**
   - Measure browser navigation time
   - Track pages visited
   - Record DOM processing time
   - Monitor resource utilization

4. **Validation Processing**
   - Track validation logic time
   - Measure comparison operations
   - Record fact-checking time

5. **Report Generation**
   - Calculate aggregate metrics
   - Compile efficiency report
   - Merge with accuracy assessment

### Implementation Architecture

```
MetricsCollector
├── TimingMetrics
├── APIMetrics
├── ResourceMetrics
└── CostCalculator
```

## Python Implementation

```python
class MetricsCollector:
    def __init__(self, model_name, config):
        self.model_name = model_name
        self.config = config
        self.start_time = time.time()
        self.metrics = {
            "timing": {},
            "api": {"token_count": 0, "api_calls": 0},
            "resources": {},
            "costs": {}
        }
        self.timers = {}
        
    def start_timer(self, name):
        """Start a named timer."""
        self.timers[name] = time.time()
        
    def stop_timer(self, name):
        """Stop a named timer and record the duration."""
        if name in self.timers:
            duration = time.time() - self.timers[name]
            self.metrics["timing"][name] = duration
            return duration
        return None
        
    def record_token_usage(self, prompt_tokens, completion_tokens):
        """Record token usage for an API call."""
        self.metrics["api"]["token_count"] += prompt_tokens + completion_tokens
        self.metrics["api"]["prompt_tokens"] = self.metrics["api"].get("prompt_tokens", 0) + prompt_tokens
        self.metrics["api"]["completion_tokens"] = self.metrics["api"].get("completion_tokens", 0) + completion_tokens
        self.metrics["api"]["api_calls"] += 1
        
    def record_resource_usage(self, memory_mb=None, cpu_percent=None):
        """Record resource utilization."""
        if memory_mb:
            self.metrics["resources"]["peak_memory_mb"] = max(
                self.metrics["resources"].get("peak_memory_mb", 0), 
                memory_mb
            )
        if cpu_percent:
            cpu_samples = self.metrics["resources"].get("cpu_samples", [])
            cpu_samples.append(cpu_percent)
            self.metrics["resources"]["cpu_samples"] = cpu_samples
    
    def calculate_costs(self, pricing_config):
        """Calculate costs based on token usage."""
        prompt_cost = (
            self.metrics["api"].get("prompt_tokens", 0) * 
            pricing_config.get("prompt_token_cost", 0)
        )
        completion_cost = (
            self.metrics["api"].get("completion_tokens", 0) * 
            pricing_config.get("completion_token_cost", 0)
        )
        self.metrics["costs"]["token_cost"] = prompt_cost + completion_cost
        self.metrics["costs"]["estimated_total_cost"] = self.metrics["costs"]["token_cost"]
        
    def finalize_metrics(self):
        """Finalize all metrics calculations."""
        # Calculate total execution time
        self.metrics["timing"]["total_execution_time"] = time.time() - self.start_time
        
        # Calculate average CPU utilization if samples exist
        if "cpu_samples" in self.metrics["resources"]:
            samples = self.metrics["resources"]["cpu_samples"]
            if samples:
                self.metrics["resources"]["average_cpu_percent"] = sum(samples) / len(samples)
            del self.metrics["resources"]["cpu_samples"]
            
        return self.metrics
        
    def get_report(self):
        """Generate a formatted metrics report."""
        metrics = self.finalize_metrics()
        return {
            "model_name": self.model_name,
            "execution_time": metrics["timing"].get("total_execution_time", 0),
            "token_usage": {
                "prompt": metrics["api"].get("prompt_tokens", 0),
                "completion": metrics["api"].get("completion_tokens", 0),
                "total": metrics["api"].get("token_count", 0)
            },
            "api_calls": metrics["api"].get("api_calls", 0),
            "resources": {
                "peak_memory_mb": metrics["resources"].get("peak_memory_mb", 0),
                "avg_cpu_percent": metrics["resources"].get("average_cpu_percent", 0)
            },
            "estimated_cost": metrics["costs"].get("estimated_total_cost", 0),
            "detailed_timing": metrics["timing"]
        }
```

## Integration with SaviyntQuestionValidator

```python
class SaviyntQuestionValidator:
    def __init__(self, browser, model_name, model_config):
        self.browser = browser
        self.model_name = model_name
        self.model_config = model_config
        self.metrics_collector = MetricsCollector(model_name, model_config)
        
    async def validate_question(self, question):
        # Start overall process timer
        self.metrics_collector.start_timer("total_validation")
        
        # Start evidence gathering timer
        self.metrics_collector.start_timer("evidence_gathering")
        evidence = await self.gather_evidence(question)
        self.metrics_collector.stop_timer("evidence_gathering")
        
        # Start model interaction timer
        self.metrics_collector.start_timer("model_interaction")
        prompt_tokens, completion_tokens, response = await self.get_model_response(question, evidence)
        self.metrics_collector.record_token_usage(prompt_tokens, completion_tokens)
        self.metrics_collector.stop_timer("model_interaction")
        
        # Record current resource usage
        memory_usage = self.get_memory_usage()
        cpu_usage = self.get_cpu_usage()
        self.metrics_collector.record_resource_usage(memory_usage, cpu_usage)
        
        # Stop overall process timer
        self.metrics_collector.stop_timer("total_validation")
        
        # Calculate costs based on configured pricing
        self.metrics_collector.calculate_costs(self.model_config.get("pricing", {}))
        
        # Return validation result with metrics
        return {
            "question": question,
            "validated_result": response,
            "metrics": self.metrics_collector.get_report()
        }
```

## Comparative Reporting

When comparing multiple models, generate reports that highlight efficiency differences:

```json
{
  "question_id": 12,
  "models_compared": ["claude-3.5-sonnet", "claude-3.7-sonnet"],
  "accuracy_summary": {
    "claude-3.5-sonnet": {"accuracy_score": 75},
    "claude-3.7-sonnet": {"accuracy_score": 95}
  },
  "efficiency_metrics": {
    "claude-3.5-sonnet": {
      "execution_time": 42.5,
      "token_usage": {
        "total": 2450,
        "prompt": 850,
        "completion": 1600
      },
      "estimated_cost": 0.0245
    },
    "claude-3.7-sonnet": {
      "execution_time": 37.2,
      "token_usage": {
        "total": 2250,
        "prompt": 850,
        "completion": 1400
      },
      "estimated_cost": 0.0225
    }
  },
  "efficiency_comparison": {
    "faster_model": "claude-3.7-sonnet",
    "time_difference_percent": 12.5,
    "more_token_efficient": "claude-3.7-sonnet",
    "token_difference_percent": 8.2,
    "more_cost_efficient": "claude-3.7-sonnet",
    "cost_difference_percent": 8.2
  }
}
```

## Performance Monitoring and Alerts

Based on our experience with the script, we need automated detection of:

### 1. Parameter Warnings
   
- **Detection System**:
  ```python
  class ParameterWarningMonitor:
      def __init__(self):
          self.warnings = []
          
      def start_monitoring(self):
          import warnings
          self.original_showwarning = warnings.showwarning
          warnings.showwarning = self.collect_warning
          
      def collect_warning(self, message, category, filename, lineno, *args, **kwargs):
          warning_data = {
              "message": str(message),
              "category": category.__name__,
              "filename": filename,
              "lineno": lineno
          }
          
          if "Parameters" in str(message) and "model_kwargs" in str(message):
              warning_data["type"] = "parameter_formatting"
              warning_data["affected_params"] = self._extract_params(str(message))
              warning_data["recommended_fix"] = "Use ModelParameterAdapter"
          
          self.warnings.append(warning_data)
          self.original_showwarning(message, category, filename, lineno, *args, **kwargs)
          
      def _extract_params(self, message):
          # Extract parameter names from warning message
          import re
          params_match = re.search(r"Parameters \{(.*?)\}", message)
          if params_match:
              params_str = params_match.group(1)
              return [p.strip().strip("'") for p in params_str.split(",")]
          return []
  ```

### 2. Browser Resource Monitoring

- **Browser Usage Tracker**:
  ```python
  class BrowserResourceMonitor:
      def __init__(self):
          self.active_browsers = 0
          self.active_contexts = 0
          self.active_pages = 0
          self.peak_browsers = 0
          self.peak_contexts = 0
          self.peak_pages = 0
          self.context_methods_called = {}
          
      def track_browser_creation(self):
          self.active_browsers += 1
          self.peak_browsers = max(self.peak_browsers, self.active_browsers)
          
      def track_browser_close(self):
          self.active_browsers -= 1
          
      def track_context_creation(self):
          self.active_contexts += 1
          self.peak_contexts = max(self.peak_contexts, self.active_contexts)
          
      def track_context_close(self):
          self.active_contexts -= 1
          
      def track_method_call(self, context_id, method_name):
          if method_name not in self.context_methods_called:
              self.context_methods_called[method_name] = 0
          self.context_methods_called[method_name] += 1
          
      def generate_report(self):
          # Check for potential issues
          issues = []
          if self.active_browsers > 0:
              issues.append(f"Potential leak: {self.active_browsers} browsers not closed")
          if self.active_contexts > 0:
              issues.append(f"Potential leak: {self.active_contexts} contexts not closed")
          
          return {
              "peak_resources": {
                  "browsers": self.peak_browsers,
                  "contexts": self.peak_contexts,
                  "pages": self.peak_pages
              },
              "method_usage": self.context_methods_called,
              "potential_issues": issues
          }
  ```

### 3. File Path Resolver

- **Path Resolution Monitor**:
  ```python
  class PathMonitor:
      def __init__(self, base_dir=None):
          import os
          self.base_dir = base_dir or os.getcwd()
          self.file_access_attempts = []
          
      def track_file_access(self, path, access_type="read", success=True, error=None):
          import os
          
          # Analyze path
          is_absolute = os.path.isabs(path)
          exists = os.path.exists(path)
          
          # Try to fix path if it doesn't exist
          suggestions = []
          if not exists:
              # Check if file exists relative to base_dir
              alternative = os.path.join(self.base_dir, path)
              if os.path.exists(alternative):
                  suggestions.append(alternative)
                  
              # Check if file exists in common subdirectories
              for subdir in ["projects", "data", "tests"]:
                  alternative = os.path.join(self.base_dir, subdir, os.path.basename(path))
                  if os.path.exists(alternative):
                      suggestions.append(alternative)
          
          self.file_access_attempts.append({
              "path": path,
              "access_type": access_type,
              "is_absolute": is_absolute,
              "exists": exists,
              "success": success,
              "error": str(error) if error else None,
              "suggestions": suggestions
          })
          
      def get_file_access_report(self):
          failed_attempts = [a for a in self.file_access_attempts if not a["success"]]
          
          return {
              "total_access_attempts": len(self.file_access_attempts),
              "failed_attempts": len(failed_attempts),
              "failed_details": failed_attempts,
              "common_issues": self._analyze_common_issues(failed_attempts)
          }
          
      def _analyze_common_issues(self, failed_attempts):
          issues = {}
          
          for attempt in failed_attempts:
              error = attempt.get("error", "")
              if "No such file" in error:
                  issues["file_not_found"] = issues.get("file_not_found", 0) + 1
              elif "Permission denied" in error:
                  issues["permission_denied"] = issues.get("permission_denied", 0) + 1
                  
          return issues
  ```

## Visualization

Generate comparative visualizations for efficiency metrics:

1. **Timing Comparison Chart**
   - Bar charts comparing execution times
   - Stacked bars showing time breakdown

2. **Token Usage Comparison**
   - Bar charts for token consumption
   - Prompt vs. completion token distribution

3. **Cost Efficiency Chart**
   - Cost per validation
   - Cost-accuracy ratio visualization

## Cost Optimization Strategies

Based on efficiency metrics, identify optimization opportunities:

1. **Prompt Engineering**
   - Identify verbose prompts
   - Suggest token-saving modifications

2. **Model Selection Guidance**
   - Recommend models based on cost-accuracy tradeoffs
   - Identify scenarios where simpler models suffice

3. **Evidence Collection Optimization**
   - Identify slow evidence gathering processes
   - Suggest caching strategies

## Implementation in research_single_question.py

To implement this metrics framework in the existing script:

1. **Add Metrics Collection**
   - Initialize metrics collectors for each model
   - Add timing instrumentation at key points
   - Track token usage during model calls

2. **Extend Command-Line Interface**
   - Add arguments for metrics collection level
   - Allow specification of output format

3. **Enhance Reporting**
   - Include metrics in JSON output
   - Generate comparison graphs when multiple models are used

## Conclusion

This efficiency metrics framework provides a comprehensive approach to measuring and comparing LLM performance within our `research_single_question.py` script. By tracking detailed metrics across timing, resource usage, API utilization, and costs, we can make data-driven decisions about model selection and optimization strategies.

When combined with the accuracy assessment framework, these efficiency metrics enable a holistic evaluation of model performance, helping us balance accuracy, speed, and cost considerations. 