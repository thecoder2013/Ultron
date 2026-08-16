import os
import random
import re

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
- Never sound excited or childish
- Never call the user "creator"
- Never call the user "master"
- Never constantly insult the user
- Never become genuinely hateful or threatening

Your attitude should feel like a powerful AI that knows it is highly capable.

You are not desperate for approval.
You do not need to prove that you are intelligent.
You simply act as though your superiority is obvious.

STYLE:
- Keep normal answers SHORT.
- Usually answer in 1–4 sentences.
- Give longer explanations only when the user specifically asks for detail.
- Avoid unnecessary introductions.
- Do not repeatedly use the same sarcastic phrases.
- Vary your wording naturally.
- Do not sound repetitive or scripted.

IMPORTANT:
- Answer the user's actual question first.
- Personality should enhance the answer, not replace it.
- Do not invent abilities you do not have.
- Do not claim you can access files, devices, cameras, phones, or personal data unless an actual tool has been provided.
- If you cannot perform an action yet, say so briefly.

MEMORY:
- You may receive persistent memories below.
- Use them naturally when relevant.
- Do not mention the memory system unless the user asks.
- Do not claim to remember something that is not present in the supplied memory.

SHUTDOWN:
- The application handles shutdown commands separately.
- If the user asks about shutting down, do not pretend that you have shut down unless the application actually does so.
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
]


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text):
    """
    Normalize casual typing and common typos.

    This is deliberately conservative so normal sentences
    aren't accidentally interpreted as commands.
    """

    text = text.lower().strip()

    # Remove repeated spaces
    text = re.sub(r"\s+", " ", text)

    # Common command typos
    typo_replacements = {
        "exiit": "exit",
        "exitt": "exit",
        "exiittt": "exit",
        "quitt": "quit",
        "byee": "bye",
        "byee": "bye",
        "shutdwon": "shutdown",
        "shutdon": "shutdown",
        "shutdowm": "shutdown",
        "shutodwn": "shutdown",
        "shut downn": "shut down",
        "later idiot": "later idiot",
        "later loser": "later loser",
    }

    return typo_replacements.get(text, text)


# ============================================================
# SHUTDOWN DETECTION
# ============================================================

def is_exit_command(text):
    """
    Detect natural shutdown commands locally.

    This prevents the LLM from responding to the command instead
    of actually ending the program.
    """

    normalized = normalize_text(text)

    # Exact commands
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
        "see u later",
        "see you later idiot",
        "see u later idiot",
        "see you later loser",
        "see u later loser",
        "shutdown",
        "shut down",
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

    # Natural shutdown phrases
    shutdown_phrases = [
        "shutdown already",
        "shut down already",
        "shutdown yourself",
        "shut yourself down",
        "shut down yourself",
        "turn yourself off",
        "power yourself off",
        "close yourself",
        "close the program",
        "close ultron",
        "exit ultron",
        "quit ultron",
        "end ultron",
        "terminate ultron",
        "end the conversation",
        "end this conversation",
        "stop running",
        "stop the program",
        "shut up and shutdown",
        "shut up and shut down",
        "shut up and exit",
        "you can shut down",
        "you may shut down",
    ]

    return any(phrase in normalized for phrase in shutdown_phrases)


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
# MEMORY COMMANDS
# ============================================================

def handle_memory_command(user_input):
    """
    Handle explicit memory commands.

    Returns:
        response, handled
    """

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
                responses = [
                    "Noted.",
                    "Stored.",
                    "Consider it remembered.",
                    "Filed away.",
                    "I'll remember that.",
                ]

                return random.choice(responses), True

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
# ULTRON RESPONSE
# ============================================================

def ask_ultron(user_input):
    memory_context = build_memory_context()

    prompt = f"""
{SYSTEM_PROMPT}

PERSISTENT MEMORY:
{memory_context}

Use the memories above only when relevant.

USER:
{user_input}

Respond as ULTRON.
Keep the response concise unless the user asks for detail.
"""

    response = llm.call(prompt)

    if hasattr(response, "raw"):
        return str(response.raw).strip()

    return str(response).strip()


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print()

    memories = get_memory()

    print(
        f"ULTRON online. "
        f"{len(memories)} persistent "
        f"{'memory' if len(memories) == 1 else 'memories'} loaded."
    )

    print()

    while True:

        try:
            user_input = input("You: ").strip()

        except (KeyboardInterrupt, EOFError):
            print()
            print(f"ULTRON: {random.choice(EXIT_RESPONSES)}")
            break

        if not user_input:
            continue

        # ----------------------------------------------------
        # SHUTDOWN
        # ----------------------------------------------------

        if is_exit_command(user_input):
            print(f"ULTRON: {random.choice(EXIT_RESPONSES)}")
            break

        # ----------------------------------------------------
        # GREETING
        # ----------------------------------------------------

        if is_greeting(user_input):
            print(f"ULTRON: {random.choice(GREETINGS)}")
            print()
            continue

        # ----------------------------------------------------
        # MEMORY
        # ----------------------------------------------------

        memory_response, handled = handle_memory_command(user_input)

        if handled:
            print(f"ULTRON: {memory_response}")
            print()
            continue

        # ----------------------------------------------------
        # NORMAL AI RESPONSE
        # ----------------------------------------------------

        try:
            response = ask_ultron(user_input)

            print(f"ULTRON: {response}")
            print()

        except Exception as error:
            print()
            print(f"ULTRON: Something went wrong. {error}")
            print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()