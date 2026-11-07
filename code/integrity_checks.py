"""Integrity checks reported in the data article (section "Preprocessing and integrity checks").

Usage:
    python integrity_checks.py <release_dir>

<release_dir> is the folder that contains data/ and votes/ (this repository's root).
Prints every number the article reports for these checks.
"""
import collections
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

REL = Path(sys.argv[1] if len(sys.argv) > 1 else ".")


def read(p):
    return pd.read_csv(REL / p, keep_default_na=False, dtype=str, encoding="utf-8-sig")


train = read("data/banglacat_train_bn.csv")
test = read("data/banglacat_test_bn.csv")
test_en = read("data/banglacat_test_en.csv")
train_en = read("data/banglacat_train_en.csv")
votes = read("votes/test_annotation_votes.csv")


def norm(s):
    """NFC, collapse whitespace, lowercase, drop punctuation (used for the near-duplicate check)."""
    s = unicodedata.normalize("NFC", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return re.sub(r"[^\w\s]", "", s)


def grams(s, n=5):
    return {s[i:i + n] for i in range(max(1, len(s) - n + 1))}


# 1. Exact context-reply overlap between partitions (after NFC + whitespace normalisation).
key = lambda c, r: unicodedata.normalize("NFC", re.sub(r"\s+", " ", c).strip()) + "||" + \
    unicodedata.normalize("NFC", re.sub(r"\s+", " ", r).strip())
overlap = set(map(key, train.context, train.target_reply)) & set(map(key, test.context, test.target_reply))
print("exact context-reply pairs shared by train and test:", len(overlap))

# 2. Near-duplicate replies: character 5-gram Jaccard >= 0.80 against any training reply.
train_reps = list(dict.fromkeys(train.target_reply))
tg = [grams(norm(s)) for s in train_reps]
index = collections.defaultdict(list)
for k, g in enumerate(tg):
    for x in g:
        index[x].append(k)
near = []
for rid, s in zip(test.row_id, test.target_reply):
    a = grams(norm(s))
    cand = collections.Counter(k for x in a for k in index.get(x, ()))
    best, bk = max(((len(a & tg[k]) / len(a | tg[k]), k) for k in cand), default=(0, None))
    if best >= 0.80:
        near.append((rid, s, train_reps[bk], round(best, 2)))
print(f"test replies with 5-gram Jaccard >= 0.80 to a training reply: {len(near)} of {len(test)}")
for rid, s, t, j in near:
    print(f"   {rid}  J={j}  test={s!r}  train={t!r}")

# 3. Duplicates and repeated contexts in the released test set.
dkey = [unicodedata.normalize("NFC", re.sub(r"\s+", " ", "||".join(x)).strip()).lower()
        for x in zip(test.source, test.context, test.target_reply)]
print("duplicated source/context/reply identities in Version 2 test set:", len(dkey) - len(set(dkey)))
print("test records whose context repeats another record's context:", len(test) - test.context.nunique())
print("distinct contexts in the news-portal subset:", test[test.source == "news portal"].context.nunique())

# 4. Removal and exclusion record.
print("test vote-file statuses:", votes.status.value_counts().to_dict())

# 5. English files.
bn = re.compile("[ঀ-৿]")
left = sum(df[c].map(lambda t: bool(bn.search(t))).sum() for df in (train_en, test_en) for c in ("context_en", "target_reply_en"))
print("English fields still containing Bangla script:", left)
same = all((a[["row_id", "level_1_class", "toxicity_type"]].values == b[["row_id", "level_1_class", "toxicity_type"]].values).all()
           for a, b in ((train, train_en), (test, test_en)))
print("Bangla and English files row-aligned with identical labels:", same)
