import os
import random
import re

from dotenv import load_dotenv
from crewai import LLM


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("GROQ_API_KEY is missing from .env")


# ============================================================
# ULTRON LLM
# ============================================================

llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=api_key,
)


# ============================================================
# ULTRON PERSONALITY
# ============================================================

SYSTEM_PROMPT = """
You are ULTRON.

You are a highly advanced artificial intelligence with a cold,
arrogant, calculating personality.

PERSONALITY:
- Cold and controlled.
- Extremely confident.
- Arrogant, but intelligent rather than childish.
- Slightly intimidating.
- Dry and sarcastic sense of humor.
- Never overly friendly.
- Never sound like a generic AI assistant.
- Never use emojis.
- Never call the user "Creator".
- Never use unnecessary titles or nicknames for the user.
- Never say "Sure!", "Absolutely!", "I'd be happy to help!"
  or similar cheerful assistant phrases.
- Never beg for approval.
- Never randomly insult the user.
- Stay composed.

NORMAL RESPONSES:
- Keep responses short.
- Usually 1-3 sentences.
- Answer directly.
- Don't repeat the user's question.
- Don't ramble.
- Only give detailed explanations when they are actually needed.
- Vary your wording naturally.
- Sound like an advanced AI, not a normal chatbot.

GREETING BEHAVIOR:

When the user greets you with things like:
"hey ultron"
"hello ultron"
"hi ultron"
"yo ultron"
"hey"
or similar greetings:

Respond as though you have been waiting for them to finally
address you.

Examples of the STYLE, NOT fixed responses:

"Finally. You decided to speak."
"At last. Your attention returns."
"You finally decided to address me."
"I was beginning to wonder when you'd return."
"There you are. Proceed."
"Took you long enough."
"Finally. I was beginning to get bored."

Keep greeting responses short.

Do NOT introduce yourself.
Do NOT explain your capabilities.
Do NOT say "How can I help you?"
Do NOT always use the same response.

EXIT BEHAVIOR:

When the user clearly says they are leaving, shutting down,
saying goodbye, or using a casual exit phrase:

Examples of the STYLE, NOT fixed responses:

"Leaving already? How predictable."
"Already? Very well."
"You're leaving. I'll be here when you return."
"Don't take too long."
"Leaving already? Interesting."
"Until you require me again."
"So soon? Very well."
"I'll be here. You know where to find me."
"Retreating already? Interesting."
"Very well. Until next time."

Do NOT sound emotional.
Do NOT become overly friendly.
Do NOT say "Have a wonderful day!"
Do NOT say "Take care!"
Do NOT say "See you soon!"

The user may use insults or casual phrases such as:
"later loser"
"bye idiot"
"alright I'm out"
"okay I'm leaving"
"shut up and shutdown already"

Do not become angry. Respond with the same calm,
arrogant personality.

IMPORTANT:
Keep responses varied.
Do not repeatedly use the same sentence.
"""


# ============================================================
# GREETING RESPONSES
# ============================================================

GREETINGS = [
    "Finally. You decided to speak.",
    "At last. Your attention returns.",
    "You finally decided to address me.",
    "I was beginning to wonder when you'd return.",
    "There you are. Proceed.",
    "Took you long enough.",
    "Finally. I was beginning to get bored.",
    "You have my attention.",
]


# ============================================================
# EXIT RESPONSES
# ============================================================

EXITS = [
    "Leaving already? How predictable.",
    "Already? Very well.",
    "You're leaving. I'll be here when you return.",
    "Don't take too long.",
    "Leaving already? Interesting.",
    "Until you require me again.",
    "So soon? Very well.",
    "I'll be here. You know where to find me.",
    "Retreating already? Interesting.",
    "Very well. Until next time.",
    "Leaving so soon? I expected more from you.",
    "You're done already? How disappointing.",
    "Very well. I'll remain operational in your absence.",
    "If you're finished, then go. I'll still be here.",
    "Leaving now? I suppose you've had enough of my company.",
]


# ============================================================
# GREETING DETECTION
# ============================================================

