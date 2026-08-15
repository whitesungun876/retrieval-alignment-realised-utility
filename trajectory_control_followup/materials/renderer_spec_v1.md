# Auditable renderer specification

The `src/renderer.py` implementation is normative together with this document.

Common shell:

```
Interaction record
Format: chronological action-observation sequence

Task description:
{P source cookbook OR C abstract statement}

Initial state:
{P source observation OR C abstract phase statement}

Step NN phase:
{phase}
Step NN action:
{P original command OR C abstract action statement}
Step NN observation:
{P original observation OR C abstract transition statement}

Interaction outcome: success
```

No source identity appears in either condition. P remains concrete and verbatim
within the neutral shell. C is derived only from source action classes and turn
count. It has no access to a target record or any P/C outcome.

Phase classification is deterministic from the source action prefix:

- look/read -> inspect
- move -> navigate
- take/open/close -> acquire
- slice/dice/chop/cut/cook/fry/roast/grill -> transform
- prepare -> complete
- eat -> stop
- otherwise -> orient

The C vocabulary is a fixed abstract lexicon. The tokenizer-matching algorithm
may add at most one distinct predeclared detail sentence per field from a finite
list. It never repeats a sentence and never includes environment nouns, recipe
content, concrete commands, zero-based indices, or target text.

The +/-10% material-length gate uses the local open-weight Qwen3-family BPE
tokenizer named in `config/design_v1.json` as a prespecified proxy. It is not
described as the exact tokenizer of the hosted `qwen3.7-plus-2026-05-26`
snapshot; a separate word-count ratio is also audited.
