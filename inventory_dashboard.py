import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 页面设置
st.set_page_config(page_title="库存库龄分析BI报表", page_icon="📊", layout="wide")

# 标题
st.title("📊 库存库龄分析BI报表")

# 加载数据
@st.cache_data
def load_data():
    df = pd.read_excel('库存库龄明细表.xlsx')
    
    # 定位列
    age_col = df.columns[18]  # S列库龄天数
    amount_col = df.columns[16]  # Q列库存金额
    item_code_col = df.columns[4]  # E列物料号
    item_name_col = df.columns[5]  # F列物料名称
    
    # 数据清洗（处理"-"字符）
    df[age_col] = df[age_col].replace('-', pd.NA).replace('', pd.NA)
    df[age_col] = pd.to_numeric(df[age_col], errors='coerce')
    
    df[amount_col] = df[amount_col].replace('-', pd.NA).replace('', pd.NA)
    df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')
    
    # 库龄分段
    def categorize_age(days):
        if pd.isna(days):
            return '未知'
        elif days <= 30:
            return '0-30天(新鲜)'
        elif days <= 90:
            return '31-90天(正常)'
        elif days <= 180:
            return '91-180天(关注)'
        elif days <= 360:
            return '181-360天(呆滞)'
        else:
            return '360天以上(严重呆滞)'
    
    df['库龄分段'] = df[age_col].apply(categorize_age)
    
    return df, age_col, amount_col, item_code_col, item_name_col

# 加载
df, age_col, amount_col, item_code_col, item_name_col = load_data()

# 侧边栏筛选
st.sidebar.header("🔍 筛选条件")
selected_categories = st.sidebar.multiselect("库龄分段", options=df['库龄分段'].unique(), default=df['库龄分段'].unique())

# 应用筛选
filtered_df = df[df['库龄分段'].isin(selected_categories)]

# 关键指标
st.subheader("📈 关键指标")
col1, col2, col3, col4 = st.columns(4)
col1.metric("总品项数", f"{len(filtered_df):,}")
total_amount = filtered_df[amount_col].sum()
col2.metric("库存总金额", f"¥{total_amount:,.2f}万")
slow_items = len(filtered_df[filtered_df['库龄分段'].isin(['181-360天(呆滞)', '360天以上(严重呆滞)'])])
col3.metric("呆滞品项数", f"{slow_items:,}")
slow_amount = filtered_df[filtered_df['库龄分段'].isin(['181-360天(呆滞)', '360天以上(严重呆滞)'])][amount_col].sum()
col4.metric("呆滞金额", f"¥{slow_amount:,.2f}万")

# 图表
st.subheader("📊 可视化")
col_left, col_right = st.columns(2)

with col_left:
    age_amount = filtered_df.groupby('库龄分段')[amount_col].sum()
    fig_pie = px.pie(values=age_amount.values, names=age_amount.index, title="库存金额库龄分布")
    st.plotly_chart(fig_pie, use_container_width=True)

with col_right:
    fig_bar = px.bar(x=age_amount.index, y=age_amount.values, title="各库龄段库存金额", labels={'x': '库龄分段', 'y': '金额(万元)'})
    st.plotly_chart(fig_bar, use_container_width=True)

# 呆滞TOP10
st.subheader("⚠️ 呆滞库存TOP10")
slow_moving = filtered_df[filtered_df['库龄分段'].isin(['181-360天(呆滞)', '360天以上(严重呆滞)'])]
if len(slow_moving) > 0:
    top_slow = slow_moving.groupby([item_code_col, item_name_col])[amount_col].sum().sort_values(ascending=False).head(10).reset_index()
    top_slow.columns = ['物料号', '物料名称', '呆滞金额(万元)']
    st.dataframe(top_slow, use_container_width=True)

# 数据下载
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button("📥 下载数据", csv, '库存库龄数据.csv', 'text/csv')
