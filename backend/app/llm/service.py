"""
LLM service for communicating with language models through LangChain.
"""
import logging
from typing import Dict, List, Any, Optional

from langchain.chains import LLMChain
from langchain_community.chat_models import ChatAnthropic, ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage, AIMessage

from app.core.config import settings

# Set up logger
logger = logging.getLogger(__name__)

class LLMService:
    """
    Service for communicating with language models using LangChain.
    Handles prompt creation, LLM initialization, and response handling.
    """
    
    def __init__(self):
        """Initialize the LLM service with the appropriate language model."""
        self._initialize_llm()
        
    def _initialize_llm(self):
        """Initialize the language model based on configuration settings."""
        if settings.ANTHROPIC_API_KEY:
            logger.info("Initializing Anthropic Claude model")
            self.llm = ChatAnthropic(
                model_name="claude-3-sonnet-20240229",  # Using a recommended Claude model
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                temperature=0.7
            )
        elif settings.OPENAI_API_KEY:
            logger.info("Initializing OpenAI model")
            self.llm = ChatOpenAI(
                model_name=settings.LLM_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=0.7
            )
        else:
            error_msg = "No API key provided for either Anthropic or OpenAI"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
    def create_chain(self, system_prompt: str, human_prompt: str = "{input}") -> LLMChain:
        """
        Create an LLM chain with the specified prompts.
        
        Args:
            system_prompt: The system prompt to guide the LLM's behavior
            human_prompt: The human message template, with {input} as the placeholder for user input
            
        Returns:
            An LLMChain object configured with the specified prompts
        """
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ])
        
        return LLMChain(llm=self.llm, prompt=prompt_template)
    
    async def generate_response(self, 
                         system_prompt: str, 
                         user_input: str, 
                         conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Generate a response from the LLM based on the system prompt, user input, and conversation history.
        
        Args:
            system_prompt: The system prompt to guide the LLM's behavior
            user_input: The user's input/query
            conversation_history: Optional list of previous messages in the conversation
            
        Returns:
            The LLM's response as a string
        """
        messages = [SystemMessage(content=system_prompt)]
        
        # Add conversation history if provided
        if conversation_history:
            for message in conversation_history:
                if message["role"] == "user":
                    messages.append(HumanMessage(content=message["content"]))
                elif message["role"] == "assistant":
                    messages.append(AIMessage(content=message["content"]))
        
        # Add the current user input
        messages.append(HumanMessage(content=user_input))
        
        try:
            logger.debug(f"Sending message to LLM: {messages}")
            response = await self.llm.agenerate([messages])
            llm_response = response.generations[0][0].text
            logger.debug(f"Received response from LLM: {llm_response}")
            return llm_response
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            raise 