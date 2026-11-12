# BanglaCAT — Version 2

A context-aware Bangla toxicity dataset with hierarchical labels. It has:

- a **synthetic training partition**: 19,453 context–reply pairs generated with Claude Sonnet 5 and then checked independently by three human reviewers;
- a **real-world test partition**: 2,322 public context–reply pairs from Facebook, YouTube and the Facebook pages of Bangladeshi news organizations, copied manually and annotated by humans.

Each row pairs a *target reply* with the *context* it answers. Every row has a binary Level-1 label (Toxic / Non-toxic). Toxic rows also have one of 11 Level-2 subtypes.

Authors: Kahakashan Ashraf, Md. Hamid Hosen, Jannathun Nahar, Mikdad Mohammad Asif, Mishu Dhar, Mahfuzulhoq Chowdhury, Md Kishor Morol, Tze Hui Liew
DOI: 10.17632/8vr3w68c7x.2

## What changed from Version 1

| Change | Detail |
|---|---|
| Test duplicates and one corrupted item removed | Six (source, context, reply) identities appeared twice under NFC/whitespace/case normalisation. Both copies carried identical labels. The second copy of each was removed, taking the test set from 2,329 to 2,323 rows. One further item (`test_0574`) was removed because its reply had been replaced by the spreadsheet error value `#NAME?` already in all annotation files, so its text could not be recovered; the Version 2 test set has **2,322** rows. The removed IDs are listed in `votes/excluded_and_removed_items.csv`. |
| Stable test IDs | `row_id` = `test_NNNN`, where NNNN is the item's row number in the 2,330-item annotation pool. Training IDs are unchanged from V1, except for two IDs that a spreadsheet had turned into scientific notation (`4.14207E+19`, `6.58467E+19`); these were restored to `41420723587897267399` and `65846714934211581143`. |
| One schema for all files | Train and test, Bangla and English, now share the same columns (below). |
| English files aligned | Both English files keep the Bangla text and add `context_en` and `target_reply_en`. |
| `None` made explicit | `toxicity_type` is the literal string `None` for every Non-toxic row. The V1 English test file had empty cells. |
| English re-translated in full | In the V1 English test file, 551 fields in 518 of the retained rows still held Bangla text. For V2 the English text of both partitions was translated again in full. The training partition was translated with the GOOGLETRANSLATE function of Google Sheets in a ChatGPT-assisted workflow, followed by script-based corrections; the scripts, log and full source-to-English mapping are in `code/translation/`. One systematic error was then corrected by the authors: in 750 training replies that open with "শান্তভাবে বললে" ("speaking calmly"), the English opening "To put it mildly"/"To put it bluntly" was changed to "To put it calmly"; each change is listed in `code/translation/v2_author_corrections.csv`. In the test partition, one news headline (the context of 40 rows) whose idiom had been translated literally was corrected after the bilingual check of a random sample; the 40 changes are listed in `code/translation/v2_qc_corrections.csv`. No English field in V2 contains Bangla script. Labels and Bangla text are unchanged. |
| Votes and code released | Individual reviewer/annotator votes, adjudication records, excluded items, analysis notebooks, the release-building script and the figure script. |

### Column mapping from V1

| V1 train | V1 test | V2 (all files) |
|---|---|---|
| previous_reply | context | `context` |
| target_reply | reply | `target_reply` |
| — | Source | `source` |
| reply_en (test only) | context_en | `context_en` / `target_reply_en` |

## Test-set sources

No keyword search was used: the authors first listed the pages and channels below and then copied comments from their posts manually (June 25 – August 25, 2026). A reply was kept when it was written directly under the post or comment used as its context; no other filtering was applied.

- News and television outlets (8): banglanews24.com, Channel 24, BanglaVision, dbcnews.tv, Jamuna TV, Rtv, Channel i, Durbin News. Their Facebook posts form the `news portal` subset, whose context is the post headline.
- Other public pages and channels (15): Salman Muqtadir, Cricket Sarcasm, Walter Bhai, Prothom Aluu, Baler Kontho, GojobVision, Lord Association, Apu Biswas, Sabila Nur, Shakib Al Hasan, BNP Media Cell, Bangladesh Awami League, Sarjis Alam, Engineer’s Diary, PUSAB – Private University Students Alliance.

## Files

