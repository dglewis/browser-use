import asyncio
import json
import argparse
import logging
import signal
from copy import deepcopy
from pathlib import Path
from typing import Dict
from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig, BrowserContextConfig
from config.llm_config import LLMFactory
import re

class SaviyntQuestionValidator:
    def __init__(self, model_name: str = 'gpt-4o', **model_kwargs):
        self.browser = Browser(
            config=BrowserConfig(
                headless=False,
                disable_security=True,
                new_context_config=BrowserContextConfig(
                    disable_security=True,
                    minimum_wait_page_load_time=1,
                    maximum_wait_page_load_time=10,
                    browser_window_size={
                        'width': 1280,
                        'height': 1100,
                    }
                ),
            )
        )

        # Initialize LLM using factory
        self.llm = LLMFactory.create_llm(model_name, **model_kwargs)
        self.logger = logging.getLogger(__name__)
        self.shutdown = False

    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up resources...")
        if self.browser:
            await self.browser.close()
        self.logger.info("Cleanup complete")

    async def get_latest_version(self) -> str:
        """Check docs homepage to determine latest version"""
        try:
            page = await self.browser.new_page()
            await page.goto("https://docs.saviyntcloud.com")
            # Logic to find latest version from available options
            return "latest"  # This would actually return the found version
        except Exception as e:
            self.logger.error(f"Failed to determine latest version: {e}")
            return "current"

    async def validate_question(self, question: Dict) -> Dict:
        self.logger.info(f"Starting validation for question ID {question['id']}")
        validated_question = deepcopy(question)

        # Extract key search terms from question
        search_terms = question['question'].lower()

        task = f"""
        You are validating Saviynt documentation. Follow this EXACT process:

        IMPORTANT: You must ONLY use the Saviynt documentation website.
        - YOU MUST use the latest version of the documentation
        - DO NOT use Google or any other search engine.

        1. ANALYZE QUESTION AND CONTEXT:
        - Question ID: {question['id']}
        - Question: "{question['question']}"
        - Type: {question['type']} (radio=single answer, checkbox=multiple answers)
        - Current Answer(s): {json.dumps(question['answer'])}
        - Extract key technical terms and features
        - Options: {json.dumps(question['options'])}

        2. DOCUMENTATION SEARCH STRATEGY:
        - Start at: {question.get('reference', {}).get('url') or "https://docs.saviyntcloud.com"}
        - Use search bar with extracted key terms
        - Use left navigation menu for context
        - YOU MUST use the latest version of the documentation
        - DO NOT use external search engines like Google

        3. VALIDATE EACH OPTION:
        Options to verify:
        {json.dumps(question['options'], indent=2)}

        For each option:
        - Find explicit documentation evidence supporting or refuting it
        - Note the specific section where evidence is found
        - For checkbox questions, validate each option independently
        - Consider configuration requirements and limitations

        4. CRAFT DETAILED EXPLANATION:
        - Explain WHY correct answers are correct and incorrect answers are incorrect
        - FOCUS on WHY the answer is correct or incorrect, not WHAT the answer is.
        - For incorrect options, explain why they're wrong
        - Include configuration context if relevant
        - Reference specific documentation sections
        - For scenario questions, explain the reasoning for each option
        - Provide a detailed, well-written explanation with a clear and concise answer, providing context where helpful for learning.
        - For scenario-based questions, also provid detailed reasoning for each option.
        - Included why secondary options (like delegation and manual selection) are less critical but still worth checking.
        - Ensure the reference URL points to a specific relevant section of the documentation.
        - DO NOT state that the answer is because the documentation says so, such as, "The documentation indicates that..." or "...as mentioned in the documentation..." since it is obvious that the documentation is the source of the answer.

        5. VERIFY AND UPDATE REFERENCE:
        - Ensure URL points to specific relevant section
        - Include exact document title
        - Verify URL is accessible and current version

        6. RETURN AND FORMAT:
        IMPORTANT:
        - Return a properly formatted JSON object
        - Use proper grammar and capitalization in all text
        - Ensure options are returned as a proper array/list, not a string

        Format the response exactly like this:
        {{
            "id": {question['id']},
            "question": "Question text with proper capitalization",
            "options": [
                "Option 1",
                "Option 2",
                "Option 3"
            ],
            "answer": "Correct answer with proper capitalization",
            "type": "{question['type']}",
            "explanation": "Detailed explanation with proper grammar and capitalization",
            "reference": {{
                "document": "Exact document title",
                "url": "Specific documentation URL"
            }}
        }}
        """

        agent = Agent(
            task=task,
            llm=self.llm,
            browser=self.browser,
            max_actions_per_step=4,
            tool_call_in_content=True
        )

        self.logger.info("Running agent for validation")
        result = await agent.run()
        self.logger.debug(f"Agent result: {result}")

        try:
            # Parse the JSON response
            response_data = json.loads(result)

            # Validate required fields
            required_fields = ['id', 'question', 'options', 'answer', 'type', 'explanation', 'reference']
            if not all(field in response_data for field in required_fields):
                raise ValueError("Missing required fields in response")

            # Ensure options is a list
            if not isinstance(response_data['options'], list):
                raise ValueError("Options must be a list")

            # Update the validated question with the response data
            validated_question.update(response_data)

            self.logger.info("Successfully updated question with validation results")

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            self.logger.debug(f"Invalid JSON response: {result}")
        except Exception as e:
            self.logger.error(f"Error processing validation response: {e}")
            self.logger.debug(f"Problematic response: {result}")

        if self.shutdown:
            self.logger.info("Gracefully stopping validation...")
            return validated_question

        return validated_question

