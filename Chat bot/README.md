# 🤖 PyBot v2.0 — Advanced Python Chatbot

A feature-rich, rule-based chatbot built in **pure Python** with zero external dependencies. PyBot combines pattern matching, intent classification, and a set of practical tools into a single interactive CLI application.

---

## What is PyBot?

PyBot is a command-line chatbot that goes well beyond simple keyword responses. It understands natural language patterns, remembers context across a conversation, analyzes the sentiment of your messages, and handles a variety of real tasks — all without calling any external API or requiring an internet connection.

Under the hood, every user message passes through a pipeline: sentiment is scored using a lexicon-based analyzer, the text is matched against a registry of regex and keyword-based intents, and the matching handler produces a structured response. The engine tracks conversation history, the user's name, and session statistics across turns.

---

## Features

**Intent & Pattern Matching**  
An `IntentRegistry` holds a prioritized list of `Intent` objects, each with a set of regex patterns and keyword fallbacks. Incoming messages are matched in priority order so that specific intents (math, greetings, farewells) always win over general ones.

**Safe Math Evaluator**  
Arithmetic expressions are parsed with a hand-written recursive-descent parser — no `eval()` or `exec()` anywhere. Supports the four basic operators, exponentiation (`**`), modulo, parentheses, and common math functions: `sqrt`, `sin`, `cos`, `tan`, `log`, `log10`, `abs`, `ceil`, `floor`, `round`, plus the constants `pi` and `e`.

**Unit Converter**  
Converts between units of length (m, km, miles, feet, inches, …), weight (kg, g, lb, oz, …), and speed (m/s, km/h, mph, knots, …) using a base-unit table. Temperature conversions between Celsius, Fahrenheit, and Kelvin are handled separately with the correct formulas.

**Sentiment Analysis**  
Each user message receives a `positive`, `negative`, or `neutral` label using a lexicon of scored words, with support for intensifiers ("very", "really") and negations ("not", "never"). The session tracks your dominant sentiment over time.

**Trivia Quiz**  
A built-in bank of 15 questions, drawn randomly for each session. Supports hints (at the cost of the point), skipping, and a final score report with a percentage and grade.

**Todo List Manager**  
An in-session task list with commands to add, complete, remove, and clear tasks. Tasks are numbered automatically and displayed with a visual done/pending indicator.

**Conversation Memory**  
The last 30 turns are stored as `Message` objects (role, content, timestamp, intent, sentiment). The bot uses this history to greet returning users by name, report session statistics, and export the full log to JSON.

**Colored Terminal Output**  
All output uses ANSI escape codes via a `Color` helper class, giving the bot, the user prompt, errors, and system messages distinct colors without any third-party library.

---

## Project Structure

```
pybot/
├── ChatBot.py          # Single-file application — everything lives here
└── chat_history.json # Auto-generated when you run the 'history' command
```

The entire project ships as one self-contained file. The main components are organized into clearly separated classes:

| Class | Responsibility |
|---|---|
| `ChatBot` | Main engine; wires all components together and runs the REPL |
| `IntentRegistry` | Stores and matches intents by regex / keyword |
| `MathEvaluator` | Recursive-descent parser for arithmetic expressions |
| `UnitConverter` | Lookup-table converter for physical units |
| `SentimentAnalyzer` | Lexicon-based positive/negative/neutral scorer |
| `QuizSession` | State machine for the trivia quiz |
| `TodoManager` | In-memory task list with command parser |
| `ConversationMemory` | Rolling history with statistics and JSON export |

---

## Usage

```bash
python ChatBot.py
```

Pass `--no-delay` to disable the typing animation (useful for testing or piping input):

```bash
python ChatBot.py --no-delay
```

**Example commands inside the chat:**

```
calculate sqrt(144) + 2**10
10 km to miles
72 fahrenheit to celsius
todo add Write unit tests
todo list
todo done 1
quiz
quiz 10 questions
stats
history
bye
```

---

## Requirements

- Python 3.7 or later
- No external packages — only the standard library (`math`, `re`, `json`, `datetime`, `random`, `dataclasses`)

---

## License

MIT