| Path | Rows | Content |
|---|---|---|
| `data/banglacat_train_bn.csv` | 19,453 | Training pairs (Bangla) with final labels |
| `data/banglacat_train_en.csv` | 19,453 | Same rows, plus `context_en`, `target_reply_en` (machine translation) |
| `data/banglacat_test_bn.csv` | 2,322 | Real-world test pairs (Bangla) with final labels |
| `data/banglacat_test_en.csv` | 2,322 | Same rows, plus `context_en`, `target_reply_en` (machine translation) |
| `votes/train_review_votes.csv` | 19,454 | Candidate label, three human reviewers' Agree/Disagree decisions and corrected labels, majority count, final label, status |
| `votes/test_annotation_votes.csv` | 2,330 | Round-1 votes (3 annotators); round-2 votes (3 new annotators) for the 188 items without a round-1 majority; final label, label source, status |
| `votes/excluded_and_removed_items.csv` | 9 | 1 training item without majority, 1 test item still tied after pooling six votes, 6 removed test duplicates, 1 test item whose reply text was lost (`#NAME?`) |
| `code/build_release_v2.py` | — | Builds `data/` and `votes/` from the project working files |
| `code/translation/` | — | Version 2 English translation of the training partition: the original session scripts (`prep_batches.py`, `finalize_train_translation.py`), their saved inputs (`inputs/`), QA report, process log, validation results, the full source-to-English mapping and `v2_author_corrections.csv` (the 750 author corrections) and `v2_qc_corrections.csv` (the 40-row test headline correction). `code/translation/README.md` explains how rerunning the scripts reproduces the delivered English exactly. |
| `code/integrity_checks.py` | — | Recomputes the integrity checks reported in the data article: train–test overlap, near-duplicate replies (5-gram Jaccard ≥ 0.80: 18 of 2,322), duplicates, repeated contexts, English-file alignment |
| `code/make_figures.py` | — | Regenerates Figs. 1–4 of the data article from `data/` |
| `code/Bangla_Toxicity_IAA_Majority_train_*.ipynb` | — | Training-review agreement (Fleiss' κ, Krippendorff's α, Gwet's AC1, bootstrap CIs) and majority adjudication |
| `code/Bangla_Toxicity_test_IAA_Majority_NoMajority_Blind.ipynb` | — | Round-1 test agreement, majority voting, blind export of items without majority |
| `code/Bangla_Toxicity_Independent_Final_Merge_test_*.ipynb` | — | Round-2 merge, pooled six-vote fallback, preprocessing, integrity checks, EDA |
| `CHECKSUMS.sha256` | — | SHA-256 of every file in this release |

The notebooks were run on Google Colab (Python 3.13; the training-review notebook used Python 3.13.16, pandas 2.2.3 and numpy 2.4.6). Their input paths point to `/content/drive/MyDrive/toxicity/...`; edit `BASE_DIR` in the first code cell to run them locally.

## Columns (all four data files)

| Column | Meaning |
|---|---|
| `row_id` | Stable identifier |
| `split` | `train` or `test` |
| `source` | `synthetic (Claude Sonnet 5)`, `facebook`, `youtube`, or `news portal` (comments under posts on the public Facebook pages of Bangladeshi news organizations) |
| `context_type` | `preceding comment (synthetic)`, `post or parent comment` (Facebook/YouTube) or `headline or post title` (news portals). The value is set by source, not row by row. |
| `context` | Text the reply responds to |
| `target_reply` | Text that is labelled |
| `context_en`, `target_reply_en` | English machine translation (English files only; the Bangla text is canonical) |
| `level_1_class` | `Toxic` or `Non-toxic` |
| `toxicity_type` | `None` for Non-toxic rows. For Toxic rows, one of: Insult, Threat, Hate Speech, Profanity, Harassment, Identity Attack, Toxic Endorsement / Agreement, Incitement / Encouragement of Harm, Mockery / Ridicule, Sexual Harassment / Objectification, Dehumanization |

> **Reading tip:** `None` is a real label, not a missing value. Load the files with
> `pd.read_csv(path, keep_default_na=False)`. Otherwise pandas turns `None` into NaN.

## Recommended use

- Train on the synthetic partition and evaluate on the 2,322-row real test partition. Report test results separately: the two partitions differ in source, length (median context 44 vs 80 characters) and subtype mix.
- Several Level-2 classes are rare in the test set: Threat (8), Toxic Endorsement / Agreement (12), Identity Attack (15). Use macro-averaged metrics and report per-class support.
- News-related contexts are headlines or post titles; Facebook and YouTube contexts are post descriptions or parent comments. Use `context_type` to evaluate each group separately.

## Licence

- **Covered by CC BY 4.0** (© the authors): the labels, the annotation and vote records, the synthetic training text, the English translations, the code and this documentation.
- **Not covered by CC BY 4.0:** the Bangla `context` and `target_reply` text of the **test** partition. These are short public comments and headlines written by third parties, and the authors hold no rights in them. They are redistributed only so that non-commercial research on toxicity detection and content moderation can be reproduced. Usernames, profile links and other account identifiers were never collected.
  - Users must follow the source platforms' terms of service.
  - Users must not try to re-identify, contact or target the authors of the comments.
  - A rights holder can ask for an item to be removed by contacting the corresponding author.

The data contain offensive language by design.

## Checksums

SHA-256 of the four data files:

```
06aef7e1ed4a9fffb52beb92bdd8dc0ffea05508ffce93393fa0d059c092efc5  data/banglacat_train_bn.csv
cd31f1715d7ce57bd751246ad77b4209bb305d0027296f930400c22d687d1565  data/banglacat_train_en.csv
c6b7b7fd1bfb3e090101313e89bb5830e4d5e786de06345c981b4c1329fdfffb  data/banglacat_test_bn.csv
8ec7d8f9c12b84ef7102c0ca334ba4d7e9e2e894d8e483070b001b4f4f28c97b  data/banglacat_test_en.csv
```

`CHECKSUMS.sha256` lists every file in the release. To verify: `shasum -a 256 -c CHECKSUMS.sha256`.

## Citation

Ashraf, K., Hosen, M. H., Nahar, J., Asif, M. M., Dhar, M., Chowdhury, M., Morol, M. K., Liew, T. H. (2026). *BanglaCAT: A Context-Aware Bangla Toxicity Dataset with LLM-Generated Training Data and a Human-Annotated Social Media Test Set* (Version 2) [Data set]. Mendeley Data. https://doi.org/10.17632/8vr3w68c7x.2
