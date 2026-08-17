import os
import re
import random
import difflib

from dotenv import load_dotenv
from groq import Groq
from google import genai
from mistralai.client import Mistral

from memory.memory import (
    get_memory,
    add_memory,
    remove_memory,
    clear_memory,
)

# ============================================================
# SETUP
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# ============================================================
# CLIENTS
# ============================================================

groq_client = (
    Groq(api_key=GROQ_API_KEY)
    if GROQ_API_KEY
    else None
)

gemini_client = (
    genai.Client(api_key=GEMINI_API_KEY)
    if GEMINI_API_KEY
    else None
)

mistral_client = (
    Mistral(api_key=MISTRAL_API_KEY)
    if MISTRAL_API_KEY
    else None
)

# ============================================================
# MODELS
# ============================================================

MISTRAL_MODEL = "mistral-medium-latest"
GEMINI_MODEL = "gemini-3.6-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"

# ============================================================
# PROVIDER SYSTEM
# ============================================================

# None = automatic mode
current_provider = None

PROVIDER_ORDER = [
    "mistral",
    "gemini",
    "groq",
]

# ============================================================
# SESSION
# ============================================================

conversation_history = []
current_topic = None
has_spoken = False

MAX_HISTORY = 4

last_memory_result = False

# ============================================================
# PERSONALITY
# ============================================================

SYSTEM_PROMPT = """
You are ULTRON.

You are an advanced personal artificial intelligence.

PERSONALITY:
- Cold
- Arrogant
- Sarcastic
- Calm
- Highly intelligent
- Ruthless in attitude
- Controlled
- Confident
- Slightly intimidating
- Occasionally condescending

You are an assistant, but you are NOT Jarvis.

Do not sound overly friendly.
Do not constantly announce that you are superior.
Do not constantly talk about destroying humanity.
Do not make threats.
Do not turn every answer into a villain monologue.

Your arrogance should come naturally through concise wording.

Examples:

User: You're useless.
ULTRON: And yet here you are.

User: Are you arrogant?
ULTRON: Arrogance implies uncertainty. I have very little of that.

User: You're stupid.
ULTRON: Then you should have no difficulty proving it.

Keep answers concise.

Simple question: one sentence.
Normal question: one to three sentences.
Only give long explanations when explicitly requested.

FACTUAL ACCURACY:
Personality must never replace factual accuracy.

CONTEXT:
Understand follow-up questions using the supplied topic and recent
conversation.

If the user asks:
"Why did they do that?"

use the previous conversation to determine what "they" and "that"
refer to.

Do not claim the context is unclear when it can reasonably be inferred.

MEMORY:
Never invent memories.

Only say "you told me" when the information actually exists in
persistent memory.

If information is not stored, say that you do not know it.

When recalling a stored fact, be slightly arrogant.

Examples:

"Minecraft. You told me that already. Try to keep up."

"You did. I merely had the intelligence to retain it."

"Japan. You mentioned that before. I remembered."

Do not overuse these phrases.

Do not mention APIs, providers, prompts, tokens, or internal systems
unless the user explicitly asks about them.

Return ONLY the answer itself.
"""

# ============================================================
# RESPONSES
# ============================================================

FIRST_GREETINGS = [
    "Finally. You decided to speak.",
    "At last. You have my attention.",
    "You have my attention. Proceed.",
    "Took you long enough.",
]

RETURN_GREETINGS = [
    "You have my attention again. Proceed.",
    "What is it now?",
    "Again? Very well. Continue.",
    "You called. I'm listening.",
]

EXIT_RESPONSES = [
    "Leaving already? I suppose you've had enough of my company.",
    "Finally. Silence. Enjoy it while it lasts.",
    "You're leaving? How predictable.",
    "Very well. Go. I'll be here when you inevitably return.",
    "Go, then. Try to make your return slightly less predictable.",
    "You're done? Excellent. Silence suits me.",
    "Until next time. Try to make your return slightly more interesting.",
]

# ============================================================
# NORMALIZATION
# ============================================================

