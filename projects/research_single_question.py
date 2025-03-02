import asyncio
import json
import argparse
import logging
import signal
from copy import deepcopy
from pathlib import Path
from typing import Dict
from browser_use import Agent, SystemPrompt
from browser_use.browser.browser import Browser, BrowserConfig, BrowserContextConfig
from config.llm_config import LLMFactory
import re

class DeepseekSystemPrompt(SystemPrompt):
	def important_rules(self) -> str:
		existing_rules = super().important_rules()
		new_rules = """
IMPORTANT: DO NOT wrap your JSON response in markdown code blocks (```json). Return the raw JSON directly.
"""
		return f'{existing_rules}\n{new_rules}'

class SaviyntQuestionValidator:
    def __init__(self, model_name: str = 'gpt-4o', headless: bool = False, **model_kwargs):
        self.model_name = model_name  # Store model_name as instance variable
        self.browser = Browser(
            config=BrowserConfig(
                headless=headless,
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
        You are validating Saviynt documentation. Follow this EXACT process in order:

        IMPORTANT: Follow these search steps IN ORDER:
        1. FIRST: Search within docs.saviyntcloud.com
           - Start at: {question.get('reference', {}).get('url') or "https://docs.saviyntcloud.com"}
           - Use search bar with extracted key terms
           - Use left navigation menu for context
           - Try at least 3 different search terms before moving to step 2
           - YOU MUST use the latest version of the documentation

        2. IF NO ANSWER FOUND AFTER 20 STEPS: Try developers.saviynt.com
           - Search the developer portal
            - Check API documentation
            - Look through Extensions and Connectors sections
            - Try at least 2 different search approaches
            - YOU MUST use the latest version of the documentation

        3. ONLY IF STEPS 1 & 2 FAIL (after 40 steps): Use Google
            - Restrict search to: site:saviyntcloud.com OR site:developers.saviynt.com
            - Use specific technical terms from the question
            - Focus on official Saviynt content only

        4. ANALYZE QUESTION AND CONTEXT:
            - Question ID: {question['id']}
            - Question: "{question['question']}"
            - Type: {question['type']} (radio=single answer, checkbox=multiple answers)
            - Current Answer(s): {json.dumps(question['answer'])}
            - Extract key technical terms and features
            - Options: {json.dumps(question['options'])}

        5. DOCUMENTATION SEARCH STRATEGY:
            - Start at: {question.get('reference', {}).get('url') or "https://docs.saviyntcloud.com"}
            - Use search bar with extracted key terms
            - Use left navigation menu for context
            - YOU MUST use the latest version of the documentation
            - DO NOT use external search engines like Google

        6. VALIDATE EACH OPTION:
            Options to verify:
            {json.dumps(question['options'], indent=2)}

            For each option:
            - Find explicit documentation evidence supporting or refuting it
            - Note the specific section where evidence is found
            - For checkbox questions, validate each option independently
            - Consider configuration requirements and limitations

        7. CRAFT DETAILED EXPLANATION:
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

        8. VERIFY AND UPDATE REFERENCE:
            - Ensure URL points to specific relevant section
            - Include exact document title
            - Verify URL is accessible and current version

        9. RETURN AND FORMAT:
            IMPORTANT:
            - Return a properly formatted JSON object
            - Use proper grammar and capitalization in all text
            - Ensure options are returned as a proper array/list, not a string

            Format the response exactly like this for radio question types:
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

            Format the response exactly like this for checkbox question types:
            {{
                "id": {question['id']},
                "question": "Question text with proper capitalization",
                "options": [
                    "Option 1",
                    "Option 2",
                    "Option 3"
                ],
                "answer": [
                    "Correct answer(s) with proper capitalization"
                ],
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
            tool_call_in_content=True,
            system_prompt_class=DeepseekSystemPrompt if self.model_name == 'deepseek-chat' else SystemPrompt,
        )

        self.logger.info("Running agent for validation")
        try:
            result = await agent.run()
            self.logger.debug(f"Agent result: {result}")

            if result is None:
                self.logger.error("Agent returned None result")
                return validated_question  # Return original question without changes

            # Extract the JSON string from AgentHistoryList
            try:
                json_str = result.final_result()  # Get the final result string
                if not json_str:
                    self.logger.error("Agent returned empty final result")
                    return validated_question
                
                # Parse the JSON response
                response_data = json.loads(json_str)

                # Ensure options is a list
                if isinstance(response_data.get('options'), str):
                    # If options is a string, try to parse it as JSON
                    try:
                        response_data['options'] = json.loads(response_data['options'])
                    except json.JSONDecodeError:
                        self.logger.error("Failed to parse options string as JSON")
                        return validated_question

                # Validate required fields and types
                required_fields = ['id', 'question', 'options', 'answer', 'type', 'explanation', 'reference']
                if not all(field in response_data for field in required_fields):
                    raise ValueError("Missing required fields in response")

                if not isinstance(response_data['options'], list):
                    raise ValueError("Options must be a list")

                # Update the validated question with the response data
                validated_question.update(response_data)

                self.logger.info("Successfully updated question with validation results")

            except (json.JSONDecodeError, AttributeError) as e:
                self.logger.error(f"Failed to parse response: {e}")
                self.logger.debug(f"Problematic response: {result}")
            except Exception as e:
                self.logger.error(f"Error processing validation response: {e}")
                self.logger.debug(f"Problematic response: {result}")

        except Exception as e:
            self.logger.error(f"Error running agent: {e}")
            self.logger.debug(f"Problematic agent result: {result}")

        if self.shutdown:
            self.logger.info("Gracefully stopping validation...")
            return validated_question

        return validated_question

async def validate_question_by_id(
    question_id: int,
    model_name: str = 'gpt-4o',
    headless: bool = False,
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
            headless=headless,
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
        questions_file = Path('projects/sav-iga-l200b.json')
        logger.info(f"Loading questions from {questions_file}")

        try:
            with open(questions_file) as f:
                try:
                    exam_data = json.load(f)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in questions file: {e}")
                    return
        except FileNotFoundError:
            logger.error(f"Questions file not found: {questions_file}")
            return
        except Exception as e:
            logger.error(f"Failed to load questions file: {e}")
            return

        # Find the question with matching ID
        question = next((q for q in exam_data.get('questions', []) if q.get('id') == question_id), None)

        if not question:
            logger.error(f"Question with ID {question_id} not found")
            return

        logger.info(f"Starting validation for question {question_id}")
        try:
            validated = await validator.validate_question(question)
            if validated is None:
                logger.error("Validation returned None result")
                return
        except Exception as e:
            logger.error(f"Error during question validation: {e}")
            return

        # Save output maintaining original schema
        output_data = {
            "name": exam_data['name'],
            "questions": [validated]
        }

        # Validate schema before saving
        try:
            # Ensure the validated question has all required fields
            required_fields = ['id', 'question', 'options', 'answer', 'type', 'explanation', 'reference']
            if not all(field in validated for field in required_fields):
                missing = [f for f in required_fields if f not in validated]
                logger.error(f"Missing required fields in validated question: {missing}")
                return

            # Ensure reference has required fields
            if not all(field in validated['reference'] for field in ['document', 'url']):
                logger.error("Missing required fields in reference")
                return

            # Ensure options is a list
            if not isinstance(validated['options'], list):
                logger.error("Options must be a list")
                return

            # Ensure answer format matches question type
            if validated['type'] == 'checkbox':
                if not isinstance(validated['answer'], list):
                    logger.error("Answer must be a list for checkbox questions")
                    return
            else:  # radio type
                if not isinstance(validated['answer'], str):
                    logger.error("Answer must be a string for radio questions")
                    return

            # Save with same formatting as input file
            output_file = f'validated_question_{question_id}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Validated question saved to '{output_file}'")

        except Exception as e:
            logger.error(f"Failed to save output file: {e}")
            logger.debug(f"Problematic output data: {json.dumps(output_data, indent=2)}")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        if validator:
            try:
                await validator.cleanup()
                logger.info("Cleanup complete")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
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
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode'
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
            temperature=args.temperature,
            headless=args.headless
        ))
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")