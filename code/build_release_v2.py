"""Build the BanglaCAT Version 2 public release from the project working files.

Usage:
    python build_release_v2.py <project_root> <output_dir>

<project_root> is the folder that contains "final data/", "train set/" and "test set/".
<output_dir> receives data/, votes/ and CHECKSUMS.sha256.

Changes relative to Version 1
  * Unified schema across train and test, Bangla and English files:
      row_id, split, source, context_type, context, target_reply, level_1_class, toxicity_type
    English files add context_en and target_reply_en next to the Bangla text.
  * Stable test row IDs (test_NNNN, from the original annotation-pool row number).
  * Six duplicated test (source, context, reply) identities removed (first occurrence kept):
    2,329 -> 2,323 rows. The Drive final files are already deduplicated; the removed rows are
    read from "final data/test/audit/excluded_duplicate_test_rows.csv".
  * The English text of both partitions comes from the re-translated Version 2 files.
  * toxicity_type is always the literal string "None" for Non-toxic rows (V1 English test
    file had empty cells).
  * Individual reviewer / annotator votes and adjudication records are released in votes/.
"""
import hashlib
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(sys.argv[1])
OUT = Path(sys.argv[2])
(OUT / "data").mkdir(parents=True, exist_ok=True)
(OUT / "votes").mkdir(parents=True, exist_ok=True)


