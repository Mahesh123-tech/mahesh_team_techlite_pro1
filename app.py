import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Hospital Emergency Room (ER) Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR MODERN INDUSTRIAL UI ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid #008080;
    }
    div[data-testid="stExpander"] {
        background-color: #ffffff;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- DATA LOADER / SYNTHETIC GENERATOR ---
@st.cache_data
def load_data():
    try:
        # Load actual file matching the schema
        df = pd.read_csv("Hospital ER_Data.csv")
    except FileNotFoundError:
        # Auto-generation fallback mirroring the user's specific dataset schema
        np.random.seed(42)
        n_rows = 1500
        start_date = datetime(2026, 1, 1)
        
        departments = ['General Medicine', 'Orthopedics', 'Cardiology', 'Pediatrics', 'Neurology', 'None']
        races = ['White', 'Black/African American', 'Asian', 'Hispanic/Latino', 'Other']
        genders = ['Male', 'Female', 'Other']
        
        data = {
            'Patient Id': [f"ER-{i:05d}" for i in range(1, n_rows + 1)],
            'Patient Admission Date': [(start_date + timedelta(days=np.random.randint(0, 90), 
                                                                hours=np.random.randint(0, 24), 
                                                                minutes=np.random.randint(0, 60))) for _ in range(n_rows)],
            'Patient First Inital': [chr(np.random.randint(65, 91)) for _ in range(n_rows)],
            'Patient Last Name': [f"Patient_{i}" for i in range(n_rows)],
            'Patient Gender': np.random.choice(genders, n_rows, p=[0.48, 0.49, 0.03]),
            'Patient Age': np.random.randint(0, 100, n_rows),
            'Patient Race': np.random.choice(races, n_rows, p=[0.55, 0.18, 0.12, 0.11, 0.04]),
            'Department Referral': np.random.choice(departments, n_rows, p=[0.35, 0.15, 0.20, 0.15, 0.10, 0.05]),
            'Patient Admission Flag': np.random.choice([True, False], n_rows, p=[0.32, 0.68]),
            'Patient Satisfaction Score': np.random.choice([1, 2, 3, 4, 5], n_rows, p=[0.06, 0.12, 0.22, 0.40, 0.20]),
            'Patient Waittime': np.random.randint(5, 220, n_rows),
            'Patients CM': np.random.randint(100, 600, n_rows)
        }
        df = pd.DataFrame(data)
    
    # Preprocessing
    df['Patient Admission Date'] = pd.to_datetime(df['Patient Admission Date'])
    df['Admission Day'] = df['Patient Admission Date'].dt.date
    df['Admission Hour'] = df['Patient Admission Date'].dt.hour
    return df

df = load_data()

# --- SIDEBAR INTERACTIVE CONTROLS ---
st.sidebar.image("https://img.icons8.com/fluent/96/000000/hospital-room.png", width=80)
st.sidebar.title("ER Analytics Control Center")
st.sidebar.markdown("Filter options for cross-sectional patient tracking.")

# Date Filter Slider
min_date, max_date = df['Admission Day'].min(), df['Admission Day'].max()
date_range = st.sidebar.date_input("Admission Date Window", [min_date, max_date], min_value=min_date, max_value=max_date)

# Category Multi-selects
gender_sel = st.sidebar.multiselect("Gender Selection", options=df['Patient Gender'].unique(), default=df['Patient Gender'].unique())
race_sel = st.sidebar.multiselect("Race/Ethnicity", options=df['Patient Race'].unique(), default=df['Patient Race'].unique())
dept_sel = st.sidebar.multiselect("Referral Department", options=df['Department Referral'].unique(), default=df['Department Referral'].unique())
admission_status = st.sidebar.radio("Inpatient Admission Status", ["All Patients", "Admitted Only", "Discharged Only"])

# Applying Filters Dynamically
filtered_df = df[
    (df['Patient Gender'].isin(gender_sel)) &
    (df['Patient Race'].isin(race_sel)) &
    (df['Department Referral'].isin(dept_sel))
]

if len(date_range) == 2:
    filtered_df = filtered_df[(filtered_df['Admission Day'] >= date_range[0]) & (filtered_df['Admission Day'] <= date_range[1])]

if admission_status == "Admitted Only":
    filtered_df = filtered_df[filtered_df['Patient Admission Flag'] == True]
elif admission_status == "Discharged Only":
    filtered_df = filtered_df[filtered_df['Patient Admission Flag'] == False]

# --- MAIN INTERFACE LAYOUT ---
st.title("🏥 Hospital Emergency Room Optimization Engine")
st.caption("Advanced operational intelligence system designed for clinical throughput, demographic insights, and resource profiling.")

if filtered_df.empty:
    st.error("❌ No observations match your active filters. Modify parameters in the sidebar panel to restore data view.")
else:
    # --- METRIC SCOREBOARD (KPIs) ---
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    total_visits = len(filtered_df)
    avg_wait_time = filtered_df['Patient Waittime'].mean()
    avg_satisfaction = filtered_df['Patient Satisfaction Score'].mean()
    admission_pct = (filtered_df['Patient Admission Flag'].sum() / total_visits) * 100 if total_visits > 0 else 0

    with kpi_col1:
        st.metric(label="Total ER Volume", value=f"{total_visits:,} Patients")
    with kpi_col2:
        st.metric(label="Average Wait Time", value=f"{avg_wait_time:.1f} Mins", 
                  delta=f"{avg_wait_time - df['Patient Waittime'].mean():.1f} mins vs Baseline", delta_color="inverse")
    with kpi_col3:
        st.metric(label="Avg Satisfaction Rating", value=f"{avg_satisfaction:.2f} / 5.0")
    with kpi_col4:
        st.metric(label="Inpatient Admission Rate", value=f"{admission_pct:.1f}%")

    st.markdown("---")

    # --- TABBED ANALYTICS SECTIONS ---
    tab_ops, tab_demo, tab_satisfaction, tab_raw = st.tabs([
        "🕒 Operational Flow & Throughput", 
        "👥 Patient Profiling & Demographics", 
        "⭐ Experience & Clinical Metrics", 
        "📋 Data Ledger & Export"
    ])

    # TAB 1: OPERATIONAL FLOW
    with tab_ops:
        st.header("Throughput Logistics & Load Tracking")
        
        col_ops1, col_ops2 = st.columns(2)
        with col_ops1:
            st.subheader("Patient Volume Timeline Trends")
            daily_series = filtered_df.groupby('Admission Day').size().reset_index(name='Patient Admissions')
            fig_trend = px.line(daily_series, x='Admission Day', y='Patient Admissions', markers=True,
                                template='plotly_white', color_discrete_sequence=['#008080'])
            st.plotly_chart(fig_trend, use_container_width=True)
            
        with col_ops2:
            st.subheader("Hourly Peak Demand Load (24-Hour Cycle)")
            hourly_series = filtered_df.groupby('Admission Hour').size().reset_index(name='Patient Traffic')
            fig_hour = px.bar(hourly_series, x='Admission Hour', y='Patient Traffic',
                              template='plotly_white', color_discrete_sequence=['#4682B4'])
            st.plotly_chart(fig_hour, use_container_width=True)

        col_ops3, col_ops4 = st.columns(2)
        with col_ops3:
            st.subheader("Mean Wait Times by Referral Department")
            dept_w = filtered_df.groupby('Department Referral')['Patient Waittime'].mean().sort_values(ascending=True).reset_index()
            fig_dept_w = px.bar(dept_w, x='Patient Waittime', y='Department Referral', orientation='h',
                                color='Patient Waittime', color_continuous_scale='Turbo', template='plotly_white')
            st.plotly_chart(fig_dept_w, use_container_width=True)
            
        with col_ops4:
            st.subheader("Clinical Conversion Rates by Department")
            dept_a = filtered_df.groupby('Department Referral')['Patient Admission Flag'].mean().reset_index()
            dept_a['Admission Percentage'] = dept_a['Patient Admission Flag'] * 100
            dept_a = dept_a.sort_values(by='Admission Percentage', ascending=False)
            fig_dept_a = px.bar(dept_a, x='Department Referral', y='Admission Percentage',
                                template='plotly_white', color_discrete_sequence=['#2E8B57'])
            st.plotly_chart(fig_dept_a, use_container_width=True)

        with st.expander("💡 Operational Insights Report"):
            max_hour = hourly_series.loc[hourly_series['Patient Traffic'].idxmax(), 'Admission Hour']
            slowest_dept = dept_w.iloc[-1]['Department Referral']
            highest_adm_dept = dept_a.iloc[0]['Department Referral']
            st.markdown(f"""
            - **Peak Operational Load:** The highest patient arrival frequency occurs during the **{max_hour}:00** hour mark. Cross-train staff or shift schedules to cover this block.
            - **Bottleneck Warning:** The **{slowest_dept}** sector shows the highest average wait duration. Internal cycle optimization is recommended for this department.
            - **Inpatient Drivers:** **{highest_adm_dept}** reports the highest transition into static inpatient status, signaling highly acute incoming cases.
            """)

    # TAB 2: DEMOGRAPHICS
    with tab_demo:
        st.header("Patient Population & Demographic Profiles")
        
        col_dem1, col_dem2 = st.columns(2)
        with col_dem1:
            st.subheader("Age Stratification & Density Profile")
            fig_age = px.histogram(filtered_df, x='Patient Age', nbins=20, marginal='violin',
                                   template='plotly_white', color_discrete_sequence=['#9370DB'])
            st.plotly_chart(fig_age, use_container_width=True)
            
        with col_dem2:
            st.subheader("Gender Representation Core Distribution")
            g_counts = filtered_df['Patient Gender'].value_counts().reset_index(name='Count')
            fig_gender = px.pie(g_counts, values='Count', names='Patient Gender', hole=0.45,
                                template='plotly_white', color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_gender, use_container_width=True)

        st.subheader("Patient Breakdown by Registered Race/Ethnicity")
        r_counts = filtered_df['Patient Race'].value_counts().sort_values(ascending=True).reset_index(name='Count')
        fig_race = px.bar(r_counts, x='Count', y='Patient Race', orientation='h',
                          color='Count', color_continuous_scale='Mint', template='plotly_white')
        st.plotly_chart(fig_race, use_container_width=True)

    # TAB 3: SATISFACTION & CLINICAL METRICS
    with tab_satisfaction:
        st.header("Patient Experience Metrics & Resource Correlation")
        
        col_sat1, col_sat2 = st.columns(2)
        with col_sat1:
            st.subheader("Impact of Wait Duration on Experience Rating")
            # Downsample plot elements for clean performance boundaries
            sample_sz = min(len(filtered_df), 600)
            scatter_df = filtered_df.sample(sample_sz)
            fig_scat = px.scatter(scatter_df, x='Patient Waittime', y='Patient Satisfaction Score',
                                  color='Patient Admission Flag', opacity=0.7,
                                  labels={'Patient Waittime': 'Wait Time (Mins)', 'Patient Satisfaction Score': 'Satisfaction Score (1-5)'},
                                  template='plotly_white')
            st.plotly_chart(fig_scat, use_container_width=True)
            
        with col_sat2:
            st.subheader("Average Experience Scores across Specialties")
            dept_s = filtered_df.groupby('Department Referral')['Patient Satisfaction Score'].mean().sort_values(ascending=False).reset_index()
            fig_dept_s = px.bar(dept_s, x='Patient Satisfaction Score', y='Department Referral', orientation='h',
                                color='Patient Satisfaction Score', color_continuous_scale='Cividis', template='plotly_white')
            st.plotly_chart(fig_dept_s, use_container_width=True)

        st.subheader("Case Management Metric (Patients CM) vs Waiting Matrix")
        fig_cm = px.scatter(filtered_df.sample(min(len(filtered_df), 400)), x='Patients CM', y='Patient Waittime',
                            size='Patient Age', color='Patient Satisfaction Score', 
                            template='plotly_white', color_continuous_scale='Plasma')
        st.plotly_chart(fig_cm, use_container_width=True)
        st.caption("Bubble Size correlates to Patient Age. Position tracks Case Management Index against Wait Time lines.")

    # TAB 4: DATA LEDGER & EXPORT CONSOLE
    with tab_raw:
        st.header("Granular Data Explorer")
        st.markdown("Inspect or isolate filtered historical records directly.")
        st.dataframe(filtered_df, use_container_width=True)
        
        csv_buffer = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Structured View Sub-cohort (CSV)",
            data=csv_buffer,
            file_name=f"er_filtered_dataset_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
