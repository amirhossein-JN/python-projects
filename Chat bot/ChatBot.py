"""
PyBot - Advanced CLI Chatbot
=============================
A feature-rich, rule-based + pattern-matching chatbot built in pure Python.
No external dependencies required.

Features:
  - Intent classification with keyword + regex matching
  - Conversation context & memory (tracks last N turns)
  - Sentiment detection (positive / negative / neutral)
  - Math expression evaluator (no eval())
  - Unit converter (length, weight, temperature)
  - Todo list manager (in-session)
  - Trivia quiz mode
  - History log saved to file
  - Colored terminal output
  - Plugin-style intent registry
  - Graceful error handling & fallback chains
  - Typing animation effect
  - Session statistics

Author  : PyBot Project
Version : 2.0.0
License : MIT
"""

from __future__ import annotations

import math
import os
import random
import re
import sys
import time
import datetime
import json
import operator
from dataclasses import dataclass, field
from typing import Callable, Optional


# ══════════════════════════════════════════════════════════════════════════════
#  ANSI COLOR HELPERS
# ══════════════════════════════════════════════════════════════════════════════

class Color:
    """ANSI escape codes for terminal coloring."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"

    @staticmethod
    def wrap(text: str, *codes: str) -> str:
        return "".join(codes) + text + Color.RESET

    @staticmethod
    def bot(text: str) -> str:
        return Color.wrap(text, Color.CYAN)

    @staticmethod
    def user_prompt() -> str:
        return Color.wrap("You: ", Color.GREEN, Color.BOLD)

    @staticmethod
    def error(text: str) -> str:
        return Color.wrap(text, Color.RED)

    @staticmethod
    def info(text: str) -> str:
        return Color.wrap(text, Color.YELLOW)

    @staticmethod
    def success(text: str) -> str:
        return Color.wrap(text, Color.GREEN)

    @staticmethod
    def dim(text: str) -> str:
        return Color.wrap(text, Color.DIM)


# ══════════════════════════════════════════════════════════════════════════════
#  DATA CLASSES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Message:
    """Represents a single conversation turn."""
    role: str          # "user" | "bot"
    content: str
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    intent: str = "unknown"
    sentiment: str = "neutral"

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "intent": self.intent,
            "sentiment": self.sentiment,
        }


@dataclass
class BotResponse:
    """Encapsulates a bot reply with metadata."""
    text: str
    intent: str = "unknown"
    confidence: float = 1.0
    should_exit: bool = False
    extras: dict = field(default_factory=dict)


@dataclass
class TodoItem:
    """A single to-do entry."""
    id: int
    text: str
    done: bool = False
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)

    def __str__(self) -> str:
        status = Color.success("✓") if self.done else Color.dim("○")
        label = Color.dim(self.text) if self.done else self.text
        return f"  [{status}] #{self.id}  {label}"


# ══════════════════════════════════════════════════════════════════════════════
#  SENTIMENT ANALYZER
# ══════════════════════════════════════════════════════════════════════════════

class SentimentAnalyzer:
    """Lightweight lexicon-based sentiment scorer."""

    POSITIVE_WORDS = {
        "good", "great", "awesome", "excellent", "happy", "love", "like",
        "fantastic", "wonderful", "amazing", "nice", "best", "cool", "fun",
        "enjoy", "pleased", "glad", "thanks", "thank", "helpful", "perfect",
        "brilliant", "superb", "beautiful", "joy", "excited", "positive",
    }

    NEGATIVE_WORDS = {
        "bad", "terrible", "awful", "hate", "dislike", "worst", "horrible",
        "annoying", "boring", "useless", "stupid", "dumb", "ugly", "sad",
        "angry", "frustrated", "disappointed", "wrong", "error", "broken",
        "problem", "issue", "fail", "failed", "crash", "confusing",
    }

    INTENSIFIERS = {"very", "really", "so", "extremely", "super", "quite"}
    NEGATIONS    = {"not", "no", "never", "don't", "doesn't", "isn't", "won't"}

    def analyze(self, text: str) -> str:
        tokens = re.findall(r"\b\w+\b", text.lower())
        score = 0
        negate = False
        for i, token in enumerate(tokens):
            if token in self.NEGATIONS:
                negate = True
                continue
            multiplier = 1.5 if (i > 0 and tokens[i - 1] in self.INTENSIFIERS) else 1.0
            if token in self.POSITIVE_WORDS:
                score += (1 * multiplier) * (-1 if negate else 1)
            elif token in self.NEGATIVE_WORDS:
                score -= (1 * multiplier) * (-1 if negate else 1)
            negate = False

        if score > 0.5:
            return "positive"
        if score < -0.5:
            return "negative"
        return "neutral"


# ══════════════════════════════════════════════════════════════════════════════
#  MATH EXPRESSION EVALUATOR  (no eval / no exec)
# ══════════════════════════════════════════════════════════════════════════════

class MathEvaluator:
    """
    Recursive-descent parser for safe arithmetic expressions.
    Supports: + - * / ** % parentheses, sqrt(), abs(), sin(), cos(), tan(),
              log(), ceil(), floor(), pi, e.
    """

    CONSTANTS = {"pi": math.pi, "e": math.e}
    FUNCTIONS = {
        "sqrt":  math.sqrt,
        "abs":   abs,
        "sin":   math.sin,
        "cos":   math.cos,
        "tan":   math.tan,
        "log":   math.log,
        "log10": math.log10,
        "ceil":  math.ceil,
        "floor": math.floor,
        "round": round,
    }

    def evaluate(self, expression: str) -> float:
        self._tokens = self._tokenize(expression)
        self._pos = 0
        result = self._parse_expr()
        if self._pos < len(self._tokens):
            raise ValueError(f"Unexpected token: {self._tokens[self._pos]}")
        return result

    def _tokenize(self, expr: str) -> list:
        token_pattern = re.compile(
            r"\s*(?:"
            r"(\d+\.?\d*)"        # number
            r"|([a-zA-Z_]\w*)"    # identifier
            r"|(\*\*|[+\-*/%()]))" # operators and parens
        )
        tokens = []
        for m in token_pattern.finditer(expr):
            if m.group(1):
                tokens.append(("NUM", float(m.group(1))))
            elif m.group(2):
                tokens.append(("ID", m.group(2)))
            elif m.group(3):
                tokens.append(("OP", m.group(3)))
        return tokens

    def _peek(self) -> Optional[tuple]:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _consume(self) -> tuple:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _parse_expr(self) -> float:
        return self._parse_additive()

    def _parse_additive(self) -> float:
        left = self._parse_multiplicative()
        while self._peek() and self._peek() == ("OP", "+") or \
              self._peek() == ("OP", "-"):
            op = self._consume()[1]
            right = self._parse_multiplicative()
            left = left + right if op == "+" else left - right
        return left

    def _parse_multiplicative(self) -> float:
        left = self._parse_power()
        while self._peek() and self._peek()[0] == "OP" and \
              self._peek()[1] in ("*", "/", "%"):
            op = self._consume()[1]
            right = self._parse_power()
            if op == "*":
                left *= right
            elif op == "/":
                if right == 0:
                    raise ZeroDivisionError("Division by zero")
                left /= right
            else:
                left %= right
        return left

    def _parse_power(self) -> float:
        base = self._parse_unary()
        if self._peek() == ("OP", "**"):
            self._consume()
            exp = self._parse_power()
            return base ** exp
        return base

    def _parse_unary(self) -> float:
        if self._peek() == ("OP", "-"):
            self._consume()
            return -self._parse_primary()
        if self._peek() == ("OP", "+"):
            self._consume()
        return self._parse_primary()

    def _parse_primary(self) -> float:
        tok = self._peek()
        if tok is None:
            raise ValueError("Unexpected end of expression")

        if tok[0] == "NUM":
            self._consume()
            return tok[1]

        if tok[0] == "ID":
            name = tok[1]
            self._consume()
            if name in self.CONSTANTS:
                return self.CONSTANTS[name]
            if name in self.FUNCTIONS:
                if self._peek() != ("OP", "("):
                    raise ValueError(f"Expected '(' after function '{name}'")
                self._consume()  # (
                arg = self._parse_expr()
                if self._peek() != ("OP", ")"):
                    raise ValueError("Expected ')'")
                self._consume()  # )
                return self.FUNCTIONS[name](arg)
            raise ValueError(f"Unknown name: '{name}'")

        if tok == ("OP", "("):
            self._consume()
            val = self._parse_expr()
            if self._peek() != ("OP", ")"):
                raise ValueError("Missing closing parenthesis")
            self._consume()
            return val

        raise ValueError(f"Unexpected token: {tok}")


# ══════════════════════════════════════════════════════════════════════════════
#  UNIT CONVERTER
# ══════════════════════════════════════════════════════════════════════════════

class UnitConverter:
    """Converts between common units across multiple categories."""

    # All values are relative to a base unit
    LENGTH = {
        "m": 1.0, "meter": 1.0, "meters": 1.0,
        "km": 1000.0, "kilometer": 1000.0, "kilometers": 1000.0,
        "cm": 0.01, "centimeter": 0.01, "centimeters": 0.01,
        "mm": 0.001, "millimeter": 0.001, "millimeters": 0.001,
        "mi": 1609.344, "mile": 1609.344, "miles": 1609.344,
        "ft": 0.3048, "foot": 0.3048, "feet": 0.3048,
        "in": 0.0254, "inch": 0.0254, "inches": 0.0254,
        "yd": 0.9144, "yard": 0.9144, "yards": 0.9144,
    }

    WEIGHT = {
        "kg": 1.0, "kilogram": 1.0, "kilograms": 1.0,
        "g": 0.001, "gram": 0.001, "grams": 0.001,
        "mg": 0.000001, "milligram": 0.000001, "milligrams": 0.000001,
        "lb": 0.453592, "pound": 0.453592, "pounds": 0.453592,
        "oz": 0.0283495, "ounce": 0.0283495, "ounces": 0.0283495,
        "t": 1000.0, "ton": 1000.0, "tons": 1000.0,
    }

    SPEED = {
        "mps": 1.0, "m/s": 1.0,
        "kph": 1 / 3.6, "km/h": 1 / 3.6, "kmh": 1 / 3.6,
        "mph": 0.44704, "mi/h": 0.44704,
        "knot": 0.514444, "knots": 0.514444,
        "fps": 0.3048, "ft/s": 0.3048,
    }

    CATEGORIES = {"length": LENGTH, "weight": WEIGHT, "speed": SPEED}

    TEMP_PATTERN = re.compile(
        r"([\d.]+)\s*(celsius|fahrenheit|kelvin|c|f|k)\s+(?:to|in)\s+(celsius|fahrenheit|kelvin|c|f|k)",
        re.IGNORECASE,
    )

    def convert_temperature(self, value: float, from_unit: str, to_unit: str) -> float:
        alias = {"c": "celsius", "f": "fahrenheit", "k": "kelvin"}
        frm = alias.get(from_unit.lower(), from_unit.lower())
        to  = alias.get(to_unit.lower(), to_unit.lower())

        # Convert to Celsius first
        if frm == "celsius":
            celsius = value
        elif frm == "fahrenheit":
            celsius = (value - 32) * 5 / 9
        elif frm == "kelvin":
            celsius = value - 273.15
        else:
            raise ValueError(f"Unknown temperature unit: {frm}")

        # Convert Celsius to target
        if to == "celsius":
            return celsius
        if to == "fahrenheit":
            return celsius * 9 / 5 + 32
        if to == "kelvin":
            return celsius + 273.15
        raise ValueError(f"Unknown temperature unit: {to}")

    def parse_and_convert(self, text: str) -> Optional[str]:
        # Temperature
        m = self.TEMP_PATTERN.search(text)
        if m:
            val = float(m.group(1))
            result = self.convert_temperature(val, m.group(2), m.group(3))
            return f"{val} {m.group(2)} = {result:.4f} {m.group(3)}"

        # Other units
        pattern = re.compile(
            r"([\d.]+)\s+(\w+(?:/\w+)?)\s+(?:to|in)\s+(\w+(?:/\w+)?)",
            re.IGNORECASE,
        )
        m = pattern.search(text)
        if not m:
            return None

        val = float(m.group(1))
        from_u = m.group(2).lower()
        to_u   = m.group(3).lower()

        for cat_name, cat in self.CATEGORIES.items():
            if from_u in cat and to_u in cat:
                base = val * cat[from_u]
                result = base / cat[to_u]
                return f"{val} {from_u} = {result:.6g} {to_u}  ({cat_name})"

        return None


# ══════════════════════════════════════════════════════════════════════════════
#  TRIVIA QUIZ ENGINE
# ══════════════════════════════════════════════════════════════════════════════

TRIVIA_BANK: list[dict] = [
    {"q": "What is the capital of France?",            "a": "paris",       "hint": "City of Love"},
    {"q": "How many sides does a hexagon have?",       "a": "6",           "hint": "More than a pentagon"},
    {"q": "What is the chemical symbol for gold?",     "a": "au",          "hint": "From Latin 'aurum'"},
    {"q": "Who wrote 'Romeo and Juliet'?",             "a": "shakespeare", "hint": "An Elizabethan playwright"},
    {"q": "What planet is known as the Red Planet?",   "a": "mars",        "hint": "Named after the god of war"},
    {"q": "What is the largest ocean on Earth?",       "a": "pacific",     "hint": "It's bigger than all land combined"},
    {"q": "In what year did World War II end?",        "a": "1945",        "hint": "The mid-40s"},
    {"q": "What gas do plants absorb from the air?",   "a": "co2",         "hint": "Carbon ___"},
    {"q": "How many bones are in the adult human body?","a": "206",        "hint": "About 200"},
    {"q": "What is the speed of light (km/s)?",        "a": "299792",      "hint": "About 300,000 km/s"},
    {"q": "Who painted the Mona Lisa?",                "a": "da vinci",    "hint": "Italian Renaissance master"},
    {"q": "What is the smallest prime number?",        "a": "2",           "hint": "The only even prime"},
    {"q": "What language is spoken in Brazil?",        "a": "portuguese",  "hint": "Not Spanish!"},
    {"q": "How many continents are there?",            "a": "7",           "hint": "One more than 6"},
    {"q": "What is H2O commonly known as?",            "a": "water",       "hint": "You drink it every day"},
]


@dataclass
class QuizSession:
    questions: list[dict] = field(default_factory=list)
    current_index: int = 0
    score: int = 0
    hint_used: bool = False
    active: bool = False

    def start(self, count: int = 5) -> str:
        pool = random.sample(TRIVIA_BANK, min(count, len(TRIVIA_BANK)))
        self.questions = pool
        self.current_index = 0
        self.score = 0
        self.hint_used = False
        self.active = True
        return self._ask_current()

    def _ask_current(self) -> str:
        if self.current_index >= len(self.questions):
            return self._finish()
        q = self.questions[self.current_index]
        n = self.current_index + 1
        total = len(self.questions)
        return (
            f"\n  Question {n}/{total}\n"
            f"  {q['q']}\n"
            f"  (type your answer, or 'hint' for a clue, 'skip' to skip)"
        )

    def answer(self, text: str) -> str:
        if not self.active:
            return ""
        q = self.questions[self.current_index]

        if text.strip().lower() == "hint":
            self.hint_used = True
            return f"  Hint: {q['hint']}"

        if text.strip().lower() == "skip":
            self.current_index += 1
            self.hint_used = False
            return f"  Skipped! The answer was: {q['a']}\n" + self._ask_current()

        correct = q["a"].lower()
        user_ans = text.strip().lower()
        if user_ans == correct or correct in user_ans:
            points = 1 if not self.hint_used else 0
            self.score += points
            self.current_index += 1
            self.hint_used = False
            feedback = Color.success("  ✓ Correct!") + (
                " (no points — hint used)" if not points else f" +1 point"
            )
            return feedback + "\n" + self._ask_current()
        else:
            return Color.error(f"  ✗ Wrong!") + f" The answer was: {q['a']}\n" + self._ask_next()

    def _ask_next(self) -> str:
        self.current_index += 1
        self.hint_used = False
        return self._ask_current()

    def _finish(self) -> str:
        self.active = False
        total = len(self.questions)
        pct = int(self.score / total * 100)
        grade = (
            "🏆 Outstanding!" if pct == 100 else
            "🎉 Great job!"   if pct >= 80  else
            "👍 Not bad!"     if pct >= 60  else
            "📚 Keep practicing!"
        )
        return (
            f"\n  Quiz finished!\n"
            f"  Score: {self.score}/{total}  ({pct}%)\n"
            f"  {grade}"
        )


# ══════════════════════════════════════════════════════════════════════════════
#  TODO MANAGER
# ══════════════════════════════════════════════════════════════════════════════

class TodoManager:
    """In-session task list."""

    def __init__(self):
        self._items: list[TodoItem] = []
        self._next_id = 1

    def add(self, text: str) -> str:
        item = TodoItem(id=self._next_id, text=text.strip())
        self._items.append(item)
        self._next_id += 1
        return f"  Added task #{item.id}: {item.text}"

    def done(self, id_: int) -> str:
        for item in self._items:
            if item.id == id_:
                item.done = True
                return f"  Task #{id_} marked as done."
        return f"  Task #{id_} not found."

    def remove(self, id_: int) -> str:
        for i, item in enumerate(self._items):
            if item.id == id_:
                self._items.pop(i)
                return f"  Task #{id_} removed."
        return f"  Task #{id_} not found."

    def list_all(self) -> str:
        if not self._items:
            return "  No tasks yet. Add one with: todo add <task>"
        lines = ["\n  📋 Your Tasks:"]
        for item in self._items:
            lines.append(str(item))
        pending = sum(1 for i in self._items if not i.done)
        lines.append(f"\n  {pending} pending / {len(self._items)} total")
        return "\n".join(lines)

    def clear_done(self) -> str:
        before = len(self._items)
        self._items = [i for i in self._items if not i.done]
        removed = before - len(self._items)
        return f"  Cleared {removed} completed task(s)."

    def parse_command(self, text: str) -> str:
        text = text.strip()
        low = text.lower()

        if re.search(r"\btodo\s+list\b", low) or re.search(r"\bshow\s+tasks\b", low):
            return self.list_all()

        m = re.search(r"\btodo\s+add\s+(.+)", text, re.IGNORECASE)
        if m:
            return self.add(m.group(1))

        m = re.search(r"\btodo\s+done\s+(\d+)", low)
        if m:
            return self.done(int(m.group(1)))

        m = re.search(r"\btodo\s+remove\s+(\d+)", low)
        if m:
            return self.remove(int(m.group(1)))

        if re.search(r"\btodo\s+clear\b", low):
            return self.clear_done()

        return (
            "  Todo commands:\n"
            "    todo add <task>    - Add a new task\n"
            "    todo list          - Show all tasks\n"
            "    todo done <id>     - Mark task as done\n"
            "    todo remove <id>   - Remove a task\n"
            "    todo clear         - Remove all done tasks"
        )


# ══════════════════════════════════════════════════════════════════════════════
#  CONVERSATION MEMORY
# ══════════════════════════════════════════════════════════════════════════════

class ConversationMemory:
    """Stores the last N messages and exposes context helpers."""

    def __init__(self, max_turns: int = 20):
        self._history: list[Message] = []
        self._max_turns = max_turns
        self._user_name: Optional[str] = None

    def push(self, msg: Message) -> None:
        self._history.append(msg)
        if len(self._history) > self._max_turns * 2:
            self._history = self._history[-(self._max_turns * 2):]

    @property
    def user_name(self) -> Optional[str]:
        return self._user_name

    @user_name.setter
    def user_name(self, name: str) -> None:
        self._user_name = name.strip().title()

    def last_user_message(self) -> Optional[str]:
        for msg in reversed(self._history):
            if msg.role == "user":
                return msg.content
        return None

    def last_intent(self) -> str:
        for msg in reversed(self._history):
            if msg.role == "bot":
                return msg.intent
        return "unknown"

    def dominant_sentiment(self) -> str:
        sentiments = [m.sentiment for m in self._history if m.role == "user"]
        if not sentiments:
            return "neutral"
        from collections import Counter
        return Counter(sentiments).most_common(1)[0][0]

    def turn_count(self) -> int:
        return sum(1 for m in self._history if m.role == "user")

    def export_json(self) -> str:
        return json.dumps([m.to_dict() for m in self._history], indent=2)

    def stats(self) -> dict:
        user_msgs = [m for m in self._history if m.role == "user"]
        bot_msgs  = [m for m in self._history if m.role == "bot"]
        avg_len = (
            sum(len(m.content) for m in user_msgs) / len(user_msgs)
            if user_msgs else 0
        )
        return {
            "turns": len(user_msgs),
            "bot_responses": len(bot_msgs),
            "avg_input_length": round(avg_len, 1),
            "dominant_sentiment": self.dominant_sentiment(),
        }


# ══════════════════════════════════════════════════════════════════════════════
#  INTENT REGISTRY
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Intent:
    name: str
    patterns: list[str]           # regex patterns
    keywords: list[str]           # plain keyword fallback
    handler: Callable             # function(text, memory, **ctx) -> BotResponse
    priority: int = 0             # higher = checked first


class IntentRegistry:
    """Stores and matches intents by regex / keyword."""

    def __init__(self):
        self._intents: list[Intent] = []

    def register(self, intent: Intent) -> None:
        self._intents.append(intent)
        self._intents.sort(key=lambda i: -i.priority)

    def match(self, text: str) -> Optional[Intent]:
        low = text.lower()
        for intent in self._intents:
            for pat in intent.patterns:
                if re.search(pat, low):
                    return intent
            for kw in intent.keywords:
                if kw in low:
                    return intent
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  RESPONSE TEMPLATES
# ══════════════════════════════════════════════════════════════════════════════

GREET_RESPONSES = [
    "Hey there! How can I help you today?",
    "Hello! What's on your mind?",
    "Hi! Ready to chat — what can I do for you?",
    "Greetings! I'm PyBot. Ask me anything.",
]

FAREWELL_RESPONSES = [
    "Goodbye! It was great chatting with you. 👋",
    "See you next time! Take care.",
    "Bye! Come back whenever you need help.",
    "Farewell! Have a wonderful day. 🌟",
]

HOW_ARE_YOU_RESPONSES = [
    "I'm running great, all systems go!",
    "Doing well, thanks for asking! How about you?",
    "Fantastic! Just processed a few million tokens. You?",
    "Better than ever! What can I help with?",
]

JOKE_BANK = [
    ("Why do programmers prefer dark mode?", "Because light attracts bugs!"),
    ("What's a computer's favorite snack?", "Microchips!"),
    ("Why did the developer go broke?", "Because he used up all his cache."),
    ("What's an algorithm?", "A word used by programmers when they don't want to explain what they did."),
    ("Why do Java developers wear glasses?", "Because they can't C#!"),
    ("How many programmers does it take to change a light bulb?", "None — that's a hardware problem."),
    ("What do you call a fish without eyes?", "A fsh!"),
    ("Why was the math book sad?", "It had too many problems."),
]

QUOTE_BANK = [
    ("Talk is cheap. Show me the code.", "Linus Torvalds"),
    ("Any fool can write code that a computer can understand. Good programmers write code that humans can understand.", "Martin Fowler"),
    ("First, solve the problem. Then, write the code.", "John Johnson"),
    ("Experience is the name everyone gives to their mistakes.", "Oscar Wilde"),
    ("The best way to predict the future is to invent it.", "Alan Kay"),
    ("Simplicity is the soul of efficiency.", "Austin Freeman"),
    ("Code is like humor. When you have to explain it, it's bad.", "Cory House"),
    ("Make it work, make it right, make it fast.", "Kent Beck"),
]

FALLBACK_RESPONSES = [
    "Interesting — tell me more!",
    "I'm not sure I follow. Could you rephrase that?",
    "Hmm, I'm still learning. Could you say that differently?",
    "That's a bit beyond me right now. Try asking about math, time, weather, or tasks!",
    "I didn't quite catch that. Type 'help' to see what I can do.",
]


# ══════════════════════════════════════════════════════════════════════════════
#  INTENT HANDLERS
# ══════════════════════════════════════════════════════════════════════════════

def _handle_greet(text: str, memory: ConversationMemory, **_) -> BotResponse:
    name = memory.user_name
    greeting = random.choice(GREET_RESPONSES)
    if name:
        greeting = f"Welcome back, {name}! " + greeting
    return BotResponse(text=greeting, intent="greet")


def _handle_farewell(text: str, memory: ConversationMemory, **_) -> BotResponse:
    return BotResponse(
        text=random.choice(FAREWELL_RESPONSES),
        intent="farewell",
        should_exit=True,
    )


def _handle_how_are_you(text: str, memory: ConversationMemory, **_) -> BotResponse:
    return BotResponse(text=random.choice(HOW_ARE_YOU_RESPONSES), intent="how_are_you")


def _handle_name_query(text: str, memory: ConversationMemory, **_) -> BotResponse:
    return BotResponse(
        text="I'm PyBot v2.0, an advanced Python chatbot built for demonstration purposes.",
        intent="name_query",
    )


def _handle_set_name(text: str, memory: ConversationMemory, **_) -> BotResponse:
    m = re.search(r"(?:my name is|call me|i am|i'm)\s+([a-zA-Z]+)", text, re.IGNORECASE)
    if m:
        memory.user_name = m.group(1)
        return BotResponse(
            text=f"Nice to meet you, {memory.user_name}! I'll remember your name.",
            intent="set_name",
        )
    return BotResponse(text="What should I call you?", intent="set_name")


def _handle_time(text: str, memory: ConversationMemory, **_) -> BotResponse:
    now = datetime.datetime.now()
    return BotResponse(
        text=f"Current time: {now.strftime('%H:%M:%S')}  ({now.strftime('%A, %B %d %Y')})",
        intent="time",
    )


def _handle_date(text: str, memory: ConversationMemory, **_) -> BotResponse:
    today = datetime.date.today()
    return BotResponse(
        text=f"Today is {today.strftime('%A, %B %d, %Y')}.",
        intent="date",
    )


def _handle_math(text: str, memory: ConversationMemory, **ctx) -> BotResponse:
    evaluator: MathEvaluator = ctx["math_evaluator"]
    # Strip leading "calculate / compute / what is" etc.
    expr = re.sub(
        r"(?i)^(calculate|compute|what\s+is|eval|=|math)\s*", "", text
    ).strip()
    try:
        result = evaluator.evaluate(expr)
        # Pretty-print integers
        if result == int(result):
            formatted = str(int(result))
        else:
            formatted = f"{result:.10g}"
        return BotResponse(text=f"  {expr} = {formatted}", intent="math")
    except Exception as exc:
        return BotResponse(
            text=f"  Could not evaluate expression: {exc}",
            intent="math",
        )


def _handle_convert(text: str, memory: ConversationMemory, **ctx) -> BotResponse:
    converter: UnitConverter = ctx["converter"]
    result = converter.parse_and_convert(text)
    if result:
        return BotResponse(text=f"  {result}", intent="convert")
    return BotResponse(
        text=(
            "  I couldn't parse that conversion.\n"
            "  Try:  10 km to miles\n"
            "        72 fahrenheit to celsius\n"
            "        5 kg to lb"
        ),
        intent="convert",
    )


def _handle_joke(text: str, memory: ConversationMemory, **_) -> BotResponse:
    setup, punchline = random.choice(JOKE_BANK)
    return BotResponse(text=f"  {setup}\n  ... {punchline}", intent="joke")


def _handle_quote(text: str, memory: ConversationMemory, **_) -> BotResponse:
    quote, author = random.choice(QUOTE_BANK)
    return BotResponse(text=f'  "{quote}"\n      — {author}', intent="quote")


def _handle_help(text: str, memory: ConversationMemory, **_) -> BotResponse:
    help_text = """
  ╔══════════════════════════════════════════════════╗
  ║             PyBot — What I Can Do                ║
  ╠══════════════════════════════════════════════════╣
  ║  🕐  time / date        Current time and date    ║
  ║  🔢  calculate <expr>   Math: 2**10, sqrt(144)   ║
  ║  📐  convert            10 km to miles           ║
  ║  📋  todo               Task list manager        ║
  ║  🧠  quiz               Start a trivia quiz      ║
  ║  😄  joke               Tell me a joke           ║
  ║  💬  quote              Inspirational quote      ║
  ║  📊  stats              Session statistics       ║
  ║  💾  history            Export chat history      ║
  ║  🚪  bye / exit         End the conversation     ║
  ╚══════════════════════════════════════════════════╝
