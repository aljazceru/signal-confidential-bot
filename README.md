# Shifra - Signal enabled confidential AI.

A Signal messenger bot that gives you AI agent in your chat.

## Features

- Chat with AI assistant via Signal messages
- Maintains conversation context
- Simple command interface
- Docker deployment ready

## Setup

1. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your configuration:
   - `SIGNAL_PHONE_NUMBER`: Your Signal phone number (e.g., +1234567890)
   - `PRIVATEMODE_BASE_URL`: URL of PrivateMode.ai API (default: http://localhost:8080)
   - `PRIVATEMODE_MODEL`: Optional - specific model to use (if not set, uses first available)

3. Link Signal account (first time only):
   ```bash
   docker-compose run --rm signal-cli-rest-api signal-cli link -n "Signal Bot"
   ```
   Follow the instructions to scan QR code with Signal app.

4. Start the bot:
   ```bash
   docker-compose up -d
   ```

## Usage

Send messages to the bot:

- `!chat <message>` - Chat with AI assistant
- `!clear` - Clear conversation history
- `!models` - List available AI models
- `!help` - Show available commands
- Any message without command prefix is treated as chat

## Available Models

The bot can use any model available through PrivateMode.ai API. Use `!models` command to see available models. Example models:
- `ibnzterrell/Meta-Llama-3.3-70B-Instruct-AWQ-INT4`

## Development

Run locally:
```bash
pip install -r requirements.txt
python signal_bot.py
```

## Architecture

- Uses `signalbot` library for Signal integration
- Connects to PrivateMode.ai Chat Completions API endpoint
- Maintains conversation context per sender (last 10 messages)
- Supports docker deployment with signal-cli-rest-api
- No authentication required (follows PrivateMode.ai approach)
