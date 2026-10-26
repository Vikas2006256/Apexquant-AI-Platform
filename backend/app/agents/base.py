import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
import google.generativeai as genai

from app.core.config import settings

logger = logging.getLogger("apexquant.agents")

class BaseAgent:
    def __init__(self, name: str, role_description: str):
        self.name = name
        self.role_description = role_description
        
        # Setup OpenAI
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            try:
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client in {self.name}: {e}")
                
        # Setup Gemini
        self.gemini_configured = False
        if settings.GEMINI_API_KEY:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.gemini_configured = True
            except Exception as e:
                logger.error(f"Failed to configure Gemini in {self.name}: {e}")

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Core execution loop for the agent. Must be implemented by subclasses."""
        raise NotImplementedError("Each agent must implement its own run method.")

    def format_prompt(self, system_prompt: str, user_prompt: str) -> str:
        """Helper to format prompts consistently."""
        return f"System: {system_prompt}\n\nUser: {user_prompt}"

    async def call_llm(self, user_prompt: str, system_prompt: Optional[str] = None) -> str:
        """Dispatches prompting to available LLM or simulation fallback."""
        sys_prompt = system_prompt or self.role_description
        
        # 1. Try OpenAI
        if self.openai_client:
            try:
                messages = []
                if sys_prompt:
                    messages.append({"role": "system", "content": sys_prompt})
                messages.append({"role": "user", "content": user_prompt})
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",  # Production grade default, handles JSON
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.2
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI call failed in {self.name}, falling back: {e}")
                
        # 2. Try Gemini
        if self.gemini_configured:
            try:
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    generation_config={"response_mime_type": "application/json"}
                )
                prompt = self.format_prompt(sys_prompt, user_prompt)
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                logger.error(f"Gemini call failed in {self.name}: {e}")
                
        # 3. If no LLM available or both failed, raise exception to trigger simulation fallback in run()
        raise RuntimeError("No LLM client configured or available.")

    def sanitize_json_response(self, text: str) -> Dict[str, Any]:
        """Cleans and parses JSON from the raw LLM string."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        try:
            return json.loads(text.strip())
        except Exception as e:
            logger.error(f"JSON parsing error in {self.name}: {e}. Raw response: {text}")
            return {
                "explanation": f"Failed to parse AI response. Error: {str(e)}",
                "confidence": 50,
                "data": {}
            }
