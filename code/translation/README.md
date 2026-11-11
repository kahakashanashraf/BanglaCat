# Version 2 English translation of the training partition

These files document how the English text of the training partition (`data/banglacat_train_en.csv`) was produced, and let it be reproduced exactly.

## What was done

1. Bangla → English bulk translation with the `GOOGLETRANSLATE(text, "bn", "en")` function of Google Sheets, in a ChatGPT-assisted session (7 November 2026). The session ran on ChatGPT Plus with GPT-6 Sol (shown as “GPT-6” in ChatGPT); Google Translate reports no model version.
2. `prep_batches.py`: kept every translation already completed in the sheet (`inputs/translation_progress_backup.csv`) and grouped the 6,660 remaining distinct strings into 1,674 batches of up to four strings joined by `⟦SEP⟧`.
3. The batches were translated in Google Sheets (`inputs/TEMP Bengali Train Remaining Batches.csv`). In one batch (493) the separators were lost, so its four strings were translated separately and added to the mapping. These are the four entries in `inputs/known_translation_map.json` that `prep_batches.py` does not produce.
4. `finalize_train_translation.py`: split the batches, merged them into the mapping and applied source-aware, rule-based corrections to 811 fields (threats, beating versus killing, profanity, insults, rhetorical questions, negation). `translation_QA_report.json` is its report.
5. Author correction: in 750 replies that open with "শান্তভাবে বললে" ("speaking calmly"), the opening "To put it mildly"/"To put it bluntly" was replaced by "To put it calmly" (`v2_author_corrections.csv`; applied by `../build_release_v2.py`).

The test-set English was produced earlier in the same ChatGPT conversation (GPT-6 Sol) from the same instruction. No intermediate or per-row record of that step was retained.

## Reproduce steps 2 and 4

The scripts are the original session files and read from `/mnt/data/`. Copy the five files in `inputs/` into a working folder, replace `/mnt/data/` in both scripts with that folder, then run:

```
python prep_batches.py                 # writes translation_remaining_batches.json etc.
cp inputs/known_translation_map.json . # restores the four batch-493 entries (step 3)
python finalize_train_translation.py   # writes bangla_context_toxicity_train_final_ENGLISH.csv
```

Expected result: `prep_batches.py` reports 7,375 known strings, 6,660 new strings and 1,674 batches. Its batch files are identical to those in `inputs/`. `finalize_train_translation.py` reports 0 untranslated fields, 1 batch issue (493) and 811 source-aware changes. Its output equals the training English before the author correction of step 5 in all 38,906 text fields. Without step 3 it writes a `..._PARTIAL_ENGLISH.csv` with five untranslated fields.

## Other files

- `train_exact_source_to_translation_map.csv`: every Bangla training string with its English, as delivered by the session.
- `workflow_and_translation_log.md`, `validation_results.json`: the session's own process note and structural validation.
