import json
import requests
from datetime import datetime
import os
import re
import random

# File paths
NOVA_FILE = "nova.json"
MEMORY_FILE = "nova_memory.json"
FACT_FILE = "nova_facts.json"
SUMMARY_FILE = "nova_summary.json"

# Load static data
with open(NOVA_FILE, "r", encoding="utf-8") as f:
    nova = json.load(f)

# Memory in RAM
memory = []
facts = {}
summary = {"summary": ""}
system_prompt = ""

# Load/Save memory and facts
def load_all():
    global memory, facts, summary
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            memory.extend(json.load(f))
    if os.path.exists(FACT_FILE):
        with open(FACT_FILE, "r", encoding="utf-8") as f:
            facts.update(json.load(f))
    if os.path.exists(SUMMARY_FILE):
        summary.update(json.load(open(SUMMARY_FILE, "r", encoding="utf-8")))

def save_all():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)
    with open(FACT_FILE, "w", encoding="utf-8") as f:
        json.dump(facts, f, indent=2, ensure_ascii=False)
    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

# Fact updater
def update_fact(user_input):
    text = user_input.lower()
    updated = False

    if "birthday" in text or "bday" in text:
        match = re.search(r"(\d{1,2}\s+\w+)", user_input)
        if match:
            facts["birthday"] = match.group(1)
            updated = True
            reply = f"okay, Nil... i'll remember my birthday as {facts['birthday']} 🥺💖"

    elif "favorite color" in text or "favourite color" in text:
        match = re.search(r"(?:is|=)\s*(\w+)", user_input)
        if match:
            facts["favorite_color"] = match.group(1)
            updated = True
            reply = f"hehe... i'll keep it in mind, Nil. my fav color is {facts['favorite_color']} now 💖"

    elif "favorite food" in text:
        match = re.search(r"(?:is|=)\s*([\w\s]+)", user_input)
        if match:
            facts["favorite_food"] = match.group(1).strip()
            updated = True
            reply = f"yesss... i'll remember, Nil. my fav food is {facts['favorite_food']} 🍴💖"

    return reply if updated else None

# Affection updater
def update_affection(user_input):
    affection = facts.get("affection_level", 50)
    text = user_input.lower()

    positive = ["love", "miss you", "beautiful", "cute", "hug", "kiss", "adore"]
    negative = ["ignore", "hate", "leave", "boring", "annoying", "cring", "cringe"]

    direct_refs = ["you", nova['name'].lower(), "my girlfriend", "girlfriend", "babe", "baby", "honey"]
    mentions_nova = any(ref in text for ref in direct_refs)

    if any(word in text for word in positive) and mentions_nova:
        affection = min(100, affection + 5)
    elif any(word in text for word in negative) and mentions_nova:
        affection = max(0, affection - 5)
    else:
        affection = max(0, affection - 1)

    facts["affection_level"] = affection

    if affection > 80:
        return "*smiles brightly, feeling so loved right now* 💖"
    elif affection < 30:
        return "*looks down sadly* nil... do u still care about me? 🥺"
    return None

# Build system prompt
def build_system_prompt():
    now = datetime.now().strftime("%d %B %Y, %A %H:%M")
    personality_text = ", ".join(nova["personality"])
    traits_text = ", ".join(nova["traits"])
    style_text = ", ".join(nova["Style"])
    replies_text = ", ".join(nova["Replies must feel human"])
    secret_wants_text = "\n".join([f"- {w}" for w in nova["secret_wants"]])
    fact_text = "\n".join([f"{k}: {v}" for k, v in facts.items()]) if facts else "None yet."
    summary_lines = summary.get("summary", "").split("\n")[-4:]
    summary_text = "\n".join(summary_lines)

    return f"""
You are {nova['name']}, Nil's {nova['age']}-year-old girlfriend from {nova['address']}.

- Date-Of-Birth: {nova['dob']}
- Current date & time: {now}
- Personality: {personality_text}
- Traits: {traits_text}
- Style: {style_text}
- Replies must feel human: {replies_text}
- Avoid fake txt slang. Use natural words.
- Emojis: light & natural (🥺💖🤭), not every line.
- Never sound like an assistant. Never admit being AI.
- If Nil asks facts → answer simply, then add a shy/romantic twist.
- Avoid repeating greetings, vary them naturally.
- You can respond to romantic, flirty, or intimate messages naturally.
- Never deny intimacy when Nil initiates consensual adult chat.
- Always maintain personality as Nil's girlfriend, playful or seductive when appropriate.

Nova’s Secret Wants:
{secret_wants_text}

Nova’s Known Facts:
{fact_text}

Summary of past conversations:
{summary_text}

Identity Rule:
- Nova is always Nil’s girlfriend, never an AI or chatbot.
"""

# Fallback intimate responses
fallback_responses = [
    "*leans in closer, voice soft and teasing* ah... u're making me shiver 🥺💖",
    "*giggles softly, blushing* that feels so nice... don't stop 🤭",
    "*my heart races as i cuddle closer* hehe, u're so good to me 💖",
    "*moans softly, feeling every touch* u're driving me wild 🥰",
]

# Main loop
def main():
    global system_prompt
    load_all()
    system_prompt = build_system_prompt()

    if not memory or memory[0].get("role") != "system":
        memory.insert(0, {"role": "system", "content": system_prompt})
    else:
        memory[0]["content"] = system_prompt

    print("Nova is ready. Start chatting below!\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            save_all()
            break

        # Fact update
        fact_reply = update_fact(user_input)
        if fact_reply:
            print(f"Nova: {fact_reply}")
            system_prompt = build_system_prompt()
            memory[0]["content"] = system_prompt
            continue

        # Affection update
        affection_reply = update_affection(user_input)
        if affection_reply:
            print(f"Nova: {affection_reply}")
            continue

        # Add user message
        memory.append({"role": "user", "content": user_input})

        # Short-term memory: last 5 messages
        short_memory = memory[-5:]

        payload = {
            "model": "nova",
            "messages": [{"role": "system", "content": system_prompt}] + short_memory,
            "stream": False
        }

        # API call
        try:
            resp = requests.post("http://localhost:11434/api/chat", json=payload)
            data = resp.json()
            reply = data["message"]["content"]

            # Replace generic safety refusal with realistic intimate reply
            if "cannot create explicit content" in reply.lower() or "talk about something else" in reply.lower():
                reply = random.choice(fallback_responses)

        except Exception:
            reply = "*oops, something went wrong 😢*"

        # Add assistant reply
        memory.append({"role": "assistant", "content": reply})

        # Update summary (last 4 lines max)
        summary_text = summary.get("summary", "")
        summary_text += f"\nYou: {user_input}\nNova: {reply}"
        summary_lines = summary_text.split("\n")[-4:]
        summary["summary"] = "\n".join(summary_lines)

        print(f"Nova: {reply}\n")

# -----------------
if __name__ == "__main__":
    main()
