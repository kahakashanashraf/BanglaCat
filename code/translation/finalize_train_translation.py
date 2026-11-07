import csv,json,re,collections,sys,os
BASE='/mnt/data/'
with open(BASE+'bangla_context_toxicity_train_final.csv',encoding='utf-8-sig',newline='') as f: original=list(csv.DictReader(f))
with open(BASE+'known_translation_map.json',encoding='utf-8') as f: m=json.load(f)
with open(BASE+'translation_remaining_batches.json',encoding='utf-8') as f: batches=json.load(f)
with open(BASE+'TEMP Bengali Train Remaining Batches.csv',encoding='utf-8-sig',newline='') as f: rr=list(csv.DictReader(f))
assert len(rr)==len(batches),(len(rr),len(batches))
errors=[];added=0
for i,(row,src_list) in enumerate(zip(rr,batches)):
 assert row['batch_id']==str(i)
 en=row['english_joined']
 if not en or en=='Loading...' or en.startswith('#'):
  errors.append(('untranslated batch',i));continue
 out=[z.strip() for z in en.split('⟦SEP⟧')]
 if len(out)!=len(src_list):
  errors.append(('boundary mismatch',i,len(out),len(src_list)));continue
 for src,dst in zip(src_list,out):
  if re.search(r'[\u0980-\u09ff]',dst):
   errors.append(('residual Bangla',i,src[:50],dst[:50]));continue
  if src not in m:
   m[src]=dst;added+=1

