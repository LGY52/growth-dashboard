import streamlit as st
import pandas as pd, io
import re
from collections import Counter
import plotly.express as px

st.set_page_config(page_title='성장 키워드 대시보드', layout='wide')
st.title('연차·직무별 성장 키워드 대시보드')

uploaded = st.file_uploader(
    '1~4분기 엑셀 파일 업로드',
    type='xlsx',
    accept_multiple_files=True
)
if not uploaded:
    st.info('엑셀 파일을 업로드하면 자동으로 분석을 시작합니다.')
    st.stop()

dfs = [
    pd.read_excel(io.BytesIO(f.read()), engine='openpyxl')
    for f in uploaded
]
data = pd.concat(dfs, ignore_index=True)

bins = [1, 5, 10, float('inf')]
labels = ['1-4년차', '5-9년차', '10년차 이상']
data['경력그룹'] = pd.cut(
    data['직무연차'].str.extract(r'(\d+)')[0].astype(int),
    bins=bins, labels=labels, right=False
)

stopwords = {
    '대한','통해','그리고','하지만','있습니다','합니다','하는',
    '되어','될','했습니다','입니다','위해','희망'
}

@st.cache_data
def extract_keywords(df, role, top_n=10):
    out = {}
    subset = df[df['직무'] == role]
    for grp in labels:
        texts = subset.loc[
            subset['경력그룹'] == grp,
            '(2) 성장/역량/커리어-구성원 의견'
        ].dropna()

        ctr = Counter()
        for doc in texts:
            tokens = re.findall(r'[가-힣]{2,}', doc)
            for t in tokens:
                if (
                    t not in stopwords
                    and not re.search(
                        r'(다|합니다|입니다|이다|한다|었|했|어요|에|하고|함으로서)$',
                        t
                    )
                ):
                    ctr[t] += 1
        out[grp] = ctr.most_common(top_n)
    return out

# ← HERE we fix the typo:
roles = data['직무'].unique().tolist()

selected = st.sidebar.selectbox('직무 선택', roles)

results = extract_keywords(data, selected, top_n=10)
cols = st.columns(len(labels))

for col, grp in zip(cols, labels):
    with col:
        st.subheader(grp)
        items = results.get(grp, [])
        if not items:
            st.write('응답 없음')
        else:
            df_kw = pd.DataFrame(items, columns=['키워드', '빈도'])
            fig = px.bar(
                df_kw, x='키워드', y='빈도', text='빈도'
            )
            fig.update_traces(
                hovertemplate='<b>%{x}</b><br>응답자 수: %{y}<extra></extra>'
            )
            fig.update_layout(xaxis_tickangle=45, margin=dict(t=30))
            st.plotly_chart(fig, use_container_width=True)


