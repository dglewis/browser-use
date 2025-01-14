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
        NEVER use Google or any other search engine.

        1. ANALYZE QUESTION AND CONTEXT:
        - Question: "{question['question']}"
        - Type: {question['type']} (radio=single answer, checkbox=multiple answers)
        - Current Answer(s): {json.dumps(question['answer'])}
        - Extract key technical terms and features
        - Identify the documentation section context (e.g., Configuration, Administration, Features)

        2. DOCUMENTATION SEARCH STRATEGY:
        - Start at: {question.get('reference', {}).get('url') or "https://docs.saviyntcloud.com"}
        - Use search bar with extracted key terms
        - Use left navigation menu for context
        - Stay within current version documentation
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
        - Explain WHY correct answers are correct
        - For incorrect options, explain why they're wrong
        - Include configuration context if relevant
        - Reference specific documentation sections
        - For scenario questions, explain the reasoning for each option

        5. VERIFY AND UPDATE REFERENCE:
        - Ensure URL points to specific relevant section
        - Include exact document title
        - Verify URL is accessible and current version

        6. RETURN AND FORMAT:
        - Format the newly verified question as the original question, but with the new explanation and reference.
        - Return results in JSON format matching the original question schema:
        {{
            "question": "original question text with proper grammar and punctuation",
            "options": "original options text with proper grammar and punctuation",
            "answer": "correct answer(s) text with proper grammar and punctuation",
            "type": "original question type",
            "explanation": "detailed explanation following guidelines",
            "reference": {{
                "document": "exact document title",
                "url": "specific documentation URL"
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
            # Parse the agent's response which is in markdown format
            lines = result.split('\n')

            # Extract the relevant parts
            explanation = ""
            reference = {}

            in_explanation = False
            for line in lines:
                if line.startswith('**Explanation**:'):
                    in_explanation = True
                    continue
                elif line.startswith('**Reference**:'):
                    in_explanation = False
                    continue
                elif in_explanation and line.strip():
                    explanation += line.strip() + "\n"
                elif line.strip().startswith('- **Document**:'):
                    reference['document'] = line.split(':')[1].strip()
                elif line.strip().startswith('- **URL**:'):
                    # Extract URL from markdown link format [title](url)
                    url_match = re.search(r'\((.*?)\)', line)
                    if url_match:
                        reference['url'] = url_match.group(1)

            # Update only the explanation and reference
            validated_question.update({
                'explanation': explanation.strip(),
                'reference': reference
            })

            self.logger.info("Successfully updated explanation and reference")

        except Exception as e:
            self.logger.error(f"Failed to parse agent response: {e}")
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