async def validate_question_by_id(
    question_id: int,
    model_name: str = 'gpt-4o',
    **model_kwargs
):
    validator = None
    try:
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'question_{question_id}_validation.log'),
                logging.StreamHandler()
            ]
        )
        logger = logging.getLogger(__name__)

        validator = SaviyntQuestionValidator(
            model_name=model_name,
            **model_kwargs
        )

        # Handle Ctrl+C gracefully
        def signal_handler():
            logger.info("Received shutdown signal, cleaning up...")
            validator.shutdown = True

        # Register signal handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop = asyncio.get_event_loop()
            loop.add_signal_handler(sig, signal_handler)

        # Load the source questions file
        questions_file = Path('sav-iga-l200b.json')
        logger.info(f"Loading questions from {questions_file}")

        try:
            with open(questions_file) as f:
                exam_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load questions file: {e}")
            return

        # Find the question with matching ID
        question = next((q for q in exam_data['questions'] if q['id'] == question_id), None)

        if not question:
            logger.error(f"Question with ID {question_id} not found")
            return

        logger.info(f"Starting validation for question {question_id}")
        validated = await validator.validate_question(question)

        # Save output maintaining original schema
        output_data = {
            "name": exam_data['name'],
            "questions": [validated]
        }

        # Save with same formatting as input file
        output_file = f'validated_question_{question_id}.json'
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Validated question saved to '{output_file}'")
        except Exception as e:
            logger.error(f"Failed to save output file: {e}")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        if validator:
            await validator.cleanup()
        logger.info("Validation process completed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Validate a specific question by ID')
    parser.add_argument('question_id', type=int, help='ID of the question to validate')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument(
        '--model',
        choices=list(LLMFactory.MODELS.keys()),
        default='gpt-4o',
        help='LLM model to use for validation'
    )
    parser.add_argument(
        '--temperature',
        type=float,
        default=0.7,
        help='Temperature for LLM sampling (0.0-1.0)'
    )
    args = parser.parse_args()

    # Set logging level based on debug flag
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'question_{args.question_id}_validation.log'),
            logging.StreamHandler()
        ]
    )

    try:
        asyncio.run(validate_question_by_id(
            question_id=args.question_id,
            model_name=args.model,
            temperature=args.temperature
        ))
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")