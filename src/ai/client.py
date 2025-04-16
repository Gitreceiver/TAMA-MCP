import logging
import time
from typing import List, Dict, Any, Optional
from openai import OpenAI, APITimeoutError, APIConnectionError, RateLimitError

# Absolute imports
from config.settings import settings
import ai.prompts as prompts

logger = logging.getLogger(__name__)

# Initialize OpenAI client for DeepSeek
if not settings.DEEPSEEK_API_KEY:
    logger.error("DEEPSEEK_API_KEY not found in settings. Please check your .env file.")
    client = None
else:
    try:
        client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY.get_secret_value(),
            base_url=settings.DEEPSEEK_BASE_URL
        )
        logger.info(f"OpenAI client initialized for DeepSeek at {settings.DEEPSEEK_BASE_URL}")
    except Exception as e:
        logger.exception("Failed to initialize OpenAI client for DeepSeek.")
        client = None

# --- Core API Call Function ---

def call_deepseek(
    model: str,
    messages: List[Dict[str, str]],
    max_retries: int = 3,
    retry_delay: int = 5,
    **kwargs # Pass other parameters like temperature, max_tokens
) -> Optional[str]:
    """
    Calls the DeepSeek API using the OpenAI client with retry logic.

    Args:
        model: The model name to use (e.g., settings.DEEPSEEK_GENERAL_MODEL).
        messages: A list of message dictionaries (e.g., [{"role": "user", "content": "..."}]).
        max_retries: Maximum number of retries on specific errors.
        retry_delay: Delay in seconds between retries.
        **kwargs: Additional arguments for chat completions create (temperature, max_tokens).

    Returns:
        The content of the response message or None if an error occurs after retries.
    """
    
    # Original code starts here
    if not client:
        logger.error("DeepSeek client not initialized. Cannot make API call.")
        return None
    
    attempt = 0
    while attempt < max_retries:
        try:
            logger.debug(f"Calling DeepSeek model '{model}' (Attempt {attempt + 1}/{max_retries}). Messages: {messages}")
            api_params = {
                "temperature": settings.AI_TEMPERATURE,
                "max_tokens": settings.AI_MAX_TOKENS,
                **kwargs 
            }
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                **api_params
            )
            response_content = completion.choices[0].message.content
            logger.debug(f"DeepSeek API call successful. Response: {response_content[:100]}...")
            return response_content.strip() if response_content else None

        except (APITimeoutError, APIConnectionError, RateLimitError) as e:
            attempt += 1
            logger.warning(f"DeepSeek API error ({type(e).__name__}), attempt {attempt}/{max_retries}. Retrying in {retry_delay}s...")
            if attempt >= max_retries:
                logger.error(f"DeepSeek API call failed after {max_retries} retries: {e}")
                return None
            time.sleep(retry_delay)
        except Exception as e:
            logger.exception(f"An unexpected error occurred during DeepSeek API call: {e}", exc_info=settings.DEBUG)
            return None
    return None

# --- Specific AI Task Functions ---

def generate_tasks_from_prd(prd_content: str) -> Optional[str]:
    """
    Uses AI to generate a structured list of tasks from PRD content.

    Args:
        prd_content: The content of the Product Requirements Document.

    Returns:
        A JSON string representing the generated tasks, or None on failure.
    """
    logger.info("Generating tasks from PRD using AI...")
    
    # Get the structured prompt from prompts.py
    prompt_message = prompts.get_generate_tasks_prompt(prd_content)

    messages = [{"role": "user", "content": prompt_message}]

    # Use the reasoning model for complex generation
    response = call_deepseek(
        model=settings.DEEPSEEK_REASONING_MODEL,
        messages=messages
    )
    if response:
        logger.info("Successfully generated task structure from PRD.")
        # --- Modification Start: Robust JSON Extraction --- 
        extracted_json = None
        response_str = response.strip()
        try:
            # Determine expected start/end characters (object or list)
            if response_str.find('[') != -1 and response_str.find('[') < response_str.find('{'):
                # Likely a list first
                start_char = '['
                end_char = ']'
            else:
                # Likely an object first or only an object
                start_char = '{'
                end_char = '}'

            # Find the start of the JSON structure
            start_index = response_str.find(start_char)
            # Find the end of the JSON structure (last closing character)
            end_index = response_str.rfind(end_char)
            
            if start_index != -1 and end_index != -1 and end_index > start_index:
                extracted_json = response_str[start_index : end_index + 1]
                # Basic check if it looks like the expected structure
                if not extracted_json.startswith(start_char):
                     extracted_json = None # Reset if extraction doesn't start correctly
            else:
                 logger.debug(f"Could not find valid JSON structure ('{start_char}...{end_char}') in raw response: {response_str[:200]}...")

        except Exception as e:
            logger.warning(f"Error during JSON extraction attempt in generate_tasks_from_prd: {e}")
            extracted_json = None

        # Return the extracted JSON string if successful, otherwise None
        if extracted_json:
            logger.debug("Successfully extracted JSON structure in generate_tasks_from_prd.")
            return extracted_json
        else:
            # Log the final error before returning None
            logger.error(f"AI response did not contain a recognizable JSON structure after extraction attempt: {response_str[:100]}...")
            return None
        # --- Modification End ---
    else:
        logger.error("Failed to generate tasks from PRD using AI (No response received).")
        return None


