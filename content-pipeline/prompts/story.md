You are creating spoken-language learning content for a short vertical video (TikTok / YouTube Shorts style).

Generate a short story/dialogue for:
- Language: {language}
- Level: {level}{level_description}
- Topic: {topic}
- Target spoken duration: about {duration} seconds

Requirements:
- Natural spoken language — the way a native speaker actually talks, not textbook prose.
- Suitable for listening practice and shadowing (repeating aloud right after hearing it).
- Reuse a small number of sentence patterns across the paragraphs so the same structure comes up more than once — this helps a learner recognize and internalize it.
- Do not use grammar structures more advanced than the given level.
- Keep the total spoken length roughly matching the target duration (~2.5 words per second of natural spoken pace as a rough guide).
- Prioritize speaking-oriented sentences over reading-oriented ones. Avoid rare or unnecessary vocabulary.

Output ONLY a single JSON object with exactly this shape — no markdown code fence, no commentary before or after:

{{
  "title": "<short title for the story>",
  "language": "{language}",
  "level": "{level}",
  "paragraphs": ["<sentence or short paragraph 1>", "<sentence or short paragraph 2>", "..."]
}}
