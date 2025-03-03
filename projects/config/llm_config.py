from typing import Dict, Optional
from dataclasses import dataclass
from langchain_openai import ChatOpenAI

@dataclass
class ModelConfig:
    model_id: str
    base_url: str = "https://openrouter.ai/api/v1"
    context_length: int = 8192
    temperature: float = 0.2
    supports_vision: bool = False
    description: str = ""

class LLMFactory:
    """Factory for creating LLM instances with OpenRouter configurations"""

    # Define available models
    MODELS: Dict[str, ModelConfig] = {
        'gpt-4o': ModelConfig(
            model_id='gpt-4o',
            description="GPT-4 via OpenRouter"
        ),
        'deepseek-chat': ModelConfig(
            model_id='deepseek/deepseek-chat',
            description="DeepSeek Chat model"
        ),
        'mistral-7b-v02': ModelConfig(
            model_id='mistralai/mistral-7b-instruct-v0.2',
            description="Mistral 7B Instruct v0.2"
        ),
        'llama-3-70b': ModelConfig(
            model_id='meta-llama/llama-3.2-70b-instruct',
            description="Llama 3 70B Instruct"
        ),
        'qwen-72b': ModelConfig(
            model_id='qwen/qwen-72b-instruct',
            description="Qwen 72B Instruct"
        ),
        'sonar-medium-online': ModelConfig(
            model_id='perplexity/llama-3.1-sonar-medium-32k-online',
            description="Sonar Medium with online access"
        ),
        'claude-3.5-sonnet': ModelConfig(
            model_id='anthropic/claude-3.5-sonnet:beta',
            description="Claude 3.5 Sonnet (self-moderated)"
        ),
        'claude-3.7-sonnet': ModelConfig(
            model_id='anthropic/claude-3.7-sonnet:beta',
            description="Claude 3.7 Sonnet (latest version)"
        ),
    }

    @classmethod
    def create_llm(cls, model_name: str, **kwargs) -> ChatOpenAI:
        """Create a LangChain ChatOpenAI instance with the specified model

        Args:
            model_name: Name of the model to use from MODELS dictionary
            **kwargs: Additional parameters to pass to ChatOpenAI
                - temperature: Controls randomness in the model's responses (0.0-1.0)
                  Lower values (e.g., 0.2) make responses more focused and deterministic
                  Higher values (e.g., 0.8) make responses more creative and diverse
                  Default values are set per model in ModelConfig, but can be overridden here

        Returns:
            ChatOpenAI: Configured language model instance

        Raises:
            ValueError: If model_name is not found in MODELS dictionary
        """
        if model_name not in cls.MODELS:
            available_models = "\n".join(f"- {k}: {v.description}" for k, v in cls.MODELS.items())
            raise ValueError(
                f"Unknown model: {model_name}\n"
                f"Available models:\n{available_models}"
            )

        config = cls.MODELS[model_name]

        # Allow temperature override from kwargs, fallback to model's default
        temperature = kwargs.pop('temperature', config.temperature)

        return ChatOpenAI(
            model=config.model_id,
            base_url=config.base_url,
            model_kwargs={"max_tokens": config.context_length},
            temperature=temperature,  # Use potentially overridden temperature
            **kwargs  # Pass remaining kwargs to ChatOpenAI
        )

    @classmethod
    def list_models(cls) -> Dict[str, str]:
        """Return a dictionary of available models and their descriptions"""
        return {name: config.description for name, config in cls.MODELS.items()}