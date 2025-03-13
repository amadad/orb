"""
Adapter module for LiteLLM skill.
Provides backward compatibility with existing activities.
"""

import logging
from .skill_chat import ChatSkill, chat_skill

logger = logging.getLogger(__name__)

# Create an alias for the global instance
lite_llm_skill = chat_skill
logger.info("Initialized lite_llm_skill adapter (aliased to chat_skill)") 