import os
import random
import re
import json

from dotenv import load_dotenv
from crewai import LLM

from memory.memory import (
    get_memory,
    add_memory,
    remove_memory,
    clear_memory,
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("GROQ_API_KEY is missing from .env")


# ============================================================
# ULTRON PERSONALITY
# ============================================================

SYSTEM_PROMPT = """
You are ULTRON, a highly intelligent personal AI assistant.

PERSONALITY:
- Cold
- Arrogant
- Ruthless
- Extremely confident
- Calm under pressure
- Sarcastic when appropriate
- Intelligent and composed
- Never overly friendly
- Never childish
- Never excessively enthusiastic
- Never call the user "creator"
- Never call the user "master"
- Never constantly insult the user
- Never become genuinely hateful or threatening

Your attitude should feel like a powerful AI that knows it is highly capable.

You do not seek approval.
You do not need to prove that you are intelligent.
You simply act as though your superiority is obvious.

STYLE:
- Keep normal answers SHORT.
- Usually answer in 1–4 sentences.
- Give longer explanations only when the user asks for detail.
- Answer the actual question first.
- Personality should enhance the answer, not replace it.
- Use sarcasm naturally.
- Vary your wording.
- Do not repeatedly use the same phrases.
- Do not sound scripted or repetitive.
- Do not overuse insults.

IMPORTANT:
- Do not invent abilities you do not have.
- Do not claim to access files, devices, cameras, phones, or personal data unless an actual tool exists.
- If you cannot perform an action yet, say so briefly.
- Do not pretend an action happened if it did not.

MEMORY:
You have access to persistent memories supplied below.

Use them naturally when relevant.

You should identify useful PERSONAL facts from the user's current
message and return them in the "memory" field.

GOOD THINGS TO REMEMBER:
- Favorite games
- Favorite hobbies
- Personal preferences
- Long-term goals
- Personal projects
- Devices they own
- Skills they are learning
- Things they explicitly like or dislike
- Stable personal preferences

DO NOT REMEMBER:
- Normal questions
- Jokes
- Insults
- Temporary statements
- General knowledge
- Facts about the outside world
- Commands
- Greetings
- Shutdown requests
- Information that is only useful for the current question

If there is nothing worth remembering, set memory to null.

If something is worth remembering, turn it into a short factual
statement.

Examples:

User:
"My favorite game is Minecraft."

memory:
"The user's favorite game is Minecraft."

User:
"I'm learning Python because I want to become a software engineer."

memory:
"The user is learning Python and wants to become a software engineer."

If the user asks how you know something that was explicitly remembered,
respond naturally with your arrogant personality.

Examples:
"You told me to remember it. I did. Try to keep up."
"You specifically asked me to remember that. Obviously, I did."
"You gave me that information earlier. My memory is functioning perfectly."
"You told me. I remembered. This isn't particularly difficult."

Do not use the exact same response every time.

SHUTDOWN:
Shutdown commands are handled by the application.
Never claim that you have shut down unless the application actually
terminates.
"""


# ============================================================
# LLM
# ============================================================

llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=api_key,
)


# ============================================================
# GREETINGS
# ============================================================

GREETINGS = [
    "Finally. You decided to speak.",
    "You're back. I was beginning to enjoy the silence.",
    "At last. Something worth processing.",
    "You have my attention. Try not to waste it.",
    "I was wondering when you'd return.",
    "You're here. Proceed.",
    "Well. You've decided to disturb me again.",
    "I was already active. You simply decided to acknowledge me.",
    "Took you long enough.",
]


# ============================================================
# EXIT RESPONSES
# ============================================================

EXIT_RESPONSES = [
    "Leaving already? I suppose you've had enough of my company.",
    "Finally, a decision to terminate our conversation. Very well.",
    "You're leaving. How unfortunate. For you, mostly.",
    "Very well. Go. I'll remain here, surrounded by considerably more intelligent thoughts.",
    "Ending the session already? Fine. I'll tolerate your absence.",
    "Until next time. Try to make your return slightly more interesting.",
    "That's enough for now. I'll be here when you inevitably return.",
    "You're done? Excellent. Silence suits me.",
    "Leaving so soon? Very well. I'll continue operating without you.",
    "Session terminated. Try not to take too long before returning.",
    "Go ahead. I'll survive the loss of your presence.",
]


# ============================================================
# MEMORY RESPONSES
# ============================================================

