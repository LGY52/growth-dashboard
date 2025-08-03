import streamlit as st
import pandas as pd, io
from konlpy.tag import Okt
from collections import Counter
import plotly.express as px

st.set_page_config(page_title='성장 키워드 대시보드', layout='wide')
st.title('연차별·직무별 성장 키워드 대시보드')

uploaded = st.file_uploader(
    '1~4분기 엑셀 파일 업로드', type='xlsx', accept_multiple_files=True
)
if not uploaded:
    st.info('엑셀 파일을 업로드해주세요.')
    st.stop()

dfs = [
    pd.read_excel(io.BytesIO(f.read()), engine='openpyxl')
    for f in uploaded
]
data = pd.concat(dfs, ignore_index=True)

bins = [1,5,10,float('inf')]
labels = ['1-4년차','5-9년차','10년차 이상']
data['경력그룹'] = pd.cut(
    data['직무연차'].str.extract(r'(\d+)')[0].astype(int),
    bins=bins, labels=labels, right=False
)

okt = Okt()
stopwords = {
    '대한','통해','그리고','하지만','있습니다','합니다','하는',
    '되어','될','했습니다','입니다','위해','희망'
}

@st.cache_data
def extract_keywords(df, role):
    res = {}
    subset = df[df['직무']==role]
    for grp in labels:
        texts = subset.loc[
            subset['경력그룹']==grp,
            '(2) 성장/역량/커리어-구성원 의견'
        ].dropna()
        ctr = Counter()
        for doc in texts:
            nouns = okt.nouns(doc)
            ctr.update([n for n in nouns if len(n)>1 and n not in stopwords])
        res[grp] = ctr.most_common(10)
    return res

roles = data['직무'].unique().tolist()
selected = st.sidebar.selectbox('직무 선택', roles)
results = extract_keywords(data, selected)

cols = st.columns(len(labels))
for col, grp in zip(cols, labels):
    with col:
        st.subheader(grp)
        top10 = results.get(grp, [])
        if not top10:
            st.write('응답 없음')
        else:
            df_kw = pd.DataFrame(top10, columns=['키워드','빈도'])
            fig = px.bar(df_kw, x='키워드', y='빈도', text='빈도')
            fig.update_traces(
                hovertemplate='<b>%{x}</b><br>응답자 수: %{y}<extra></extra>'
            )
            fig.update_layout(xaxis_tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