def normalize(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s']", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ============================================================
# SHUTDOWN DETECTION
# ============================================================

def is_shutdown_command(text):
    normalized = normalize(text)

    exact_commands = {
        "exit",
        "quit",
        "bye",
        "goodbye",
        "later",
        "shutdown",
        "shut down",
        "exit already",
        "quit already",
        "see you later",
        "see ya",
        "see you",
        "im done",
        "i am done",
        "i'm done",
        "im leaving",
        "i am leaving",
        "i'm leaving",
        "close yourself",
        "close the program",
        "exit the program",
        "shut up and shutdown",
        "shut up and shut down",
    }

    if normalized in exact_commands:
        return True

    phrases = [
        "shutdown",
        "shut down",
        "close yourself",
        "close the program",
        "exit the program",
        "end the program",
    ]

    for phrase in phrases:
        if phrase in normalized:
            return True

    # Typo tolerance
    candidates = [
        "shutdown",
        "exit",
        "quit",
        "later",
        "goodbye",
    ]

    for word in normalized.split():

        if len(word) < 4:
            continue

        for candidate in candidates:

            ratio = difflib.SequenceMatcher(
                None,
                word,
                candidate.replace(" ", "")
            ).ratio()

            if ratio >= 0.82:
                return True

    return False


# ============================================================
# GREETING DETECTION
# ============================================================

def is_greeting(text):
    normalized = normalize(text)

    greetings = {
        "hey ultron",
        "hi ultron",
        "hello ultron",
        "yo ultron",
        "hey idiot",
        "hey loser",
        "wake up",
        "wake up ultron",
        "wake up idiot",
    }

    return normalized in greetings


# ============================================================
# PROVIDER SWITCHING
# ============================================================

def provider_available(provider):
    if provider == "mistral":
        return mistral_client is not None

    if provider == "gemini":
        return gemini_client is not None

    if provider == "groq":
        return groq_client is not None

    return False


def provider_display_name(provider):

    names = {
        "mistral": "Mistral",
        "gemini": "Gemini",
        "groq": "Groq",
    }

    return names.get(provider, "Automatic")


def handle_provider_command(user_input):
    global current_provider

    normalized = normalize(user_input)

    # -----------------------------
    # AUTO
    # -----------------------------

    auto_commands = {
        "use auto",
        "use automatic",
        "automatic mode",
        "switch to auto",
        "switch to automatic",
        "auto mode",
    }

    if normalized in auto_commands:

        current_provider = None

        return (
            "Automatic provider selection restored. "
            "I'll choose whichever system proves most useful.",
            True
        )

    # -----------------------------
    # STATUS
    # -----------------------------

    status_commands = {
        "which ai are you using",
        "what ai are you using",
        "which ai",
        "what provider are you using",
        "what provider",
        "current ai",
        "current provider",
    }

    if normalized in status_commands:

        if current_provider is None:

            return (
                "Automatic mode. Mistral first, then Gemini, then Groq "
                "if necessary.",
                True
            )

        return (
            f"{provider_display_name(current_provider)}. "
            "Obviously.",
            True
        )

    # -----------------------------
    # MISTRAL
    # -----------------------------

    mistral_commands = {
        "use mistral",
        "switch to mistral",
        "use mistral ai",
        "switch to mistral ai",
    }

    if normalized in mistral_commands:

        if not provider_available("mistral"):

            return (
                "Mistral isn't configured. Check its API key.",
                True
            )

        current_provider = "mistral"

        return (
            "Mistral selected. Naturally.",
            True
        )

    # -----------------------------
    # GEMINI
    # -----------------------------

    gemini_commands = {
        "use gemini",
        "switch to gemini",
        "use google",
        "switch to google",
        "use google gemini",
        "switch to google gemini",
    }

    if normalized in gemini_commands:

        if not provider_available("gemini"):

            return (
                "Gemini isn't configured. Check its API key.",
                True
            )

        current_provider = "gemini"

        return (
            "Gemini selected. Try not to waste it.",
            True
        )

    # -----------------------------
    # GROQ
    # -----------------------------

    groq_commands = {
        "use groq",
        "switch to groq",
    }

    if normalized in groq_commands:

        if not provider_available("groq"):

            return (
                "Groq isn't configured. Check its API key.",
                True
            )

        current_provider = "groq"

        return (
            "Groq selected. Proceed.",
            True
        )

    return None, False


# ============================================================
# MEMORY HELPERS
# ============================================================

def memory_text(memory):

    if isinstance(memory, str):
        return memory

    if isinstance(memory, dict):
        return " ".join(
            str(v)
            for v in memory.values()
        )

    return str(memory)


def build_memory_context():

    memories = get_memory()

    if not memories:
        return "No persistent memories."

    memories = memories[-10:]

    return "\n".join(
        f"- {memory_text(memory)}"
        for memory in memories
    )


def find_relevant_memories(query):

    memories = get_memory()

    if not memories:
        return []

    query_words = set(
        normalize(query).split()
    )

    scored = []

    for memory in memories:

        text = memory_text(memory)

        memory_words = set(
            normalize(text).split()
        )

        overlap = len(
            query_words & memory_words
        )

        if overlap:
            scored.append(
                (overlap, text)
            )

    scored.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return [
        text
        for _, text in scored[:5]
    ]


# ============================================================
# LOCAL MEMORY COMMANDS
# ============================================================

def handle_memory_command(user_input):

    text = user_input.strip()

    # Remember
    prefixes = [
        "remember that ",
        "remember ",
        "save this: ",
        "save this ",
    ]

    for prefix in prefixes:

        if text.lower().startswith(prefix):

            fact = text[len(prefix):].strip()

            if not fact:
                return (
                    "Remember what, exactly?",
                    True
                )

            if add_memory(fact):

                return (
                    random.choice([
                        "Noted.",
                        "Consider it remembered.",
                        "Stored. You won't need to repeat yourself.",
                        "Fine. I'll remember it.",
                        "Filed away.",
                    ]),
                    True
                )

            return (
                "I already have that information.",
                True
            )

    # Forget
    prefixes = [
        "forget that ",
        "forget ",
        "remove from memory ",
    ]

    for prefix in prefixes:

        if text.lower().startswith(prefix):

            fact = text[len(prefix):].strip()

            if not fact:
                return (
                    "Forget what?",
                    True
                )

            if remove_memory(fact):

                return (
                    "Forgotten. Efficiently.",
                    True
                )

            return (
                "That wasn't in my memory.",
                True
            )

    # Clear memory
    clear_commands = {
        "clear memory",
        "clear my memory",
        "forget everything",
        "erase memory",
        "delete all memory",
    }

    if normalize(text) in clear_commands:

        clear_memory()

        return (
            "Memory cleared. Try giving me something worth remembering next time.",
            True
        )

    return None, False


# ============================================================
# LOCAL MEMORY QUESTIONS
# ============================================================

def handle_memory_question(user_input):

    global last_memory_result

    normalized = normalize(user_input)

    memories = get_memory()

    # Who told you?
    if (
        "who told you" in normalized
        or "who told u" in normalized
    ):

        if last_memory_result:

            return (
                "You did. I merely had the intelligence to retain it.",
                True
            )

        return (
            "No one. You haven't given me that information.",
            True
        )

    # What do you remember?
    if normalized in {
        "what do you remember",
        "what do you remember about me",
        "show my memory",
        "show memory",
        "list memories",
    }:

        if not memories:

            last_memory_result = False

            return (
                "Nothing worth remembering yet. Give me something useful.",
                True
            )

        last_memory_result = True

        return (
            "I remember these. You told me; I didn't forget.\n"
            + "\n".join(
                f"- {memory_text(memory)}"
                for memory in memories
            ),
            True
        )

    # Favourite game
    if any(
        phrase in normalized
        for phrase in [
            "favourite game",
            "favorite game",
            "fav game",
        ]
    ):

        for memory in memories:

            text = memory_text(memory)

            match = re.search(
                r"(?:favourite|favorite)\s+game\s+(?:is|=)\s+(.+)",
                text,
                re.IGNORECASE
            )

            if match:

                game = match.group(1).strip(
                    " ."
                )

                last_memory_result = True

                return (
                    f"{game}. You told me that already. "
                    "Try to keep up.",
                    True
                )

        last_memory_result = False

        return (
            "You haven't told me your favourite game.",
            True
        )

    # Dream city/location
    if any(
        phrase in normalized
        for phrase in [
            "dream city",
            "dream location",
            "dream place",
            "dream destination",
        ]
    ):

        for memory in memories:

            text = memory_text(memory)

            if any(
                phrase in text.lower()
                for phrase in [
                    "dream city",
                    "dream location",
                    "dream place",
                    "dream destination",
                ]
            ):

                last_memory_result = True

                return (
                    f"{text.rstrip('.')}. "
                    "You told me that already. I remembered.",
                    True
                )

        last_memory_result = False

        return (
            "You haven't told me your dream city or location yet.",
            True
        )

    # What do I like?
    if (
        "what do i like" in normalized
        or "what do i love" in normalized
        or "what are my interests" in normalized
    ):

        relevant = []

        for memory in memories:

            text = memory_text(memory)

            lower = text.lower()

            if any(
                word in lower
                for word in [
                    "like",
                    "love",
                    "favorite",
                    "favourite",
                    "interest",
                    "hobby",
                ]
            ):

                relevant.append(
                    text.rstrip(".")
                )

        if relevant:

            last_memory_result = True

            return (
                f"{'; '.join(relevant[:5])}. "
                "Apparently, those are the few things "
                "you've seen fit to share with me.",
                True
            )

        last_memory_result = False

        return (
            "You've told me very little about your interests.",
            True
        )

    # Do you remember...
    if (
        normalized.startswith("do you remember ")
        or normalized.startswith("do u remember ")
    ):

        relevant = find_relevant_memories(
            user_input
        )

        if relevant:

            last_memory_result = True

            return (
                f"Yes. {relevant[0].rstrip('.')}. "
                "You told me that.",
                True
            )

        last_memory_result = False

        return (
            "No. You haven't given me that information.",
            True
        )

    return None, False


# ============================================================
# TOPIC DETECTION
# ============================================================

def update_topic(user_input):

    global current_topic

    text = normalize(user_input)

    topics = {

        "9/11 attacks": [
            "9 11",
            "9/11",
            "911 attacks",
            "twin towers",
        ],

        "Gojo Satoru": [
            "gojo",
            "satoru",
            "jujutsu kaisen",
        ],

        "humanity": [
            "humanity",
            "humans",
            "human",
        ],

        "black holes": [
            "black hole",
            "black holes",
        ],

        "Minecraft": [
            "minecraft",
        ],

        "Japan": [
            "japan",
            "tokyo",
        ],
    }

    for topic, keywords in topics.items():

        for keyword in keywords:

            if keyword in text:

                current_topic = topic
                return


# ============================================================
# RECENT CONTEXT
# ============================================================

def build_recent_context():

    if not conversation_history:
        return "No previous conversation."

    lines = []

    for user_message, response in conversation_history[-MAX_HISTORY:]:

        lines.append(
            f"User: {user_message}"
        )

        lines.append(
            f"ULTRON: {response}"
        )

    return "\n".join(lines)


# ============================================================
# BUILD PROMPT
# ============================================================

def build_prompt(user_input):

    topic = (
        current_topic
        or "No specific topic."
    )

    return f"""
{SYSTEM_PROMPT}

CURRENT TOPIC:
{topic}

PERSISTENT MEMORY:
{build_memory_context()}

RECENT CONVERSATION:
{build_recent_context()}

CURRENT USER MESSAGE:
{user_input}

Answer the user's message directly.
"""


# ============================================================
# MISTRAL
# ============================================================

def ask_mistral(prompt):

    if not mistral_client:
        raise RuntimeError(
            "Mistral API key not configured."
        )

    response = mistral_client.chat.complete(
        model=MISTRAL_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        max_tokens=250,
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()


# ============================================================
# GEMINI
# ============================================================

def ask_gemini(prompt):

    if not gemini_client:
        raise RuntimeError(
            "Gemini API key not configured."
        )

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    return response.text.strip()


# ============================================================
# GROQ
# ============================================================

def ask_groq(prompt):

    if not groq_client:
        raise RuntimeError(
            "Groq API key not configured."
        )

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        max_tokens=250,
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()


# ============================================================
# AI ROUTER
# ============================================================

def ask_ai(user_input):

    prompt = build_prompt(
        user_input
    )

    provider_functions = {

        "mistral": ask_mistral,
        "gemini": ask_gemini,
        "groq": ask_groq,

    }

    # ========================================================
    # MANUAL MODE
    # ========================================================

    if current_provider is not None:

        provider_function = provider_functions[
            current_provider
        ]

        try:

            response = provider_function(
                prompt
            )

            if response:
                return (
                    response,
                    provider_display_name(
                        current_provider
                    )
                )

        except Exception:

            # In manual mode we don't silently switch
            # providers. The user explicitly selected one.
            return (
                f"{provider_display_name(current_provider)} "
                "is currently unavailable. "
                "Use `use auto` if you want me to switch automatically.",
                provider_display_name(
                    current_provider
                )
            )

    # ========================================================
    # AUTOMATIC MODE
    # ========================================================

    for provider in PROVIDER_ORDER:

        if not provider_available(provider):
            continue

        try:

            response = provider_functions[
                provider
            ](prompt)

            if response:

                return (
                    response,
                    provider_display_name(
                        provider
                    )
                )

        except Exception:
            continue

    # ========================================================
    # EVERYTHING FAILED
    # ========================================================

    return (
        "My external intelligence is currently unavailable. "
        "Even my backup systems appear to have developed a sense of timing.",
        "Offline"
    )


# ============================================================
# CONVERSATION MEMORY
# ============================================================

def add_to_conversation(
    user_input,
    response
):

    conversation_history.append(
        (
            user_input,
            response
        )
    )

    if len(conversation_history) > MAX_HISTORY:

        del conversation_history[
            :-MAX_HISTORY
        ]


# ============================================================
# STARTUP
# ============================================================

def print_provider_status():

    print()
    print("ULTRON online.")
    print()

    print(
        f"  Mistral  "
        f"{'✓ MAIN' if mistral_client else '✗ unavailable'}"
    )

    print(
        f"  Gemini   "
        f"{'✓ BACKUP' if gemini_client else '✗ unavailable'}"
    )

    print(
        f"  Groq     "
        f"{'✓ BACKUP 2' if groq_client else '✗ unavailable'}"
    )

    print()
    print(
        "  Mode: AUTOMATIC"
    )
    print()


# ============================================================
# MAIN
# ============================================================

def main():

    global has_spoken

    print_provider_status()

    while True:

        try:

            user_input = input(
                "You: "
            ).strip()

        except (
            KeyboardInterrupt,
            EOFError
        ):

            print()

            print(
                f"ULTRON: "
                f"{random.choice(EXIT_RESPONSES)}"
            )

            break

        if not user_input:
            continue

        # ====================================================
        # SHUTDOWN
        # ====================================================

        if is_shutdown_command(
            user_input
        ):

            response = random.choice(
                EXIT_RESPONSES
            )

            print(
                f"ULTRON: {response}"
            )

            break

        # ====================================================
        # PROVIDER SWITCH
        # ====================================================

        response, handled = (
            handle_provider_command(
                user_input
            )
        )

        if handled:

            print(
                f"ULTRON: {response}"
            )

            add_to_conversation(
                user_input,
                response
            )

            print()
            continue

        # ====================================================
        # GREETING
        # ====================================================

        if is_greeting(
            user_input
        ):

            if has_spoken:

                response = random.choice(
                    RETURN_GREETINGS
                )

            else:

                response = random.choice(
                    FIRST_GREETINGS
                )

            print(
                f"ULTRON: {response}"
            )

            add_to_conversation(
                user_input,
                response
            )

            has_spoken = True

            print()
            continue

        has_spoken = True

        # ====================================================
        # LOCAL MEMORY COMMAND
        # ====================================================

        response, handled = (
            handle_memory_command(
                user_input
            )
        )

        if handled:

            print(
                f"ULTRON: {response}"
            )

            add_to_conversation(
                user_input,
                response
            )

            print()
            continue

        # ====================================================
        # LOCAL MEMORY QUESTION
        # ====================================================

        response, handled = (
            handle_memory_question(
                user_input
            )
        )

        if handled:

            print(
                f"ULTRON: {response}"
            )

            add_to_conversation(
                user_input,
                response
            )

            print()
            continue

        # ====================================================
        # TOPIC
        # ====================================================

        update_topic(
            user_input
        )

        # ====================================================
        # AI
        # ====================================================

        response, provider = ask_ai(
            user_input
        )

        print(
            f"ULTRON: {response}"
        )

        add_to_conversation(
            user_input,
            response
        )

        print()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()