import streamlit as st
import pandas as pd
import io
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
for file in uploaded:
    content = file.read()
    df = pd.read_excel(io.BytesIO(content), engine='openpyxl')
    dfs.append(df)
data = pd.concat(dfs, ignore_index=True)

# 4) 경력 그룹 설정
bins = [1, 5, 10, float('inf')]
labels = ['1-4년차', '5-9년차', '10년차 이상']
if '직무연차' in data.columns:
    years = data['직무연차'].str.extract(r'(\d+)')[0].astype(int)
    data['경력그룹'] = pd.cut(years, bins=bins, labels=labels, right=False)
else:
    data['경력그룹'] = pd.Categorical([], categories=labels)

# 5) 불용어 및 패턴
stopwords = {
    '대한','통해','그리고','하지만','있습니다','합니다','하는',
    '되어','될','했습니다','입니다','위해','희망','분야의'
}
# 불필요한 어미 필터
ending_pattern = re.compile(
    r'(다|입니다|이다|합니다|한다|었|했|어요|에|하고|함으로서|하여|으로는|로서|니까|여서|이므로|바탕으로)$'
)
# 조사 및 어미를 제거하여 기본형만 남김
norm_pattern = re.compile(
    r'(은|는|이|가|을|를|과|와|의|도|게|도록|이다|입니다|하게|하도록)$'
)

# 6) 키워드 추출 함수
def extract_keywords(df, role, top_n=10):
    df_role = df if role=='전체' else df[df['직무']==role]
    results = {}
    for grp in labels:
        texts = df_role.loc[
            df_role['경력그룹']==grp,
            '(2) 성장/역량/커리어-구성원 의견'
        ].dropna().astype(str)
        ctr = Counter()
        for doc in texts:
            for token in re.findall(r'[가-힣]{2,}', doc):
                # 1) 원형 필터
                if token in stopwords:
                    continue
                # 2) 어미 필터
                if ending_pattern.search(token):
                    token = ending_pattern.sub('', token)
                # 3) 조사 및 기타 접미사 제거
                base = norm_pattern.sub('', token)
                # 4) 최종 불용어 및 길이 필터
                if base in stopwords or len(base) < 2:
                    continue
                ctr[base] += 1
        results[grp] = ctr.most_common(top_n)
    return results

# 캐시 적용
extract_keywords = st.cache_data(extract_keywords)

# 7) 사이드바: 직무 선택
drop_roles = ['전체'] + data['직무'].dropna().unique().tolist()
selected = st.sidebar.selectbox('직무 선택', drop_roles)

# 8) 결과 추출 및 시각화
results = extract_keywords(data, selected, top_n=10)
cols = st.columns(len(labels))
for col, grp in zip(cols, labels):
    with col:
        st.subheader(grp)
        items = results.get(grp, [])
        if not items:
            st.write('응답 없음')
        else:
            df_kw = pd.DataFrame(items, columns=['키워드','빈도'])
            fig = px.bar(df_kw, x='키워드', y='빈도', text='빈도')
            fig.update_traces(hovertemplate='<b>%{x}</b><br>응답자 수: %{y}<extra></extra>')
            fig.update_layout(xaxis_tickangle=45, margin=dict(t=20,b=20))
            st.plotly_chart(fig, use_container_width=True)