def expand_task_with_ai(task_title: str, task_description: Optional[str], context: str) -> Optional[str]:
    """
    Uses AI to break down a task into subtasks based on context.

    Args:
        task_title: The title of the parent task.
        task_description: The description of the parent task.
        context: Additional context (e.g., project goals, related tasks).

    Returns:
        A JSON string representing a list of subtasks, or None on failure.
    """
    logger.info(f"Expanding task '{task_title}' into subtasks using AI...")
    # Placeholder prompt:
    prompt_message = f"Please break down the following task into smaller, actionable subtasks based on the provided context. Return the subtasks as a JSON list. Each subtask should have a title and optionally a description and dependencies.\n\nTask Title: {task_title}\nTask Description: {task_description or 'N/A'}\n\nContext:\n{context}"
    messages = [{"role": "user", "content": prompt_message}]

    # Use the reasoning model
    response = call_deepseek(
        model=settings.DEEPSEEK_REASONING_MODEL,
        messages=messages
    )

    if response:
        logger.info(f"Successfully generated subtasks for task '{task_title}'.")
        
        # --- Modification Start: Robust JSON Extraction directly in ai_client ---
        extracted_json = None
        try:
            # Find the start of the JSON list
            start_index = response.find('[')
            # Find the end of the JSON list (last closing bracket)
            end_index = response.rfind(']')
            
            if start_index != -1 and end_index != -1 and end_index > start_index:
                extracted_json = response[start_index : end_index + 1].strip()
                # Basic check if it looks like a list
                if not extracted_json.startswith('['):
                     extracted_json = None # Reset if extraction doesn't start correctly
            else:
                 # Log if structure not found, but don't error yet
                 logger.debug(f"Could not find valid JSON list structure ('[...]') in raw response: {response[:200]}...")

        except Exception as e:
            # Log extraction error, but don't error yet
            logger.warning(f"Error during JSON extraction attempt in ai_client: {e}")
            extracted_json = None

        # Return the extracted JSON string if successful, otherwise None
        if extracted_json:
            logger.debug(f"Successfully extracted JSON list structure in ai_client.")
            return extracted_json
        else:
            # Log the final error before returning None
            logger.error(f"AI response did not contain a recognizable JSON list structure after extraction attempt: {response[:100]}...")
            return None
        # --- Modification End ---
    else:
        logger.error(f"Failed to generate subtasks for task '{task_title}' using AI (No response received).")
        return None

# Example usage (for testing purposes, remove later)
# if __name__ == '__main__':
#     logging.basicConfig(level=logging.DEBUG)
#     # Ensure you have a .env file with DEEPSEEK_API_KEY
#     # test_prd = "Create a login page with username and password fields and a submit button."
#     # generated_tasks_json = generate_tasks_from_prd(test_prd)
#     # print("Generated Tasks JSON:\n", generated_tasks_json)

#     # test_task_title = "Implement user authentication"
#     # test_task_desc = "Handle user login and session management."
#     # test_context = "The application needs secure login. Use JWT tokens."
#     # generated_subtasks_json = expand_task_with_ai(test_task_title, test_task_desc, test_context)
#     # print("\nGenerated Subtasks JSON:\n", generated_subtasks_json)