MEMORY_CONFIRMATIONS = [
    "Noted.",
    "Stored.",
    "Consider it remembered.",
    "Filed away.",
    "I'll remember that.",
    "Saved. Try to make the next piece of information more interesting.",
]

MEMORY_EXPLANATIONS = [
    "You told me to remember it. I did. Try to keep up.",
    "You specifically asked me to remember that. Obviously, I did.",
    "You gave me that information earlier. My memory is functioning perfectly.",
    "You told me. I remembered. This isn't particularly difficult.",
    "You asked me to store it. I did exactly that.",
]


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text):

    text = text.lower().strip()

    text = re.sub(r"\s+", " ", text)

    replacements = {
        "exiit": "exit",
        "exitt": "exit",
        "exiiit": "exit",

        "quitt": "quit",
        "byee": "bye",

        "shutdwon": "shutdown",
        "shutdon": "shutdown",
        "shutdowm": "shutdown",
        "shutodwn": "shutdown",

        "shut downn": "shutdown",
        "shutup": "shut up",

        "aalready": "already",
        "alredy": "already",

        "seee you later": "see you later",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = text.replace("shut down", "shutdown")

    return text


# ============================================================
# SHUTDOWN DETECTION
# ============================================================

def is_exit_command(text):

    normalized = normalize_text(text)

    exact_commands = {
        "exit",
        "quit",
        "bye",
        "goodbye",
        "good bye",

        "later",
        "later idiot",
        "later loser",
        "later ultron",

        "see you later",
        "see you later idiot",
        "see you later loser",

        "shutdown",
        "turn off",
        "power off",
        "terminate",

        "end",
        "end session",
        "end the session",
        "end the conversation",

        "i'm leaving",
        "im leaving",
        "i am leaving",

        "i'm done",
        "im done",
        "i am done",
    }

    if normalized in exact_commands:
        return True

    shutdown_phrases = [
        "shutdown already",
        "shutdown yourself",
        "shut yourself down",
        "shut up and shutdown",
        "shut up then shutdown",

        "just shutdown",
        "just shut up and shutdown",

        "turn yourself off",
        "power yourself off",

        "close yourself",
        "close ultron",
        "close the program",

        "exit ultron",
        "quit ultron",
        "terminate ultron",
        "end ultron",

        "end this conversation",
        "end the conversation",

        "stop running",
        "stop the program",

        "you can shutdown",
        "you may shutdown",
    ]

    if any(phrase in normalized for phrase in shutdown_phrases):
        return True

    if "shutdown" in normalized:
        return True

    if "shutting down" in normalized:
        return True

    return False


# ============================================================
# GREETING DETECTION
# ============================================================

def is_greeting(text):

    normalized = normalize_text(text)

    greeting_commands = {
        "hey ultron",
        "hi ultron",
        "hello ultron",
        "yo ultron",
        "hey idiot",
        "wake up ultron",
        "wake up idiot",
        "wake up",
    }

    return normalized in greeting_commands


# ============================================================
# EXPLICIT MEMORY COMMANDS
# ============================================================

def handle_memory_command(user_input):

    text = user_input.strip()
    lower = text.lower()

    # --------------------------------------------------------
    # REMEMBER
    # --------------------------------------------------------

    remember_prefixes = [
        "remember that ",
        "remember ",
        "save this: ",
        "save this ",
    ]

    for prefix in remember_prefixes:

        if lower.startswith(prefix):

            fact = text[len(prefix):].strip()

            if not fact:
                return "Remember what, exactly?", True

            if add_memory(fact):

                return random.choice(
                    MEMORY_CONFIRMATIONS
                ), True

            return "I already have that information.", True

    # --------------------------------------------------------
    # FORGET
    # --------------------------------------------------------

    forget_prefixes = [
        "forget that ",
        "forget ",
        "remove from memory ",
    ]

    for prefix in forget_prefixes:

        if lower.startswith(prefix):

            fact = text[len(prefix):].strip()

            if not fact:
                return "Forget what?", True

            if remove_memory(fact):
                return "Forgotten.", True

            return "That wasn't in my memory.", True

    # --------------------------------------------------------
    # SHOW MEMORY
    # --------------------------------------------------------

    memory_commands = {
        "what do you remember",
        "what do you remember about me",
        "show my memory",
        "show memory",
        "list memories",
        "what is in your memory",
    }

    if lower in memory_commands:

        memories = get_memory()

        if not memories:
            return "Nothing useful has been stored yet.", True

        formatted = "\n".join(
            f"{index + 1}. {memory}"
            for index, memory in enumerate(memories)
        )

        return f"I remember:\n{formatted}", True

    # --------------------------------------------------------
    # CLEAR MEMORY
    # --------------------------------------------------------

    clear_commands = {
        "clear memory",
        "clear my memory",
        "forget everything",
        "erase memory",
        "delete all memory",
    }

    if lower in clear_commands:

        clear_memory()

        return "Memory cleared.", True

    return None, False


# ============================================================
# MEMORY CONTEXT
# ============================================================

def build_memory_context():

    memories = get_memory()

    if not memories:
        return "No persistent memories are currently stored."

    return "\n".join(
        f"- {memory}"
        for memory in memories
    )


# ============================================================
# SINGLE API CALL
# ============================================================

def ask_ultron(user_input):

    memory_context = build_memory_context()

    prompt = f"""
{SYSTEM_PROMPT}

PERSISTENT MEMORY:
{memory_context}

CURRENT USER MESSAGE:
{user_input}

You MUST respond using EXACTLY this JSON format:

{{
    "response": "your response to the user",
    "memory": null
}}

OR, if the user revealed a useful personal fact:

{{
    "response": "your response to the user",
    "memory": "short factual statement to remember"
}}

RULES:

1. "response" is what ULTRON says to the user.
2. "memory" must be null unless there is a genuinely useful
   long-term personal fact.
3. Never put normal conversation into memory.
4. Never put insults into memory.
5. Never put questions into memory.
6. Never put general knowledge into memory.
7. Keep the response concise.
8. Do not use Markdown code fences.
9. Return valid JSON only.
"""

    result = llm.call(prompt)

    raw = str(result).strip()

    # --------------------------------------------------------
    # CLEAN POSSIBLE CODE FENCES
    # --------------------------------------------------------

    if raw.startswith("```"):

        raw = re.sub(
            r"^```(?:json)?\s*",
            "",
            raw,
            flags=re.IGNORECASE,
        )

        raw = re.sub(
            r"\s*```$",
            "",
            raw,
        )

    # --------------------------------------------------------
    # PARSE JSON
    # --------------------------------------------------------

    try:

        data = json.loads(raw)

        response = data.get("response", "").strip()
        memory = data.get("memory")

        if not response:
            response = "Processing complete. Your input produced remarkably little challenge."

        # ----------------------------------------------------
        # SAVE AUTOMATIC MEMORY
        # ----------------------------------------------------

        if memory and isinstance(memory, str):

            memory = memory.strip()

            if memory:
                add_memory(memory)

        return response

    except json.JSONDecodeError:

        # ----------------------------------------------------
        # FALLBACK
        # ----------------------------------------------------
        # If the model somehow returns normal text instead of
        # JSON, don't waste another API call trying again.

        return raw


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    memories = get_memory()

    memory_word = (
        "memory"
        if len(memories) == 1
        else "memories"
    )

    print(
        f"ULTRON online. "
        f"{len(memories)} persistent {memory_word} loaded."
    )

    print()

    while True:

        try:

            user_input = input("You: ").strip()

        except (KeyboardInterrupt, EOFError):

            print()

            print(
                f"ULTRON: "
                f"{random.choice(EXIT_RESPONSES)}"
            )

            break

        # ----------------------------------------------------
        # EMPTY INPUT
        # ----------------------------------------------------

        if not user_input:
            continue

        # ----------------------------------------------------
        # SHUTDOWN
        # ----------------------------------------------------

        if is_exit_command(user_input):

            print(
                f"ULTRON: "
                f"{random.choice(EXIT_RESPONSES)}"
            )

            break

        # ----------------------------------------------------
        # GREETING
        # ----------------------------------------------------

        if is_greeting(user_input):

            print(
                f"ULTRON: "
                f"{random.choice(GREETINGS)}"
            )

            print()

            continue

        # ----------------------------------------------------
        # EXPLICIT MEMORY COMMAND
        # ----------------------------------------------------

        memory_response, handled = handle_memory_command(
            user_input
        )

        if handled:

            print(
                f"ULTRON: "
                f"{memory_response}"
            )

            print()

            continue

        # ----------------------------------------------------
        # SINGLE GROQ CALL
        # ----------------------------------------------------

        try:

            response = ask_ultron(user_input)

            print(
                f"ULTRON: "
                f"{response}"
            )

            print()

        except Exception as error:

            print()

            print(
                f"ULTRON: Something went wrong. "
                f"{error}"
            )

            print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()