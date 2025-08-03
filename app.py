import streamlit as st
import pandas as pd, io
import re
from collections import Counter
import plotly.express as px

# 1) 페이지 설정
st.set_page_config(page_title='성장 키워드 대시보드', layout='wide')
st.title('연차·직무별 성장 키워드 대시보드')

# 2) 엑셀 파일 업로드 UI
uploaded = st.file_uploader(
    '1~4분기 엑셀 파일 업로드',
    type='xlsx',
    accept_multiple_files=True
)
if not uploaded:
    st.info('엑셀 파일을 업로드하면 자동으로 분석을 시작합니다.')
    st.stop()

# 3) 데이터 로드 & 병합
dfs = [
    pd.read_excel(io.BytesIO(f.read()), engine='openpyxl')
    for f in uploaded
]
data = pd.concat(dfs, ignore_index=True)

# 4) 경력 그룹 나누기
bins = [1, 5, 10, float('inf')]
labels = ['1-4년차', '5-9년차', '10년차 이상']
data['경력그룹'] = pd.cut(
    data['직무연차'].str.extract(r'(\d+)')[0].astype(int),
    bins=bins, labels=labels, right=False
)

# 5) 불용어 사전
stopwords = {
    '대한','통해','그리고','하지만','있습니다','합니다','하는',
    '되어','될','했습니다','입니다','위해','희망'
}

# 6) 키워드 추출 함수
@st.cache_data
def extract_keywords(df, role, top_n=10):
    out = {}
    subset = df[df['직무']==role]
    for grp in labels:
        texts = subset.loc[
            subset['경력그룹']==grp,

            subset['경력그룹']==grp
