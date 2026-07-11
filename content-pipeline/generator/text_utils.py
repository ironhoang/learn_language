"""Shared text helpers used by more than one stage (chunks + subtitle fallback).

This lives outside any single generator/<stage>/ package on purpose: importing
a stage's own generate.py from another stage would violate "no stage should
call another stage directly" (audio-tecnical-flow.md), but a plain utility
function with no stage-specific behavior is fine to share.
"""

import re

_SENTENCE_END = re.compile(r"[^.!?。！？]+[.!?。！？]+|[^.!?。！？]+$")


def split_sentences(paragraphs: list[str]) -> list[str]:
    sentences = []
    for paragraph in paragraphs:
        for match in _SENTENCE_END.finditer(paragraph.strip()):
            sentence = match.group().strip()
            if sentence:
                sentences.append(sentence)
    return sentences