"""
    return BotResponse(text=help_text, intent="help")


def _handle_stats(text: str, memory: ConversationMemory, **_) -> BotResponse:
    s = memory.stats()
    lines = [
        "\n  📊 Session Statistics",
        f"  Turns          : {s['turns']}",
        f"  Bot responses  : {s['bot_responses']}",
        f"  Avg input len  : {s['avg_input_length']} chars",
        f"  Your mood      : {s['dominant_sentiment']}",
    ]
    if memory.user_name:
        lines.insert(1, f"  User           : {memory.user_name}")
    return BotResponse(text="\n".join(lines), intent="stats")


def _handle_history(text: str, memory: ConversationMemory, **_) -> BotResponse:
    path = "chat_history.json"
    with open(path, "w", encoding="utf-8") as f:
        f.write(memory.export_json())
    return BotResponse(
        text=f"  Chat history exported to '{path}' ({memory.turn_count()} turns).",
        intent="history",
    )


def _handle_weather(text: str, memory: ConversationMemory, **_) -> BotResponse:
    return BotResponse(
        text=(
            "  I don't have live weather data (no internet access),\n"
            "  but I can convert temperatures for you!\n"
            "  Try: 25 celsius to fahrenheit"
        ),
        intent="weather",
    )


def _handle_sentiment_response(text: str, memory: ConversationMemory, **_) -> BotResponse:
    sentiment = memory.dominant_sentiment()
    if sentiment == "positive":
        reply = "I'm glad you're feeling positive! Keep it up 😊"
    elif sentiment == "negative":
        reply = "I'm sorry to hear things aren't great. I'm here to help!"
    else:
        reply = "I'm picking up a calm vibe. What's on your mind?"
    return BotResponse(text=reply, intent="sentiment_check")


# ══════════════════════════════════════════════════════════════════════════════
#  CHATBOT ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class ChatBot:
    """
    Core engine that wires together all components:
    memory, intents, quiz, todo, math, converter, sentiment.
    """

    VERSION = "2.0.0"

    def __init__(self, typing_delay: bool = True):
        self.memory       = ConversationMemory(max_turns=30)
        self.sentiment    = SentimentAnalyzer()
        self.math_eval    = MathEvaluator()
        self.converter    = UnitConverter()
        self.quiz         = QuizSession()
        self.todo         = TodoManager()
        self.registry     = IntentRegistry()
        self.typing_delay = typing_delay
        self._register_intents()

    # ── Intent Registration ──────────────────────────────────────────────────

    def _register_intents(self) -> None:
        intents = [
            Intent("greet",     [r"\b(hi|hello|hey|howdy|greetings|sup)\b"],
                   ["salam", "yo", "good morning", "good evening", "good afternoon"],
                   _handle_greet, priority=10),

            Intent("farewell",  [r"\b(bye|goodbye|exit|quit|farewell|see\s+you|cya)\b"],
                   ["quit", "leave", "close", "end chat"],
                   _handle_farewell, priority=10),

            Intent("how_are_you", [r"\bhow\s+are\s+you\b", r"\byou\s+doing\b", r"\byou\s+ok\b"],
                   ["how r u", "how're you", "you alright"],
                   _handle_how_are_you, priority=8),

            Intent("set_name",  [r"\bmy\s+name\s+is\b", r"\bcall\s+me\b", r"\bi\s+am\b", r"\bi'm\b(?=\s+[a-z]+)"],
                   [],
                   _handle_set_name, priority=9),

            Intent("name_query",[r"\bwhat.*your\s+name\b", r"\bwho\s+are\s+you\b"],
                   ["your name", "are you a bot", "are you ai", "are you human"],
                   _handle_name_query, priority=8),

            Intent("time",      [r"\bwhat.*time\b", r"\bcurrent\s+time\b"],
                   ["what time", "tell me the time", "clock"],
                   _handle_time, priority=7),

            Intent("date",      [r"\bwhat.*date\b", r"\btoday.*date\b", r"\bwhat\s+day\b"],
                   ["today's date", "what day is it", "current date"],
                   _handle_date, priority=7),

            Intent("math",      [r"\b(calculate|compute|eval|math)\b",
                                  r"[\d.]+\s*[\+\-\*\/\^%]\s*[\d.(]"],
                   ["square root", "sqrt", "what is 2", "result of"],
                   _handle_math, priority=9),

            Intent("convert",   [r"\b\d+\.?\d*\s+\w+\s+(to|in)\s+\w+"],
                   ["convert", "how many", "how much is"],
                   _handle_convert, priority=8),

            Intent("joke",      [r"\btell.*joke\b", r"\bfunny\b"],
                   ["joke", "make me laugh", "humor me"],
                   _handle_joke, priority=6),

            Intent("quote",     [r"\b(quote|inspire|motivation)\b"],
                   ["quote", "wisdom", "inspire me", "motivate me"],
                   _handle_quote, priority=6),

            Intent("help",      [r"\bhelp\b", r"\bwhat\s+can\s+you\s+do\b"],
                   ["commands", "usage", "guide", "options"],
                   _handle_help, priority=10),

            Intent("stats",     [r"\b(stats|statistics|session)\b"],
                   ["my stats", "session info"],
                   _handle_stats, priority=7),

            Intent("history",   [r"\b(history|export|save\s+chat)\b"],
                   ["save history", "export chat", "download history"],
                   _handle_history, priority=7),

            Intent("weather",   [r"\b(weather|temperature|forecast)\b"],
                   ["weather today", "is it raining"],
                   _handle_weather, priority=6),

            Intent("sentiment_check", [r"\bhow.*i.*feel\b", r"\bmy\s+mood\b"],
                   ["how do i feel", "what's my mood"],
                   _handle_sentiment_response, priority=5),
        ]
        for intent in intents:
            self.registry.register(intent)

    # ── Processing ───────────────────────────────────────────────────────────

    def process(self, user_input: str) -> BotResponse:
        text = user_input.strip()

        # Empty input
        if not text:
            return BotResponse(text="(Please type something — or 'help' for options.)")

        # Detect sentiment for memory
        sentiment = self.sentiment.analyze(text)

        # Save user message
        user_msg = Message(role="user", content=text, sentiment=sentiment)
        self.memory.push(user_msg)

        # Quiz mode intercepts all input
        if self.quiz.active:
            reply_text = self.quiz.answer(text)
            response = BotResponse(text=reply_text, intent="quiz")
        # Todo commands
        elif re.search(r"\btodo\b|\bshow\s+tasks\b", text, re.IGNORECASE):
            reply_text = self.todo.parse_command(text)
            response = BotResponse(text=reply_text, intent="todo")
        # Quiz start
        elif re.search(r"\b(quiz|trivia|test\s+me)\b", text, re.IGNORECASE):
            m = re.search(r"(\d+)\s+question", text, re.IGNORECASE)
            count = int(m.group(1)) if m else 5
            reply_text = self.quiz.start(count)
            response = BotResponse(text=reply_text, intent="quiz")
        else:
            # Match intent
            intent = self.registry.match(text)
            ctx = {
                "math_evaluator": self.math_eval,
                "converter":      self.converter,
            }
            if intent:
                response = intent.handler(text, self.memory, **ctx)
            else:
                response = BotResponse(
                    text=random.choice(FALLBACK_RESPONSES),
                    intent="fallback",
                    confidence=0.1,
                )

        # Save bot message
        bot_msg = Message(role="bot", content=response.text, intent=response.intent)
        self.memory.push(bot_msg)

        return response

    # ── Output Helpers ───────────────────────────────────────────────────────

    def _type_out(self, text: str) -> None:
        """Simulate typing with a small delay."""
        if not self.typing_delay:
            print(Color.bot(f"Bot: {text}\n"))
            return
        print(Color.wrap("Bot: ", Color.CYAN, Color.BOLD), end="", flush=True)
        for char in text:
            print(Color.cyan_char(char) if hasattr(Color, "cyan_char") else char,
                  end="", flush=True)
            time.sleep(0.008)
        print()

    def print_response(self, response: BotResponse) -> None:
        prefix = Color.wrap("Bot: ", Color.CYAN, Color.BOLD)
        print(prefix + Color.bot(response.text) + "\n")

    # ── Main Loop ────────────────────────────────────────────────────────────

    def run(self) -> None:
        self._print_banner()
        while True:
            try:
                user_input = input(Color.user_prompt())
            except (EOFError, KeyboardInterrupt):
                print()
                self.print_response(BotResponse(
                    text="Session interrupted. Goodbye! 👋",
                    should_exit=True,
                ))
                break

            response = self.process(user_input)
            self.print_response(response)

            if response.should_exit:
                self._print_footer()
                break

    def _print_banner(self) -> None:
        banner = f"""
{Color.wrap('╔══════════════════════════════════════════════════╗', Color.CYAN)}
{Color.wrap('║', Color.CYAN)}  {Color.wrap('PyBot  v' + self.VERSION, Color.BOLD, Color.WHITE)}  —  Advanced Python Chatbot          {Color.wrap('║', Color.CYAN)}
{Color.wrap('║', Color.CYAN)}  Built with pure Python · No external deps         {Color.wrap('║', Color.CYAN)}
{Color.wrap('╚══════════════════════════════════════════════════╝', Color.CYAN)}
{Color.dim("  Type 'help' to see all commands.")}
"""
        print(banner)

   


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    # Allow --no-delay flag for CI / testing
    delay = "--no-delay" not in sys.argv
    bot = ChatBot(typing_delay=delay)
    bot.run()


if __name__ == "__main__":
    main()