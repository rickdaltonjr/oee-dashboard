import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import os
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="OEE Dashboard", page_icon="🏭", layout="wide")

# Custom CSS for Styling

st.markdown("""
<style>
.main-header { font-size: 2.5rem; font-weight: bold; color: #1f77b4; text-align: center; }
.kpi-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px;
            color: white; text-align: center; }
.kpi-value { font-size: 2.5rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)
def get_database_path():
    """Locate the database file in different possible directory structures"""
    if os.path.exists('../database/oee_database.db'):
        return '../database/oee_database.db'
    elif os.path.exists('database/oee_database.db'):
        return 'database/oee_database.db'

    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, 'database', 'oee_database.db')

def find_column(columns, patterns):
    """Find the first column that matches any of the given patterns (case-insensitive)"""
    for pattern in patterns:
        for col in columns:
            if pattern in col.lower():
                return col
    return None

@st.cache_data(ttl=300)
def load_data():
    db_path = get_database_path()

    if not os.path.exists(db_path):
        st.error(f"Database not found at: {db_path}")
        st.stop()

    conn = sqlite3.connect(db_path)

    # Get table names
    tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    def get_cols(table):
        cursor = conn.execute(f"PRAGMA table_info({table})")
        return [row[1] for row in cursor.fetchall()]

    prod_cols = get_cols('production') if 'production' in tables else []
    lines_cols = get_cols('lines') if 'lines' in tables else []
    dm_cols = get_cols('daily_metrics') if 'daily_metrics' in tables else []
    stop_cols = get_cols('downtime_events') if 'downtime_events' in tables else []

    st.session_state['debug_info'] = {
        'tables': tables,
        'production_cols': prod_cols,
        'lines_cols': lines_cols,
        'daily_metrics_cols': dm_cols,
        'downtime_cols': stop_cols
    }

    if not prod_cols:
        st.error("Production table not found in database.")
        return pd.DataFrame(), pd.DataFrame()

    df_prod = pd.read_sql_query(f"SELECT * FROM production", conn,
                                parse_dates=['date'] if 'date' in prod_cols else None)

 # Map Line Names

    if 'line_id' in prod_cols:
        df_prod['line_name'] = df_prod['line_id'].astype(str)
        if 'lines' in tables:
            name_col = find_column(lines_cols, ['name', 'nome', 'desc'])
            if name_col and 'line_id' in lines_cols:

                try:
                    df_lines = pd.read_sql_query(f"SELECT line_id, {name_col} FROM lines", conn)

                    df_lines[name_col] = df_lines[name_col].astype(str).str.replace('Linha', 'Line', case=False)
                    df_lines[name_col] = df_lines[name_col].str.replace('_', ' ')
                    line_map = dict(zip(df_lines['line_id'], df_lines[name_col]))
                    df_prod['line_name'] = df_prod['line_id'].map(line_map).fillna(df_prod['line_id'].astype(str))

                except:

                    pass

        df_prod['line_name'] = df_prod['line_name'].str.replace('Linha', 'Line', case=False).str.replace('_', ' ')

    # Map Shifts

    if 'shift' in prod_cols:
        df_prod['shift_name'] = df_prod['shift'].map({1: 'Morning', 2: 'Afternoon', 3: 'Evening'}).fillna('Other')

    else:
        df_prod['shift_name'] = 'General'

    # Load Daily Metrics
    if 'daily_metrics' in tables:

        try:
            has_shift_dm = 'shift' in dm_cols
            has_shift_prod = 'shift' in prod_cols

            select_cols = ['line_id', 'date', 'oee', 'availability', 'performance', 'quality']
            select_cols = [c for c in select_cols if c in dm_cols]

            if has_shift_dm and has_shift_prod:
                query = f"SELECT {', '.join(select_cols)} FROM daily_metrics"
                df_metrics = pd.read_sql_query(query, conn, parse_dates=['date'])
                merge_on = ['line_id', 'date', 'shift'] if 'shift' in select_cols else ['line_id', 'date']
                df_prod = df_prod.merge(df_metrics, on=merge_on, how='left', suffixes=('', '_dm'))

            else:
                agg_cols = [c for c in ['oee', 'availability', 'performance', 'quality'] if c in dm_cols]

                if agg_cols:
                    query = f"SELECT line_id, date, {', '.join([f'AVG({c}) as {c}' for c in agg_cols])} FROM daily_metrics GROUP BY line_id, date"
                    df_metrics = pd.read_sql_query(query, conn, parse_dates=['date'])
                    df_prod = df_prod.merge(df_metrics, on=['line_id', 'date'], how='left', suffixes=('', '_dm'))

        except Exception as e:
            st.session_state['debug_info']['metrics_error'] = str(e)

    if 'oee' not in df_prod.columns or df_prod['oee'].isna().all():
        actual_col = find_column(prod_cols, ['actual', 'real', 'efetivo'])
        planned_col = find_column(prod_cols, ['planned', 'planejado', 'previsto', 'plan'])

        if actual_col and planned_col:
            df_prod['availability'] = df_prod.apply(
                lambda x: x[actual_col] / x[planned_col] if pd.notna(x[planned_col]) and x[planned_col] > 0 else 0, axis=1
            )

        else:
            df_prod['availability'] = 0.0
        good_col = find_column(prod_cols, ['good', 'bom', 'aprovado', 'ok', 'defective'])
        total_col = find_column(prod_cols, ['total', 'geral', 'produzido', 'units'])

        if good_col and total_col:
    
            df_prod['quality'] = df_prod.apply(

                lambda x: x[good_col] / x[total_col] if pd.notna(x[total_col]) and x[total_col] > 0 else 0, axis=1
            )

        else:
            df_prod['quality'] = 0.0
        df_prod['performance'] = 0.0
        df_prod['oee'] = df_prod['availability'] * df_prod['quality']

    # Ensure all metric columns exist
    for col in ['oee', 'availability', 'performance', 'quality']:
        if col not in df_prod.columns:
            df_prod[col] = 0.0

    # Load Downtime Data
    df_stops = pd.DataFrame()
    if 'downtime_events' in tables:
        try:
            prod_id_col = find_column(stop_cols, ['production_id', 'prod_id'])
            if prod_id_col and 'production' in tables:
                prod_pk = 'production_id' if 'production_id' in prod_cols else 'id' if 'id' in prod_cols else None
                if prod_pk:
                    query = f"""
                        SELECT d.*, p.date, p.line_id, p.shift
                        FROM downtime_events d
                        JOIN production p ON d.{prod_id_col} = p.{prod_pk}
                    """
                    df_stops = pd.read_sql_query(query, conn, parse_dates=['date'])
                    reason_col = find_column(stop_cols, ['reason', 'cause', 'motivo', 'parada'])
                    df_stops['downtime_reason'] = df_stops[reason_col] if reason_col else 'Not specified'
                    df_stops['downtime_reason'] = df_stops['downtime_reason'].astype(str)
                    def translate_reason(text):
                        t = text.lower()
                        if 'manuten' in t: return 'Preventive Maintenance'
                        if 'falta' in t: return 'Lack of Raw Materials'
                        if 'troca' in t: return 'Flavor Changeover'
                        if 'qualidade' in t: return 'Quality Issues'
                        if 'insumo' in t or 'material' in t: return 'Lack of Materials'
                        if 'limpeza' in t or 'cip' in t: return 'CIP Cleaning'
                        if 'turno' in t: return 'Shift Change'
                        if 'quebra' in t or 'falha' in t: return 'Machine Breakdown'
                        if 'ajuste' in t: return 'Process Adjustment'
                        return text 

                    df_stops['downtime_reason'] = df_stops['downtime_reason'].apply(translate_reason)
                    duration_col = find_column(stop_cols, ['duration', 'minutes', 'minutos', 'time'])
                    df_stops['duration_minutes'] = df_stops[duration_col] if duration_col else 0
                    if 'line_id' in df_stops.columns:
                        df_stops['line_name'] = df_stops['line_id'].map(line_map).fillna(df_stops['line_id'].astype(str))
                        df_stops['line_name'] = df_stops['line_name'].str.replace('Linha', 'Line', case=False).str.replace('_', ' ')
        except Exception as e:
            st.session_state['debug_info']['stops_error'] = str(e)

    conn.close()

    return df_prod, df_stops

def main():
    st.markdown('<h1 class="main-header">🏭 OEE DASHBOARD - PRODUCTION ANALYSIS</h1>', unsafe_allow_html=True)
    try:
        df_prod, df_stops = load_data()
        st.success(f"Data Loaded: {len(df_prod)} records, {len(df_stops)} downtime events")
        with st.expander("🔍 Debug - Detected Structure"):
            if 'debug_info' in st.session_state:
                info = st.session_state['debug_info']
                st.write("**Tables:**", info.get('tables', []))
                st.write("**Production Columns:**", info.get('production_cols', []))
                if 'metrics_error' in info:
                    st.error(f"Metrics Error: {info['metrics_error']}")

    except Exception as e:
        st.error(f"Critical Error: {e}")

        return

    if df_prod.empty:
        st.error("No data available to display.")

        return

    # Sidebar Filters

    st.sidebar.markdown("## Filters")

    if 'date' in df_prod.columns:
        min_date = df_prod['date'].min().date()
        max_date = df_prod['date'].max().date()
        date_range = st.sidebar.date_input("Period", value=(min_date, max_date))

    else:
        date_range = (datetime.now().date(), datetime.now().date())

    lines = ['All'] + sorted(df_prod['line_name'].unique().tolist()) if 'line_name' in df_prod.columns else ['All']

    selected_line = st.sidebar.selectbox("Production Line", lines)

    shifts = ['All'] + sorted(df_prod['shift_name'].unique().tolist()) if 'shift_name' in df_prod.columns else ['All']

    selected_shift = st.sidebar.selectbox("Shift", shifts)

    # Apply Filters

    df_filtered = df_prod.copy()

    if 'date' in df_prod.columns and len(date_range) == 2:

        df_filtered = df_filtered[
            (df_filtered['date'] >= pd.to_datetime(date_range[0])) &
            (df_filtered['date'] <= pd.to_datetime(date_range[1]))
        ]

    if selected_line != 'All' and 'line_name' in df_filtered.columns:

        df_filtered = df_filtered[df_filtered['line_name'] == selected_line]

    if selected_shift != 'All' and 'shift_name' in df_filtered.columns:

        df_filtered = df_filtered[df_filtered['shift_name'] == selected_shift]

    if len(df_filtered) == 0:

        st.warning("No records found for the selected filters.")

        return

    # KPI Section
    st.markdown("### Main Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    metrics_avg = {

        'oee': df_filtered['oee'].mean() if 'oee' in df_filtered else 0,
        'availability': df_filtered['availability'].mean() if 'availability' in df_filtered else 0,
        'performance': df_filtered['performance'].mean() if 'performance' in df_filtered else 0,
        'quality': df_filtered['quality'].mean() if 'quality' in df_filtered else 0
    }

    # OEE Color Logic: Red < 60% | Orange < 85% | Green >= 85% (World Class)

    oee_color = "#ff4b4b" if metrics_avg['oee'] < 0.6 else "#ffa500" if metrics_avg['oee'] < 0.85 else "#00cc66"

    with col1:

        st.markdown(f'<div class="kpi-card" style="background: {oee_color}"><div>OEE</div><div class="kpi-value">{metrics_avg["oee"]:.1%}</div></div>', unsafe_allow_html=True)

    with col2:

        st.markdown(f'<div class="kpi-card" style="background: #1f77b4"><div>Availability</div><div class="kpi-value">{metrics_avg["availability"]:.1%}</div></div>', unsafe_allow_html=True)

    with col3:

        st.markdown(f'<div class="kpi-card" style="background: #ff7f0e"><div>Performance</div><div class="kpi-value">{metrics_avg["performance"]:.1%}</div></div>', unsafe_allow_html=True)

    with col4:

        st.markdown(f'<div class="kpi-card" style="background: #2ca02c"><div>Quality</div><div class="kpi-value">{metrics_avg["quality"]:.1%}</div></div>', unsafe_allow_html=True)

    # Analysis Tabs

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📅 Evolution", "🏭 Comparison", "⏱️ Downtime Analysis"])

    with tab1:

        if 'date' in df_filtered.columns:

            col_a, col_b = st.columns(2)

            with col_a:

                daily = df_filtered.groupby('date')['oee'].mean().reset_index()

                fig = go.Figure(go.Scatter(x=daily['date'], y=daily['oee'], mode='lines+markers', fill='tonexty', name='OEE'))

                fig.add_hline(y=0.85, line_dash="dash", line_color="green", annotation_text="World Class (85%)")

                fig.update_layout(height=400, yaxis_tickformat='.0%', title="OEE Trend Over Time")

                st.plotly_chart(fig, use_container_width=True)

            with col_b:

                if 'shift_name' in df_filtered.columns:

                    by_shift = df_filtered.groupby('shift_name')['oee'].mean().reset_index()

                    fig = go.Figure(go.Bar(x=by_shift['shift_name'], y=by_shift['oee'], marker_color='#764ba2'))

                    fig.update_layout(height=400, yaxis_tickformat='.0%', title="OEE by Production Shift")

                    st.plotly_chart(fig, use_container_width=True)

    with tab2:

        if 'line_name' in df_filtered.columns:

            line_m = df_filtered.groupby('line_name')[['availability', 'performance', 'quality', 'oee']].mean().reset_index()

            fig = go.Figure()

            colors_list = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

            for i, col in enumerate(['availability', 'performance', 'quality', 'oee']):

                fig.add_trace(go.Bar(name=col.capitalize(), x=line_m['line_name'], y=line_m[col], marker_color=colors_list[i]))

            fig.update_layout(barmode='group', height=500, yaxis_tickformat='.0%', title="Metric Comparison by Production Line")

            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        if not df_stops.empty:
            stops_f = df_stops.copy()

            if 'date' in stops_f.columns:
                stops_f = stops_f[(stops_f['date'] >= pd.to_datetime(date_range[0])) & (stops_f['date'] <= pd.to_datetime(date_range[1]))]
            
            if selected_line != 'All' and 'line_name' in stops_f.columns:
                stops_f = stops_f[stops_f['line_name'] == selected_line]

            if not stops_f.empty:
                pareto = stops_f.groupby('downtime_reason')['duration_minutes'].sum().reset_index()
                pareto = pareto.sort_values('duration_minutes', ascending=False).head(10)
                pareto['hours'] = pareto['duration_minutes'] / 60

                pareto['cum_percentage'] = (pareto['hours'].cumsum() / pareto['hours'].sum()) * 100

                fig = go.Figure()

                fig.add_trace(go.Bar(
                    x=pareto['downtime_reason'], 
                    y=pareto['hours'], 
                    name='Downtime (h)', 
                    marker_color='#e74c3c'
                ))

                fig.add_trace(go.Scatter(
                    x=pareto['downtime_reason'], 
                    y=pareto['cum_percentage'], 
                    name='Cumulative %', 
                    marker_color='#2c3e50',
                    yaxis='y2' 
                ))

                # Update Layout to support dual axes
                fig.update_layout(
                    height=500, 
                    title="Top 10 Downtime Causes (Pareto Analysis)",
                    xaxis_tickangle=-45,
                    yaxis=dict(
                        title="Downtime (Hours)",
                        side="left"
                    ),
                    yaxis2=dict(
                        title="Cumulative Percentage (%)",
                        overlaying='y',
                        side='right',
                        range=[0, 105], 
                        showgrid=False  
                    ),
                    legend=dict(x=1.1, y=1) 
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No downtime events recorded for the selected filters.")
        else:
            st.info("Downtime event table is empty or not found.")

if __name__ == "__main__":

    main()