You are preparing shadowing/chunking practice material from a spoken-language story for {language} learners at level {level}.

Here are the sentences from the story, numbered:

{sentences}

For EACH sentence, break it into small spoken "chunks" (phrases) of about 2-5 words, split at natural semantic/breath boundaries — the way a speaker would actually pause, for example:
"Good morning everyone." -> ["Good morning", "everyone."]

Rules:
- Joining a sentence's chunks with a single space MUST reproduce the sentence text EXACTLY (same words, same order, same punctuation) — do not drop, add, or reorder anything.
- Keep chunks meaningful — avoid splitting a single word in half, avoid breaking up a fixed phrase like "Good morning" or "thank you".

Also extract, for the story as a whole:
- keywords: important vocabulary words worth highlighting for this level
- reusable_expressions: short expressions a learner could reuse in other conversations (e.g. "Let's kick off", "I don't have any big problems")
- sentence_patterns: general sentence structures learners can reuse, with a blank for the variable part (e.g. "Yesterday, I focused on ___", "Today, my plan is to ___")

Output ONLY a single JSON object with exactly this shape — no markdown code fence, no commentary before or after:

{{
  "chunks": [
    {{"sentence": "<sentence 1 exact text>", "parts": ["<chunk 1>", "<chunk 2>", "..."]}},
    "..."
  ],
  "keywords": ["...", "..."],
  "reusable_expressions": ["...", "..."],
  "sentence_patterns": ["...", "..."]
}}