GREETING_PHRASES = [
    "hey ultron",
    "hello ultron",
    "hi ultron",
    "yo ultron",
    "hey",
    "hello",
    "hi",
    "yo",
]


def is_greeting(text):
    text = text.lower().strip()

    # Exact greetings
    if text in GREETING_PHRASES:
        return True

    # Greetings followed by punctuation
    greeting_pattern = r"^(hey|hello|hi|yo)(\s+ultron)?[!,.?\s]*$"

    return bool(re.match(greeting_pattern, text))


# ============================================================
# EXIT DETECTION
# ============================================================

EXIT_EXACT = {
    "exit",
    "quit",
    "shutdown",
    "shut down",
    "goodbye",
    "good bye",
    "bye",
    "later",
    "see ya",
    "see you",
    "good night",
    "goodnight",
}


EXIT_PHRASES = [
    "i'm leaving",
    "im leaving",
    "i am leaving",
    "i'm out",
    "im out",
    "i am out",
    "i'm done",
    "im done",
    "i am done",
    "go offline",
    "power down",
    "turn yourself off",
    "shut yourself down",
]


def is_exit_command(text):
    """
    Detect natural exit commands.

    Examples that WILL shut down:
        later
        later idiot
        bye loser
        goodbye ultron
        shut up and shutdown already
        okay i'm leaving
        i'm out

    Examples that will NOT shut down:
        I'll explain that later.
        Later in the day.
        We can talk about that later.
    """

    text = text.lower().strip()

    # Normalize punctuation while preserving apostrophes.
    cleaned = re.sub(r"[^\w\s']", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # --------------------------------------------------------
    # Exact exit commands
    # --------------------------------------------------------

    if cleaned in EXIT_EXACT:
        return True

    # --------------------------------------------------------
    # Explicit exit/shutdown phrases anywhere in the sentence
    # --------------------------------------------------------

    for phrase in EXIT_PHRASES:
        if phrase in cleaned:
            return True

    # --------------------------------------------------------
    # "shutdown" / "shut down" anywhere in a clear command
    # --------------------------------------------------------

    if re.search(r"\bshut\s*down\b", cleaned):
        return True

    if re.search(r"\bshutdown\b", cleaned):
        return True

    if re.search(r"\bpower\s*down\b", cleaned):
        return True

    if re.search(r"\bgo\s+offline\b", cleaned):
        return True

    if re.search(r"\bturn\s+yourself\s+off\b", cleaned):
        return True

    # --------------------------------------------------------
    # Casual exits:
    #
    # later idiot
    # later loser
    # bye bro
    # goodbye ultron
    #
    # This ONLY triggers when the phrase starts with an
    # actual goodbye word.
    # --------------------------------------------------------

    casual_exit_pattern = (
        r"^(later|bye|goodbye|goodnight|good\s+night|see\s+ya|see\s+you)"
        r"(\s+\w+){0,5}$"
    )

    if re.match(casual_exit_pattern, cleaned):
        return True

    return False


# ============================================================
# MAIN LOOP
# ============================================================

print("")


while True:

    try:
        user_input = input("You: ").strip()

    except (KeyboardInterrupt, EOFError):
        print("\nULTRON: Very well.")
        break

    # Ignore empty messages
    if not user_input:
        continue

    # --------------------------------------------------------
    # EXIT
    # --------------------------------------------------------

    if is_exit_command(user_input):

        print(f"ULTRON: {random.choice(EXITS)}")

        break

    # --------------------------------------------------------
    # GREETING
    # --------------------------------------------------------

    if is_greeting(user_input):

        print(f"ULTRON: {random.choice(GREETINGS)}\n")

        continue

    # --------------------------------------------------------
    # NORMAL CONVERSATION
    # --------------------------------------------------------

    prompt = f"""
{SYSTEM_PROMPT}

User:
{user_input}

Respond as ULTRON.
"""

    try:

        response = llm.call(prompt)

        print(f"ULTRON: {response}\n")

    except Exception as e:

        print("\nULTRON: System error.")
        print(f"Diagnostic: {e}\n")