def read(p):
    return pd.read_csv(ROOT / p, keep_default_na=False, encoding="utf-8-sig")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    s = re.sub(r"[​-‏⁠﻿\x00-\x08\x0b-\x1f\x7f]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def write(df, path):
    df.to_csv(path, index=False, encoding="utf-8-sig", lineterminator="\n")


COLS = ["row_id", "split", "source", "context_type", "context", "target_reply",
        "level_1_class", "toxicity_type"]

# ---------------------------------------------------------------- train
tr_bn = read("final data/train/bangla_context_toxicity_train_final_preprocessed.csv")
tr_en = read("final data/train/bangla_context_toxicity_train_final_ENGLISH.csv")
assert (tr_bn.row_id.values == tr_en.row_id.values).all()
assert (tr_bn[["level_1_class", "toxicity_type"]].values == tr_en[["level_1_class", "toxicity_type"]].values).all()
assert not tr_bn.row_id.astype(str).str.contains("E+", regex=False).any()
train = pd.DataFrame({
    "row_id": tr_bn.row_id,
    "split": "train",
    "source": "synthetic (Claude Sonnet 5)",
    "context_type": "preceding comment (synthetic)",
    "context": tr_bn.previous_reply,
    "target_reply": tr_bn.target_reply,
    "level_1_class": tr_bn.level_1_class,
    "toxicity_type": tr_bn.toxicity_type.replace("", "None"),
})
train_en = train.copy()
train_en.insert(6, "context_en", tr_en.previous_reply.values)
train_en.insert(7, "target_reply_en", tr_en.target_reply.values)

# Author correction of one systematic machine-translation error in the training English:
# "শান্তভাবে বললে" ("speaking calmly") at the start of a reply was rendered as "To put it mildly"
# or "To put it bluntly", which changes the meaning. Only that opening phrase is replaced; every
# change is logged in code/translation/v2_author_corrections.csv.
corr = []
for i, (bn, en) in enumerate(zip(train_en.target_reply, train_en.target_reply_en)):
    if bn.startswith("শান্তভাবে বললে"):
        m = re.match(r"To put it (mildly|bluntly)\b", en)
        if m:
            new = "To put it calmly" + en[m.end():]
            corr.append({"row_id": train_en.at[i, "row_id"], "field": "target_reply_en",
                         "source_bn": bn, "before": en, "after": new})
            train_en.at[i, "target_reply_en"] = new
assert len(corr) == 750, len(corr)
(OUT / "code" / "translation").mkdir(parents=True, exist_ok=True)
write(pd.DataFrame(corr), OUT / "code" / "translation" / "v2_author_corrections.csv")
print("author corrections applied:", len(corr))

# ---------------------------------------------------------------- test
te_bn = read("final data/test/bangla_toxicity_test_set_HIERARCHICAL_FINAL.csv")
# In the English file the "context" and "reply" columns hold the English text.
te_en = read("final data/test/bangla_toxicity_test_set_HIERARCHICAL_FINAL_ENGLISH.csv")
prov = read("final data/test/bangla_toxicity_test_set_HIERARCHICAL_FINAL_WITH_PROVENANCE.csv")
pre_dedup = read("final data/test/audit/pre_dedup_annotated_test_records.csv")
dup_rows = read("final data/test/audit/excluded_duplicate_test_rows.csv")
key = ["Source", "context", "reply"]
labels = ["Source", "level_1_class", "toxicity_type"]
assert (te_bn[key].values == prov[key].values).all() and (te_en[labels].values == te_bn[labels].values).all()

ctype = {"facebook": "post or parent comment", "youtube": "post or parent comment", "news portal": "headline or post title"}
test = pd.DataFrame({
    "row_id": prov.original_row_number.map(lambda n: f"test_{int(n):04d}"),
    "split": "test",
    "source": te_bn.Source,
    "context_type": te_bn.Source.map(ctype),
    "context": te_bn.context,
    "target_reply": te_bn.reply,
    "level_1_class": te_bn.level_1_class,
    "toxicity_type": te_bn.toxicity_type.replace("", "None"),
})
test_en = test.copy()
test_en.insert(6, "context_en", te_en.context.values)
test_en.insert(7, "target_reply_en", te_en.reply.values)
assert len(test) == 2323

# One test reply holds the spreadsheet error value "#NAME?" instead of text. The value is already
# present in all three round-1 annotation files, so the original comment cannot be recovered and the
# item is removed from the Version 2 release (recorded in votes/excluded_and_removed_items.csv).
lost = (test.target_reply.str.strip() == "#NAME?").values
assert lost.sum() == 1
lost_rows = test[lost].copy()
test = test[~lost].reset_index(drop=True)
test_en = test_en[~lost].reset_index(drop=True)
assert len(test) == 2322


def dedup_key(s, c, r):
    return "||".join(norm(x).lower() for x in (s, c, r))


kept_of = {dedup_key(s, c, r): rid for s, c, r, rid in zip(test.source, test.context, test.target_reply, test.row_id)}
removed_dups = pd.DataFrame({
    "row_id": dup_rows.original_row_number.map(lambda n: f"test_{int(n):04d}"),
    "context": dup_rows.context,
    "target_reply": dup_rows.reply,
    "duplicate_of": [kept_of[dedup_key(s, c, r)] for s, c, r in dup_rows[key].values],
})
assert len(removed_dups) == 6

# No English field may still contain Bangla script.
bangla = re.compile(r"[ঀ-৿]")
left = sum(df[c].map(lambda t: bool(bangla.search(t))).sum()
           for df in (train_en, test_en) for c in ("context_en", "target_reply_en"))
assert left == 0, left

# ---------------------------------------------------------------- votes: training review
au = read("train set/adjudicated_q1_outputs/final_dataset_majority_adjudicated_AUDIT.csv")
au["_k"] = au.previous_reply.map(norm) + "||" + au.target_reply.map(norm)
link = dict(zip(tr_bn.previous_reply.map(norm) + "||" + tr_bn.target_reply.map(norm), tr_bn.row_id))
tv = pd.DataFrame({
    "row_id": au._k.map(link).fillna(""),
    "status": au._k.map(lambda k: "released" if k in link else "excluded_no_majority"),
    "context": au.previous_reply,
    "target_reply": au.target_reply,
    "candidate_level_1": au._original_label1_norm,
    "candidate_toxicity_type": au._original_label2_norm,
})
for i in (1, 2, 3):
    tv[f"reviewer{i}_decision"] = au[f"annotator{i}_agree_disagree"]
    tv[f"reviewer{i}_level_1"] = au[f"annotator{i}_suggested_label1"]
    tv[f"reviewer{i}_toxicity_type"] = au[f"annotator{i}_suggested_label2"].replace("", "None")
tv["majority_vote_count"] = au.majority_vote_count
tv["final_level_1"] = au.final_level_1_class
tv["final_toxicity_type"] = au.final_toxicity_type
tv["label_changed_from_candidate"] = au.label_changed_by_majority
assert (tv.status == "released").sum() == 19453

# ---------------------------------------------------------------- votes: test annotation
r1 = read("test set/annotator/iaa_results/THREE_ANNOTATOR_MAJORITY_WITH_AUDIT.csv")
nm = read("test set/annotator/iaa_results/NO_MAJORITY_PRIVATE_AUDIT.csv")
ind = {i: read(f"test set/independently annotate/independent{i}.csv").set_index("blind_item_id") for i in (1, 2, 3)}


def parse(pattern):
    out = {}
    for part in pattern.split(" | "):
        who, lab = part.split("=", 1)
        l1, l2 = lab.split("::", 1)
        out[who] = (l1, l2)
    return out


rows = []
for _, r in r1.iterrows():
    v = parse(r.private_vote_pattern)
    rows.append({"orig": int(r.original_row_number), "source": r.Source, "context": r.context,
                 "target_reply": r.reply, "round1": [v[f"Annotator{i}"] for i in (1, 2, 3)],
                 "blind": "", "round2": [("", "")] * 3})
for _, r in nm.iterrows():
    rows.append({"orig": int(r.original_row_number), "source": r.Source, "context": r.context,
                 "target_reply": r.reply,
                 "round1": [(r[f"Annotator{i}_level_1"], r[f"Annotator{i}_toxicity_type"]) for i in (1, 2, 3)],
                 "blind": r.blind_item_id,
                 "round2": [(ind[i].loc[r.blind_item_id, "level_1_class"],
                             ind[i].loc[r.blind_item_id, "toxicity_type"] or "None") for i in (1, 2, 3)]})
fin = pre_dedup.set_index("original_row_number")
removed_ids = set(removed_dups.row_id)
out = []
for x in sorted(rows, key=lambda d: d["orig"]):
    rid = f"test_{x['orig']:04d}"
    rec = {"row_id": rid, "source": x["source"], "context": x["context"], "target_reply": x["target_reply"]}
    for i, (l1, l2) in enumerate(x["round1"], 1):
        rec[f"round1_annotator{i}_level_1"], rec[f"round1_annotator{i}_toxicity_type"] = l1, l2
    rec["round2_blind_item_id"] = x["blind"]
    for i, (l1, l2) in enumerate(x["round2"], 1):
        rec[f"round2_annotator{i}_level_1"], rec[f"round2_annotator{i}_toxicity_type"] = l1, l2
    if x["orig"] in fin.index:
        f = fin.loc[x["orig"]]
        rec.update(final_level_1=f.level_1_class, final_toxicity_type=f.toxicity_type,
                   final_label_source=f.final_label_source,
                   status="removed_duplicate_v2" if rid in removed_ids
                   else ("removed_text_lost_v2" if rid in set(lost_rows.row_id) else "released"))
    else:
        rec.update(final_level_1="", final_toxicity_type="", final_label_source="unresolved_tie",
                   status="excluded_unresolved_tie")
    out.append(rec)
tvotes = pd.DataFrame(out)
assert len(tvotes) == 2330 and (tvotes.status == "released").sum() == 2322

excluded = pd.concat([
    tv[tv.status != "released"].assign(split="train", row_id="(no id)", reason="no 2-of-3 majority in review")
      [["split", "row_id", "context", "target_reply", "reason"]],
    tvotes[tvotes.status == "excluded_unresolved_tie"].assign(split="test", reason="tie after pooling six votes")
      [["split", "row_id", "context", "target_reply", "reason"]],
    removed_dups.assign(split="test", reason="duplicate of " + removed_dups.duplicate_of)
      [["split", "row_id", "context", "target_reply", "reason"]],
    lost_rows.assign(split="test", reason="reply text lost: spreadsheet error value #NAME? already in all annotation files")
      [["split", "row_id", "context", "target_reply", "reason"]],
], ignore_index=True)

# ---------------------------------------------------------------- write
files = {
    "data/banglacat_train_bn.csv": train,
    "data/banglacat_train_en.csv": train_en,
    "data/banglacat_test_bn.csv": test,
    "data/banglacat_test_en.csv": test_en,
    "votes/train_review_votes.csv": tv,
    "votes/test_annotation_votes.csv": tvotes,
    "votes/excluded_and_removed_items.csv": excluded,
}
for rel, df in files.items():
    write(df, OUT / rel)

lines = []
for p in sorted(OUT.rglob("*")):
    if p.is_file() and p.name != "CHECKSUMS.sha256" and not p.name.startswith("."):
        lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(OUT).as_posix()}")
(OUT / "CHECKSUMS.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

print("train", len(train), train.level_1_class.value_counts().to_dict())
print("test", len(test), test.level_1_class.value_counts().to_dict(), test.source.value_counts().to_dict())
print("removed duplicates", removed_dups.row_id.tolist(), "->", removed_dups.duplicate_of.tolist())
print("excluded", len(excluded))