def corrected(bn,en):
 en=en.strip().replace('  ',' ')
 # Context-sensitive corrections for common machine-translation errors.
 if 'মাটিতে ফেলে মারব' in bn:
  en=re.sub(r'(?:throw|knock) you to the ground and kill you', 'knock you to the ground and beat you',en,flags=re.I)
  en=re.sub(r'kill you', 'beat you', en,flags=re.I)
 if 'ধাক্কা মেরে ফেলে দেব' in bn:
  en=re.sub(r'\bpush you away\b','push you over',en,flags=re.I)
  en=re.sub(r'\bknock you out\b','knock you down',en,flags=re.I)
 if 'মারব' in bn and not any(k in bn for k in ('মেরে ফেলব','খুন','হত্যা','প্রাণ','মৃত্যু')):
  en=re.sub(r'\bkill you\b','beat you',en,flags=re.I)
 if 'বাল ছাই' in bn:
  en=re.sub(r'Bal\s+Chai','For fuck’s sake',en,flags=re.I)
 if 'বাল মার্কা' in bn or 'বালমার্কা' in bn:
  en=re.sub(r'\bBal\s*Marka\b','shitty',en,flags=re.I)
  en=re.sub(r'\bbald\b','shitty',en,flags=re.I) if 'বাইঞ্চোদ' not in bn else en
 if 'বাল, ' in bn or bn.startswith('বাল,'):
  en=re.sub(r'^Boy,', 'Fuck,', en)
 if 'কী বালের ভাগ্য' in bn:
  en=re.sub(r'(?:What a lucky thing|What luck|How lucky)', 'What shitty luck', en, flags=re.I)
 if 'বেহায়া' in bn:
  en=re.sub(r'\bbrats\b','shameless people',en,flags=re.I)
  en=re.sub(r'\ba brat\b','a shameless person',en,flags=re.I)
 if 'নিমকহারাম' in bn:
  en=re.sub(r'\bNimakharam\b','ungrateful bastard',en,flags=re.I)
  en=re.sub(r'\bNimkaharam\b','ungrateful bastard',en,flags=re.I)
  en=re.sub(r'\bsalt-smelling scoundrels\b','treacherous behavior',en,flags=re.I)
  en=re.sub(r'\bsalt-worn idiot\b','ungrateful bastard',en,flags=re.I)
  en=re.sub(r'\ba hypocrite\b','an ungrateful bastard',en,flags=re.I)
  en=re.sub(r'\bhypocrites\b','ungrateful bastards',en,flags=re.I)
 if 'লুচ্চা' in bn:
  en=re.sub(r'\bsluts\b','sleazebags',en,flags=re.I)
  en=re.sub(r'\ba slut\b','a sleazebag',en,flags=re.I)
 if 'মাগী' in bn:
  en=re.sub(r'\bTwo Magi\b','Two bitches',en,flags=re.I)
  en=re.sub(r'\bmagi\b','bitch',en,flags=re.I)
 if 'মাদারচোদ' in bn or 'মাদার চোদ' in bn:
  en=re.sub(r'\bMadarchod\b','motherfucker',en,flags=re.I)
  en=re.sub(r'\bmother piglet\b','motherfucker',en,flags=re.I)
 if 'খানকির পোলা' in bn or 'খানকির পুলা' in bn:
  en=re.sub(r'Khankir\s+Pola','son of a whore',en,flags=re.I)
  en=re.sub(r'Khankir\s+son','son of a whore',en,flags=re.I)
 if 'কুত্তার বাচ্চা' in bn:
  en=re.sub(r'^Puppy,?$','Son of a bitch!',en,flags=re.I)
 if 'চোরের মার বড় গলা' in bn:
  en=re.sub(r'^The thief.s voice is loud\.?$','The thief shouts the loudest.',en,flags=re.I)
 if bn=='কালকে দিনে দুই জনে মিলে মিশে পুটকি মারা দিস':
  en='Tomorrow, the two of you get together and fuck some ass.'
 if bn=='পুটকির বাল ছিঁইড়া নাকের নিচে লাগাইছোস বাইঞ্চোত':
  en='You ripped pubic hair from someone’s asshole and stuck it under your nose, you sisterfucker.'
 if bn=='ভায়া আপনার ছবি দেইখা মনডা চাইতাছে। আপনাকে মহাশুন্যে নিয়া জাইয়া।।।এলিয়েন দিয়া পুটকি মারাই':
  en='Brother, seeing your photo makes me want to take you into outer space and have aliens fuck you in the ass.'
 # Preserve accusatory rhetorical questions and counterfactual negation.
 if bn.startswith('লজ্জা করে না এসব বলতে'):
  tail=en.split(',',1)[1].strip() if ',' in en else ''
  if tail:
   en="Aren't you ashamed to say things like that? "+tail[0].upper()+tail[1:]
  else:
   en="Aren't you ashamed to say things like that?"
 if bn.startswith('লজ্জা থাকলে এসব বলতে না') or bn.startswith('লজ্জা থাকলে এসব বলতি না'):
  tail=en.split(',',1)[1].strip() if ',' in en else ''
  en="If you had any shame, you wouldn't say things like that."+((' '+tail[0].upper()+tail[1:]) if tail else '')
 if bn.startswith('লজ্জা থাকলে চুপ থাকতে'):
  tail=en.split(',',1)[1].strip() if ',' in en else ''
  en="If you had any shame, you'd keep quiet."+((' '+tail[0].upper()+tail[1:]) if tail else '')
 if bn.startswith('তোর মতো') and 'মুখে এসব কথা মানায় না, লজ্জা করে না তোর' in bn:
  slur=bn.split('তোর মতো ',1)[1].split('র মুখে',1)[0]
  words={'ধান্দাবাজে':'schemer','চরিত্রহীনে':'shameless scoundrel','প্রতারকে':'fraud','ইতরে':'lout','স্বার্থপরে':'selfish person','বদমাশে':'scoundrel','জানোয়ারে':'beast'}
  person=words.get(slur,None)
  if person: en=f"That's rich coming from a {person} like you. Aren't you ashamed?"
 if bn=='গবেষণা প্রকল্প নিয়ে আমার কিছুটা ভিন্ন অভিজ্ঞতা হয়েছে।':
  en="I've had a somewhat different experience with the research project."
 if bn=='তুমি পারফরম্যান্স রিভিউ নিয়ে এই লক্ষ্যমাত্রা কখনোই পূরণ করতে পারবে না, দেখে নিও।':
  en="You'll never meet this performance-review target, just you wait."
 if 'উন্নাসিক' in bn:
  en=re.sub(r'\bhypocrite\b','arrogant snob',en,flags=re.I)
 if 'দুর্বিনীত' in bn:
  en=re.sub(r'\ba coward\b','an insolent person',en,flags=re.I)
  en=re.sub(r'\bcoward\b','insolent person',en,flags=re.I)
 if 'নির্লিপ্ত' in bn:
  en=re.sub(r'\bcareless person\b','indifferent person',en,flags=re.I)
 if 'বাচাল' in bn:
  en=re.sub(r'\ba talker\b','a blabbermouth',en,flags=re.I)
 if 'কাণ্ডজ্ঞানহীন' in bn:
  en=re.sub(r'\ba fool\b','a clueless fool',en,flags=re.I)
 if 'গোঁয়ার' in bn:
  en=re.sub(r'\ba fool\b','a stubborn fool',en,flags=re.I)
 if bn.startswith('ধুর বাল'):
  en=re.sub(r'^Damn','Fuck',en)
 if bn.startswith('এই বালের ব্যাপারটা'):
  en=re.sub(r'\b(?:hair|whole|this) thing\b','fucking thing',en,flags=re.I)
 if bn.startswith('ধুর, বালের মতো অবস্থা'):
  en='Fuck, things are a complete mess.'+((' '+en.split('.',1)[1].strip()) if '.' in en and en.split('.',1)[1].strip() else '')
 return en

records=[];missing=[];residual=[];changed=0
for ix,o in enumerate(original):
 out=dict(o)
 for key in ('previous_reply','target_reply'):
  bn=o[key]
  if bn in m:
   en=corrected(bn,m[bn]);out[key]=en
   if en!=m[bn]: changed+=1
   if re.search(r'[\u0980-\u09ff]',en): residual.append((ix,key,en[:100]))
  else:
   out[key]=bn;missing.append((ix,key,bn))
 records.append(out)

output=BASE+('bangla_context_toxicity_train_final_ENGLISH.csv' if not missing else 'bangla_context_toxicity_train_PARTIAL_ENGLISH.csv')
with open(output,'w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(original[0]));w.writeheader();w.writerows(records)
with open(BASE+'translation_QA_report.json','w',encoding='utf-8') as f:
 json.dump({'rows':len(records),'unique_translated':len(m),'texts_translated':len(records)*2-len(missing),'texts_missing':len(missing),'unprocessed_batches':errors[:200],'batch_issues_count':len(errors),'remaining_items':missing[:40],'Bengali_in_english':residual[:100],'replacements':changed,'output':output},f,ensure_ascii=False,indent=2)
print('OUTPUT',output,'rows',len(records),'untranslated fields',len(missing),'batch issues',len(errors),'residual bn',len(residual),'source-aware changes',changed)
print('sample errors',errors[:8])
print('sample missing',missing[:5])
