
import ollama

from bible_study_ai.agent.schemas import GeneratedAnswer

response = ollama.chat(
    model="qwen3:4b",
    messages=[
        {
            "role": "system",
            "content": (
                "You are a Bible study assistant. "
                "Answer the question using only the supplied passage. "
                "Write a coherent explanation in the answer field. "
                "Include only relevant scripture references in citations. "
                "Do not repeat the question."
            ),
        },
        {
            "role": "user",
            "content": """
Question:
How can I show compassion to someone who has wronged me?

Bible passage:

Romans 12:14-21 (WEB)

14. Bless those who persecute you; bless, and don't curse.
15. Rejoice with those who rejoice. Weep with those who weep.
16. Be of the same mind one toward another. Don't set your mind on
high things, but associate with the humble.
17. Repay no one evil for evil. Respect what is honorable in the
sight of all men.
18. If it is possible, as much as it is up to you, be at peace
with all men.
19. Don't seek revenge yourselves, beloved, but give place to
God's wrath.
20. If your enemy is hungry, feed him. If he is thirsty, give him
a drink.
21. Don't be overcome by evil, but overcome evil with good.
""",
        },
    ],
    format=GeneratedAnswer.model_json_schema(),
    options={"temperature": 0},
    think=False,
)

print(response.message.content)
