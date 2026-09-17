# Python AI Agent

A starter AI agent built with Python and OpenAI tool/function calling.

## What it can do

- Chat with an LLM
- Read local text files
- List local files and folders
- Fetch readable text from public webpages
- Look up public GitHub user information
- Use Python functions as agent tools
- Easily add more tools and app/API integrations

## 1. Install Python

Use Python 3.10+.

Check:

```bash
python --version
```

## 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Git Bash:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure API keys

Copy `.env.example` to `.env`.

Windows:

```bash
copy .env.example .env
```

Git Bash/Linux/macOS:

```bash
cp .env.example .env
```

Then put your OpenAI API key into `.env`:

```text
OPENAI_API_KEY=your_real_key
```

Never upload `.env` to GitHub.

## 5. Run the agent

```bash
python run.py
```

## Example commands

Try:

```text
Hello, introduce yourself.
```

```text
Read README.md
```

```text
List the files in the current directory.
```

```text
Open https://example.com and summarize it.
```

```text
Get public information about the GitHub user octocat.
```

## How the agent works

```text
User
  |
  v
Python Agent
  |
  v
OpenAI model
  |
  +----> Local File Tool
  |
  +----> Web Tool
  |
  +----> GitHub Tool
  |
  v
Final answer
```

The model decides whether it needs one of the registered tools. Python executes the selected tool and sends the result back to the model.

## Add your own app

Create a Python function in `app/tools/`.

For example:

```python
def get_weather(city):
    # Call a weather API here
    return "weather result"
```

Then register it inside `TOOLS` in `app/agent.py`.

You can use the same pattern for:

- Gmail
- Google Calendar
- Slack
- Notion
- Discord
- Jira
- GitHub
- databases
- your own REST APIs
- browser automation

For apps that support OAuth, store tokens securely and use the app's official API.

## Important security notes

Do not give the agent unrestricted access to your computer.

For production, add:

- authentication
- permission checks
- tool allowlists
- input validation
- rate limits
- audit logs
- secret management
- human approval for sensitive actions

This starter project intentionally uses read-oriented tools first.
