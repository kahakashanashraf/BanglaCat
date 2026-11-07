import csv,json,collections
src='/mnt/data/bangla_context_toxicity_train_final.csv'
progress='/mnt/data/translation_progress_backup.csv'
with open(src,encoding='utf-8-sig',newline='') as f: orig=list(csv.DictReader(f))
with open(progress,encoding='utf-8-sig',newline='') as f: pr=list(csv.DictReader(f))
assert len(orig)==len(pr)
m={}
for o,p in zip(orig,pr):
 assert all(o[k]==p[k] for k in orig[0].keys())
 for a,b in [('previous_reply','english_previous_reply'),('target_reply','english_target_reply')]:
  if p[b] and p[b]!='Loading...' and not p[b].startswith('#'):
   m[o[a]]=p[b]
need=list(dict.fromkeys(s for o in orig for s in (o['previous_reply'],o['target_reply']) if s not in m))
print('Mapped known texts',len(m),'new distinct translations needed',len(need))
sep=' ⟦SEP⟧ '
assert all('⟦SEP⟧' not in s for s in need)
# Keep batches under ~500 Bengali characters to avoid excessive compression or loss.
batches=[]; current=[]; nchars=0
for s in need:
 if current and (len(current)>=4 or nchars+len(s)>480):
  batches.append(current);current=[];nchars=0
 current.append(s);nchars+=len(s)
if current:batches.append(current)
p='/mnt/data/translation_remaining_batch_4.csv'
with open(p,'w',encoding='utf8',newline='') as f:
 w=csv.writer(f);w.writerow(['batch_id','bangla_joined','english_joined'])
 for i,strings in enumerate(batches):w.writerow([str(i),sep.join(strings),''])
with open('/mnt/data/translation_remaining_batches.json','w',encoding='utf8') as f:json.dump(batches,f,ensure_ascii=False)
with open('/mnt/data/known_translation_map.json','w',encoding='utf8') as f:json.dump(m,f,ensure_ascii=False)
print('batch count',len(batches),'max batch char',max(len(sep.join(b)) for b in batches),'max segments',max(map(len,batches)))
