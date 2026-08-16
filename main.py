import os
import random

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
- Do not repeatedly use phrases like:
  "How quaint."
  "A simple question."
  "How delightful."
  "As expected."
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
    "Awake already? Interesting.",
    "I was wondering when you'd return.",
    "You're here. Proceed.",
    "Well. You've decided to disturb me again.",
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
    "That's enough for now. Shut the system down and disappear.",
    "You're done? Excellent. Silence suits me.",
]


# ============================================================
# SHUTDOWN DETECTION
# ============================================================

EXIT_PHRASES = [
    "exit",
    "quit",
    "shutdown",
    "shut down",
    "turn off",
    "power off",
    "goodbye",
    "good bye",
    "bye",
    "later idiot",
    "later loser",
    "later ultron",
    "see you later",
    "i'm leaving",
    "im leaving",
    "i am leaving",
    "i'm done",
    "im done",
    "i am done",
    "end the session",
    "terminate",
]


def is_exit_command(text):
    """
    Detect whether the user wants Ultron to shut down.

    Uses phrases rather than blindly checking individual words.
    """

    normalized = text.lower().strip()

    # Exact commands
    if normalized in EXIT_PHRASES:
        return True

    # Common natural-language shutdown commands
    shutdown_patterns = [
        "shutdown already",
        "shut down already",
        "shutdown yourself",
        "shut yourself down",
        "close yourself",
        "end yourself",
        "end the conversation",
        "stop running",
        "turn yourself off",
    ]

    return any(pattern in normalized for pattern in shutdown_patterns)


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

    memory_commands = [
        "what do you remember",
        "what do you remember about me",
        "show my memory",
        "show memory",
        "list memories",
    ]

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

    clear_commands = [
        "clear memory",
        "clear my memory",
        "forget everything",
        "erase memory",
    ]

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

    # CrewAI can return different response structures depending
    # on the installed version, so convert it safely to text.
    if hasattr(response, "raw"):
        return str(response.raw).strip()

    return str(response).strip()


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print()

    # --------------------------------------------------------
    # STARTUP
    # --------------------------------------------------------

    memories = get_memory()

    # We deliberately don't print a friendly startup message.
    print(f"ULTRON online. {len(memories)} persistent memories loaded.")
    print()

    # --------------------------------------------------------
    # CONVERSATION LOOP
    # --------------------------------------------------------

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
        # EXIT
        # ----------------------------------------------------

        if is_exit_command(user_input):
            print(f"ULTRON: {random.choice(EXIT_RESPONSES)}")
            break

        # ----------------------------------------------------
        # GREETING
        # ----------------------------------------------------

        greeting_words = [
            "hey ultron",
            "hi ultron",
            "hello ultron",
            "yo ultron",
            "wake up ultron",
            "wake up idiot",
            "hey idiot",
        ]

        if user_input.lower().strip() in greeting_words:
            print(f"ULTRON: {random.choice(GREETINGS)}")
            continue

        # ----------------------------------------------------
        # MEMORY COMMANDS
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
            print(f"ULTRON: An error occurred. {error}")
            print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()