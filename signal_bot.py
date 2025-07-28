#!/usr/bin/env python3
import os
import asyncio
import logging
import aiohttp
import json
from signalbot import SignalBot, Command, Context
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PrivateModeClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Content-Type": "application/json"
        }
    
    async def list_models(self) -> list:
        url = f"{self.base_url}/v1/models"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return [model['id'] for model in data.get('data', [])]
                    else:
                        logger.error(f"Failed to list models: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"Model listing failed: {str(e)}")
                return []
    
    async def chat_completion(self, messages: list, model: str = None) -> str:
        url = f"{self.base_url}/v1/chat/completions"
        
        # Use provided model or get the first available one
        if not model:
            available_models = await self.list_models()
            if available_models:
                model = available_models[0]
                logger.info(f"Using model: {model}")
            else:
                return "Sorry, no models are available at the moment."
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['choices'][0]['message']['content']
                    else:
                        error_text = await response.text()
                        logger.error(f"API error: {response.status} - {error_text}")
                        return f"Sorry, I encountered an error: {response.status}"
            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                return f"Sorry, I couldn't process your request: {str(e)}"


class ChatCommand(Command):
    def __init__(self, privatemode_client: PrivateModeClient, model: str = None):
        self.privatemode_client = privatemode_client
        self.model = model
        self.conversations = {}
    
    def describe(self) -> str:
        return "Chat with AI assistant"
    
    async def handle(self, c: Context):
        logger.info(f"ChatCommand.handle called with message: {c.message.text}")
        
        message_text = c.message.text
        if not message_text:
            await c.send("Please provide a message to chat with the AI.")
            return
        
        # Get or create conversation history for this sender
        sender = c.message.source
        if sender not in self.conversations:
            self.conversations[sender] = []
        
        # Add user message to history
        self.conversations[sender].append({
            "role": "user",
            "content": message_text
        })
        
        # Keep only last 10 messages for context
        if len(self.conversations[sender]) > 10:
            self.conversations[sender] = self.conversations[sender][-10:]
        
        # Get AI response
        response = await self.privatemode_client.chat_completion(self.conversations[sender], self.model)
        
        # Add assistant response to history+50672831532
        self.conversations[sender].append({
            "role": "assistant",
            "content": response
        })
        
        # Send response
        await c.send(response)


class ClearCommand(Command):
    def __init__(self, chat_command: ChatCommand):
        self.chat_command = chat_command
    
    def describe(self) -> str:
        return "Clear conversation history"
    
    async def handle(self, c: Context):
        sender = c.message.source
        if sender in self.chat_command.conversations:
            del self.chat_command.conversations[sender]
            await c.send("Conversation history cleared.")
        else:
            await c.send("No conversation history to clear.")


class ModelsCommand(Command):
    def __init__(self, privatemode_client: PrivateModeClient):
        self.privatemode_client = privatemode_client
    
    def describe(self) -> str:
        return "List available AI models"
    
    async def handle(self, c: Context):
        models = await self.privatemode_client.list_models()
        if models:
            models_text = "Available models:\n" + "\n".join(f"• {model}" for model in models)
        else:
            models_text = "No models available or unable to fetch model list."
        await c.send(models_text)


class HelpCommand(Command):
    def describe(self) -> str:
        return "Show available commands"
    
    async def handle(self, c: Context):
        help_text = """Available commands:
!chat <message> - Chat with AI assistant
!clear - Clear conversation history
!models - List available models
!help - Show this help message

You can also send messages without commands for direct chat."""
        await c.send(help_text)


def main():
    # Load configuration
    signal_service = os.getenv("SIGNAL_SERVICE", "localhost:8080")
    phone_number = os.getenv("SIGNAL_PHONE_NUMBER")
    
    if not phone_number:
        logger.error("SIGNAL_PHONE_NUMBER environment variable is required")
        return
    
    # PrivateMode API configuration
    privatemode_base_url = os.getenv("PRIVATEMODE_BASE_URL", "http://localhost:8080")
    model = os.getenv("PRIVATEMODE_MODEL", None)
    
    # Initialize PrivateMode client
    privatemode_client = PrivateModeClient(privatemode_base_url)
    
    # Initialize Signal bot
    bot = SignalBot({
        "signal_service": signal_service,
        "phone_number": phone_number,
        "logging_level": logging.INFO
    })
    
    # Create a universal chat handler
    class UniversalChatHandler(Command):
        def __init__(self):
            self.chat_command = ChatCommand(privatemode_client, model)
        
        def describe(self) -> str:
            return "Universal chat handler"
        
        async def handle(self, c: Context):
            logger.info(f"UniversalChatHandler.handle called with message: {c.message.text}")
            if c.message.text:
                # Pass the full message text to chat command
                await self.chat_command.handle(c)
    
    # Register the universal handler for all messages
    bot.register(UniversalChatHandler())
    
    logger.info(f"Starting Signal bot on {signal_service} with number {phone_number}")
    logger.info(f"Using PrivateMode API at {privatemode_base_url}")
    if model:
        logger.info(f"Using model: {model}")
    
    bot.start()


if __name__ == "__main__":
    main()