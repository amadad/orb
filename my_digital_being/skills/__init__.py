"""
Skills package for Digital Being

Implementations of various skills that activities can use.

Skills registry - provides centralized access to all skill instances.

Import this module to access skills:
    from skills import registry
    
    # Then use:
    registry.chat_skill.get_chat_completion(...)
    registry.image_generation_skill.generate_image(...)
"""

import logging
from importlib import import_module
from types import ModuleType
from typing import Dict, Any, Optional
import sys
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Add the my_digital_being directory to sys.path
# This makes direct 'framework' imports work in skill files
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.append(str(parent_dir))

class SkillRegistry:
    """Central registry for all skills in the system."""
    
    def __init__(self):
        self._skill_modules: Dict[str, ModuleType] = {}
        self._skill_instances: Dict[str, Any] = {}
        
        # Register standard skills
        self.register_skill_module("skill_chat", "chat_skill")
        self.register_skill_module("skill_generate_image", "ImageGenerationSkill", 
                                  instance_name="image_generation_skill",
                                  init_args=[{
                                      "enabled": True,
                                      "max_generations_per_day": 50,
                                      "supported_formats": ["png", "jpg"]
                                  }])
                                  
        # Also create aliases for backward compatibility
        self.register_alias("lite_llm_skill", "chat_skill")
        
        # Register the Serper API skill
        self.register_skill_module("skill_serper_api", "serper_api_skill")
    
    def register_skill_module(self, module_name: str, attr_name: str, 
                             instance_name: Optional[str] = None,
                             init_args=None, init_kwargs=None) -> None:
        """
        Register a skill module and make its instance available.
        
        Args:
            module_name: Name of the module (without 'skills.' prefix)
            attr_name: Name of the class or instance in the module
            instance_name: Name to expose the instance as (defaults to attr_name)
            init_args: Arguments for class instantiation (if attr_name is a class)
            init_kwargs: Keyword arguments for instantiation (if attr_name is a class)
        """
        try:
            # Import the module
            full_module_path = f"skills.{module_name}"
            module = import_module(full_module_path)
            self._skill_modules[module_name] = module
            
            # Get the attribute (class or instance)
            attr = getattr(module, attr_name)
            
            # If no instance name provided, use the attribute name
            if not instance_name:
                instance_name = attr_name
            
            # If it's a class, instantiate it
            if isinstance(attr, type):
                args = init_args or []
                kwargs = init_kwargs or {}
                instance = attr(*args, **kwargs)
                self._skill_instances[instance_name] = instance
                logger.info(f"Instantiated {attr_name} from {module_name} as {instance_name}")
            else:
                # It's already an instance
                self._skill_instances[instance_name] = attr
                logger.info(f"Registered instance {attr_name} from {module_name} as {instance_name}")
                
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not register skill {module_name}.{attr_name}: {e}")
    
    def register_alias(self, alias_name: str, original_name: str) -> None:
        """Register an alias for an existing skill instance."""
        if original_name in self._skill_instances:
            self._skill_instances[alias_name] = self._skill_instances[original_name]
            logger.info(f"Created alias {alias_name} -> {original_name}")
        else:
            logger.warning(f"Cannot create alias {alias_name}: {original_name} not found")
    
    def __getattr__(self, name: str) -> Any:
        """Allow accessing registered skills as attributes."""
        if name in self._skill_instances:
            return self._skill_instances[name]
        raise AttributeError(f"No skill named '{name}' is registered")


# Create the global registry instance
registry = SkillRegistry()

# For backward compatibility, also export individual skills
chat_skill = registry.chat_skill
image_generation_skill = registry.image_generation_skill
lite_llm_skill = registry.lite_llm_skill
