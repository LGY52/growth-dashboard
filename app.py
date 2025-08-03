@@
- from konlpy.tag import Okt
+ import re

@@
- okt = Okt()
- stopwords = {
+ # 정규표현식 기반 토큰화 + 불용어 목록
+ stopwords = {
     '대한','통해','그리고','하지만','있습니다','합니다','하는',
     '되어','될','했습니다','입니다','위해','희망'
 }

@@
- @st.cache_data
- def extract_keywords(df, role):
+ @st.cache_data
+ def extract_keywords(df, role):
     res = {}
     subset = df[df['직무']==role]
     for grp in labels:
         texts = subset.loc[
             subset['경력그룹']==grp,
             '(2) 성장/역량/커리어-구성원 의견'
         ].dropna()
-        ctr = Counter()
-        for doc in texts:
-            nouns = okt.nouns(doc)
-            ctr.update([n for n in nouns if len(n)>1 and n not in stopwords])
+        ctr = Counter()
+        for doc in texts:
+            # 한글 2자 이상 토큰 추출
+            tokens = re.findall(r'[가-힣]{2,}', doc)
+            filtered = [t for t in tokens if t not in stopwords]
+            ctr.update(filtered)
         res[grp] = ctr.most_common(10)
     return res

