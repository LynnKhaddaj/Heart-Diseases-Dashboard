import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ——————————————————————————————
# 0) PAGE CONFIG & CSS
# ——————————————————————————————
st.set_page_config(page_title="Heart Disease Dashboard", layout="wide")
st.markdown("""
    <style>
      .block-container { padding-top: 0rem; }
      .main-title { font-size: 2.1rem; margin-bottom: 0.7rem; }
      .chart-title { font-size: 1.08rem; margin: 0.3rem 0 0.7rem 0; font-weight:600; }
      .element-container:has(.js-plotly-plot) {
          background: #fff;
          border-radius: 15px;
          box-shadow: 0 2px 8px 0 rgba(60,60,60,0.09), 0 0.5px 1.5px 0 rgba(0,0,0,0.05);
          border: 1px solid #edeef2;
          padding: 16px 8px 8px 8px;
          margin-bottom: 16px;
      }
    </style>
""", unsafe_allow_html=True)

# ——————————————————————————————
# 1) LOAD & PREPROCESS
# ——————————————————————————————
@st.cache_data
def load_data():
    df = pd.read_csv("heart_cleaned_fe.csv")
    bins = [29, 40, 50, 60, 70, df.age.max()]
    labels = ['30-40','41-50','51-60','61-70','71+']
    df['Age Group'] = pd.cut(df.age, bins=bins, labels=labels)
    return df

df = load_data()

# ——————————————————————————————
# 2) SIDEBAR FILTERS
# ——————————————————————————————
st.sidebar.header("Filters")
cp  = st.sidebar.multiselect("Chest Pain Type", df.chest_pain_type.unique(), df.chest_pain_type.unique())
ecg = st.sidebar.selectbox("Resting ECG", ['All'] + df.resting_ecg.unique().tolist())
ag  = st.sidebar.multiselect("Age Group", df['Age Group'].cat.categories.tolist(), df['Age Group'].cat.categories.tolist())
ang = st.sidebar.checkbox("Exercise-Induced Angina: Yes")
sex = st.sidebar.selectbox("Sex", ['All','Male','Female'])

d = df[df.chest_pain_type.isin(cp)]
if ecg!='All': d = d[d.resting_ecg==ecg]
d = d[d['Age Group'].isin(ag)]
if ang:        d = d[d['Exercise-Induced Angina: Yes']==1]
if sex!='All':
    val = 1 if sex=='Male' else 0
    d = d[d['Sex: Male']==val]

# ——————————————————————————————
# 3) TITLE
# ——————————————————————————————
st.markdown("<div class='main-title'>💓 Heart Disease Dashboard</div>", unsafe_allow_html=True)

# ——————————————————————————————
# 4) LAYOUT & CHARTS (2×3 GRID)
# ——————————————————————————————
tile_h = 250
marg   = dict(l=20, r=20, t=20, b=20)

top = st.columns(3)
bot = st.columns(3)

# Row1 Col1: Chest Pain % by Age Group
with top[0]:
    st.markdown("<div class='chart-title'>Chest Pain % by Age Group</div>", unsafe_allow_html=True)
    mos = d.groupby(['Age Group','chest_pain_type']).size().reset_index(name='count')
    mos['pct'] = mos['count']/mos.groupby('Age Group')['count'].transform('sum')
    fig1 = px.bar(
        mos, x='Age Group', y='pct', color='chest_pain_type',
        barmode='stack', color_discrete_sequence=px.colors.qualitative.Safe,
        labels={'pct':'% Patients'}
    )
    fig1.update_layout(height=tile_h, margin=marg, yaxis_tickformat='.0%', showlegend=False)
    st.plotly_chart(fig1, use_container_width=True, key="fig1")

# Row1 Col2: ECG Count & Disease %
with top[1]:
    st.markdown("<div class='chart-title'>ECG Count & Disease %</div>", unsafe_allow_html=True)
    ct = d.resting_ecg.value_counts().reset_index(name='count')
    ct.columns = ['ecg','count']
    rt = d.groupby('resting_ecg')['heart_disease'].mean().reset_index(name='rate')
    rt['rate'] *= 100
    df_e = ct.merge(rt, left_on='ecg', right_on='resting_ecg')
    fig2 = make_subplots(specs=[[{'secondary_y':True}]])
    fig2.add_trace(go.Bar(x=df_e['ecg'], y=df_e['count'], marker_color='teal'), secondary_y=False)
    fig2.add_trace(go.Scatter(x=df_e['ecg'], y=df_e['rate'], mode='lines+markers', marker_color='crimson'), secondary_y=True)
    fig2.update_layout(height=tile_h, margin=marg, showlegend=False)
    fig2.update_yaxes(title_text='Count', secondary_y=False)
    fig2.update_yaxes(title_text='Disease %', secondary_y=True, tickformat='.0f')
    st.plotly_chart(fig2, use_container_width=True, key="fig2")

