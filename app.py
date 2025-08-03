import streamlit as st
import pandas as pd, io
import re
from collections import Counter
import plotly.express as px

# 1) 페이지 설정
st.set_page_config(page_title='성장 키워드 대시보드', layout='wide')
st.title('연차·직무별 성장 키워드 대시보드')

# 2) 엑셀 파일 업로드
uploaded = st.file_uploader(
    '1~4분기 엑셀 파일 업로드',
    type='xlsx',
    accept_multiple_files=True
)
if not uploaded:
    st.info('엑셀 파일을 업로드하면 분석을 시작합니다.')
    st.stop()

# 3) 데이터 병합
dfs = []
for f in uploaded:
    df = pd.read_excel(io.BytesIO(f.read()), engine='openpyxl')
    dfs.append(df)
data = pd.concat(dfs, ignore_index=True)

# 4) 경력 그룹
bins = [1, 5, 10, float('inf')]
labels = ['1-4년차', '5-9년차', '10년차 이상']
years = data['직무연차'].str.extract(r'(\d+)')[0].astype(int)
data['경력그룹'] = pd.cut(years, bins=bins, labels=labels, right=False)

# 5) 불용어 및 패턴
stopwords = {
    '대한','통해','그리고','하지만','있습니다','합니다','하는',
    '되어','될','했습니다','입니다','위해','희망','분야의'
}
ending_pattern = re.compile(
    r'(다|합니다|입니다|이다|한다|었|했|어요|에|하고|함으로서|'
    r'하여|으로는|로서|니까|여서|이므로|바탕으로)$'
)
norm_pattern = re.compile(
    r'(으로는|으로|로는|로|로서|와|과|이|가|은|는|의|도|게|도록)$'
)

# 6) 키워드 추출 함수
@st.cache_data
def extract_keywords(df, role, top_n=10):
    df_role = df if role == '전체' else df[df['직무']==role]
    out = {}
    for grp in labels:
        texts = df_role.loc[
            df_role['경력그룹']==grp,
            '(2) 성장/역량/커리어-구성원 의견'
        ].dropna().astype(str)
        ctr = Counter()
        for doc in texts:
            for t in re.findall(r'[가-힣]{2,}', doc):
                if t in stopwords or ending_pattern.search(t):
                    continue
                base = norm_pattern.sub('', t)
                if base in stopwords or len(base)<2:
                    continue
                ctr[base] += 1
        out[grp] = ctr.most_common(top_n)
    return out

# 7) “문서 보기” 함수: 키워드 포함 문장 필터링
@st.cache_data
def get_documents(df, role, grp, keyword):
    df_role = df if role == '전체' else df[df['직무']==role]
    subset = df_role[df_role['경력그룹']==grp]
    docs = subset['(2) 성장/역량/커리어-구성원 의견'].dropna().astype(str)
    return [d for d in docs if re.search(re.escape(keyword), d)]

# 8) 사이드바: 직무 선택 (전체 포함)
roles = ['전체'] + data['직무'].dropna().unique().tolist()
selected = st.sidebar.selectbox('직무 선택', roles)

# 9) 추출 & 시각화 + 문서 보기
results = extract_keywords(data, selected, top_n=10)
cols = st.columns(len(labels))

for col, grp in zip(cols, labels):
    with col:
        st.subheader(grp)
        items = results[grp]
        if not items:
            st.write('응답 없음')
            continue

        # 9-1) 막대그래프
        df_kw = pd.DataFrame(items, columns=['키워드','빈도'])
        fig = px.bar(df_kw, x='키워드', y='빈도', text='빈도')
        fig.update_traces(
            hovertemplate='<b>%{x}</b><br>응답자 수: %{y}<extra></extra>'
        )
        fig.update_layout(xaxis_tickangle=45, margin=dict(t=20,b=20))
        st.plotly_chart(fig, use_container_width=True)

        # 9-2) 키워드 선택 박스
        sel_kw = st.selectbox(f"{grp} 문서 보기", [''] + [w for w,_ in items])
        if sel_kw:
            docs = get_documents(data, selected, grp, sel_kw)
            with st.expander(f"‘{sel_kw}’ 포함 면담 문서 {len(docs)}건 보기"):
                for d in docs:
                    st.write(f"- {d}")