# Row1 Col3: Heatmap: Age vs ST Slope
with top[2]:
    st.markdown("<div class='chart-title'>Heatmap: Age Group vs ST Slope</div>", unsafe_allow_html=True)
    heat = d.groupby(['Age Group','st_slope'])['heart_disease'].mean().reset_index()
    heat = heat.pivot(index='Age Group', columns='st_slope', values='heart_disease') * 100
    fig3 = px.imshow(
        heat, text_auto='.1f',
        color_continuous_scale=['royalblue','firebrick'],
        labels={'color':'Disease %'}
    )
    fig3.update_layout(height=tile_h, margin=marg)
    st.plotly_chart(fig3, use_container_width=True, key="fig3")

# Row2 Col1: Disease % by Chest Pain Type (Bubble)
with bot[0]:
    st.markdown("<div class='chart-title'>Disease % by Chest Pain Type</div>", unsafe_allow_html=True)
    df4 = (
        d.groupby(['Sex: Male','chest_pain_type'])
         .agg(count=('heart_disease','size'),
              rate =('heart_disease','mean'))
         .reset_index()
    )
    df4['rate'] *= 100
    df4['Sex'] = df4['Sex: Male'].map({0:'Female',1:'Male'})
    fig4 = px.scatter(
        df4,
        x='chest_pain_type',
        y='rate',
        size='count',
        color='Sex',
        size_max=40,
        labels={'chest_pain_type':'Chest Pain Type','rate':'Disease %','count':'N'},
        hover_data={'count':True,'rate':':.1f'}
    )
    fig4.update_traces(marker=dict(opacity=0.7, line=dict(width=1, color='DarkSlateGrey')))
    fig4.update_layout(
        height=tile_h, margin=marg,
        yaxis=dict(range=[0,100], ticksuffix='%'),
        xaxis_title='Chest Pain Type',
        legend_title='Sex'
    )
    st.plotly_chart(fig4, use_container_width=True, key="fig4")

# Row2 Col2: Absolute Correlation with Heart Disease (includes fasting_bs)
with bot[1]:
    st.markdown("<div class='chart-title'>Abs Correlation with Heart Disease</div>", unsafe_allow_html=True)
    cols = ['age','resting_bp','cholesterol','max_hr','oldpeak','fasting_bs']
    if d['Sex: Male'].nunique()>1:
        cm = (d[d['Sex: Male']==1][cols+['heart_disease']].corr()['heart_disease'].abs()
                .drop('heart_disease').reset_index(name='corr'))
        cf = (d[d['Sex: Male']==0][cols+['heart_disease']].corr()['heart_disease'].abs()
                .drop('heart_disease').reset_index(name='corr'))
        th = cm['index']
        fig5 = go.Figure()
        fig5.add_trace(go.Scatterpolar(theta=th, r=cm['corr'], name='Male',
                                       fill='toself', line_color='royalblue'))
        fig5.add_trace(go.Scatterpolar(theta=th, r=cf['corr'], name='Female',
                                       fill='toself', line_color='firebrick'))
        fig5.update_layout(polar=dict(radialaxis=dict(visible=True, tickformat='.2f')),
                           height=tile_h, margin=marg)
    else:
        c0 = (d[cols+['heart_disease']].corr()['heart_disease'].abs()
               .drop('heart_disease').reset_index(name='corr'))
        fig5 = px.bar_polar(
            c0, r='corr', theta='index',
            color='corr', color_continuous_scale=['royalblue','firebrick'],
            labels={'corr':'|Corr|','index':'Feature'}
        )
        fig5.update_layout(height=tile_h, margin=marg, showlegend=False)
    st.plotly_chart(fig5, use_container_width=True, key="fig5")

# Row2 Col3: Trend: Age Group & Chest Pain
with bot[2]:
    st.markdown("<div class='chart-title'>Trend: Age Group & Chest Pain</div>", unsafe_allow_html=True)
    ln = d.groupby(['Age Group','chest_pain_type'])['heart_disease'].mean().reset_index(name='rate')
    fig6 = px.line(
        ln, x='Age Group', y='rate', color='chest_pain_type', markers=True,
        labels={'rate':'Disease %'}
    )
    fig6.update_layout(height=tile_h, margin=marg, showlegend=False)
    fig6.update_yaxes(tickformat='.0%', range=[0,1])
    st.plotly_chart(fig6, use_container_width=True, key="fig6")

st.markdown("---")
st.write("*Use the sidebar filters to refresh all six panels.*")

