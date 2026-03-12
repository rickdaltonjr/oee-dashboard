import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import os
from datetime import datetime

st.set_page_config(page_title="Dashboard OEE", page_icon="🏭", layout="wide")

st.markdown("""
<style>
.main-header { font-size: 2.5rem; font-weight: bold; color: #1f77b4; text-align: center; }
.kpi-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; 
            color: white; text-align: center; }
.kpi-value { font-size: 2.5rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def get_database_path():
    if os.path.exists('../database/oee_database.db'):
        return '../database/oee_database.db'
    elif os.path.exists('database/oee_database.db'):
        return 'database/oee_database.db'
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, 'database', 'oee_database.db')

def find_column(columns, patterns):
    """Encontra coluna que contenha algum dos padrões"""
    for pattern in patterns:
        for col in columns:
            if pattern in col.lower():
                return col
    return None

@st.cache_data(ttl=300)
def load_data():
    db_path = get_database_path()
    
    if not os.path.exists(db_path):
        st.error(f"❌ Banco não encontrado: {db_path}")
        st.stop()
    
    conn = sqlite3.connect(db_path)
    
    # Verificar tabelas
    tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    
    # Obter colunas de cada tabela
    def get_cols(table):
        cursor = conn.execute(f"PRAGMA table_info({table})")
        return [row[1] for row in cursor.fetchall()]
    
    prod_cols = get_cols('production') if 'production' in tables else []
    lines_cols = get_cols('lines') if 'lines' in tables else []
    dm_cols = get_cols('daily_metrics') if 'daily_metrics' in tables else []
    stop_cols = get_cols('downtime_events') if 'downtime_events' in tables else []
    
    # Guardar para debug
    st.session_state['debug_info'] = {
        'tables': tables,
        'production_cols': prod_cols,
        'lines_cols': lines_cols,
        'daily_metrics_cols': dm_cols,
        'downtime_cols': stop_cols
    }
    
    # ========== CARREGAR PRODUCTION ==========
    if not prod_cols:
        st.error("❌ Tabela production não encontrada")
        return pd.DataFrame(), pd.DataFrame()
    
    # Carregar production
    df_prod = pd.read_sql_query(f"SELECT * FROM production", conn, 
                                parse_dates=['date'] if 'date' in prod_cols else None)
    
    # Adicionar line_name
    if 'line_id' in prod_cols:
        df_prod['line_name'] = df_prod['line_id'].astype(str)
        # Tentar buscar nome real
        if 'lines' in tables:
            name_col = find_column(lines_cols, ['name', 'nome', 'desc'])
            if name_col and 'line_id' in lines_cols:
                try:
                    df_lines = pd.read_sql_query(f"SELECT line_id, {name_col} FROM lines", conn)
                    line_map = dict(zip(df_lines['line_id'], df_lines[name_col].astype(str)))
                    df_prod['line_name'] = df_prod['line_id'].map(line_map).fillna(df_prod['line_id'].astype(str))
                except:
                    pass
    
    # Adicionar shift_name
    if 'shift' in prod_cols:
        df_prod['shift_name'] = df_prod['shift'].map({1: 'Manhã', 2: 'Tarde', 3: 'Noite'}).fillna('Outro')
    else:
        df_prod['shift_name'] = 'Geral'
    
    # ========== BUSCAR MÉTRICAS OEE ==========
    if 'daily_metrics' in tables:
        try:
            # Verificar se daily_metrics tem shift
            has_shift_dm = 'shift' in dm_cols
            has_shift_prod = 'shift' in prod_cols
            
            # Montar query conforme colunas disponíveis
            select_cols = ['line_id', 'date', 'oee', 'availability', 'performance', 'quality']
            select_cols = [c for c in select_cols if c in dm_cols]
            
            if has_shift_dm and has_shift_prod:
                # Merge com shift
                query = f"SELECT {', '.join(select_cols)} FROM daily_metrics"
                df_metrics = pd.read_sql_query(query, conn, parse_dates=['date'])
                merge_on = ['line_id', 'date', 'shift'] if 'shift' in select_cols else ['line_id', 'date']
                df_prod = df_prod.merge(df_metrics, on=merge_on, how='left', suffixes=('', '_dm'))
            else:
                # Merge sem shift (agrupar por line_id, date)
                agg_cols = [c for c in ['oee', 'availability', 'performance', 'quality'] if c in dm_cols]
                if agg_cols:
                    query = f"SELECT line_id, date, {', '.join([f'AVG({c}) as {c}' for c in agg_cols])} FROM daily_metrics GROUP BY line_id, date"
                    df_metrics = pd.read_sql_query(query, conn, parse_dates=['date'])
                    df_prod = df_prod.merge(df_metrics, on=['line_id', 'date'], how='left', suffixes=('', '_dm'))
        except Exception as e:
            st.session_state['debug_info']['metrics_error'] = str(e)
    
    # ========== CALCULAR MÉTRICAS SE NECESSÁRIO ==========
    # Verificar se temos as métricas, se não, calcular
    if 'oee' not in df_prod.columns or df_prod['oee'].isna().all():
        # Disponibilidade = actual / planned
        actual_col = find_column(prod_cols, ['actual', 'real', 'efetivo'])
        planned_col = find_column(prod_cols, ['planned', 'planejado', 'previsto', 'plan'])
        
        if actual_col and planned_col:
            df_prod['availability'] = df_prod.apply(
                lambda x: x[actual_col] / x[planned_col] if pd.notna(x[planned_col]) and x[planned_col] > 0 else 0, axis=1
            )
        else:
            df_prod['availability'] = 0.0
        
        # Qualidade = good / total
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
    
    # Garantir colunas existem
    for col in ['oee', 'availability', 'performance', 'quality']:
        if col not in df_prod.columns:
            df_prod[col] = 0.0
    
    # ========== CARREGAR DOWNTIME ==========
    df_stops = pd.DataFrame()
    if 'downtime_events' in tables:
        try:
            # Encontrar coluna de join
            prod_id_col = find_column(stop_cols, ['production_id', 'prod_id'])
            
            if prod_id_col and 'production' in tables:
                # Verificar se production tem production_id ou id
                prod_pk = 'production_id' if 'production_id' in prod_cols else 'id' if 'id' in prod_cols else None
                
                if prod_pk:
                    query = f"""
                        SELECT d.*, p.date, p.line_id, p.shift 
                        FROM downtime_events d 
                        JOIN production p ON d.{prod_id_col} = p.{prod_pk}
                    """
                    df_stops = pd.read_sql_query(query, conn, parse_dates=['date'])
                    
                    # Normalizar colunas
                    reason_col = find_column(stop_cols, ['reason', 'cause', 'motivo', 'parada'])
                    if reason_col:
                        df_stops = df_stops.rename(columns={reason_col: 'downtime_reason'})
                    else:
                        df_stops['downtime_reason'] = 'Não especificado'
                    
                    duration_col = find_column(stop_cols, ['duration', 'minutes', 'minutos', 'time'])
                    if duration_col:
                        df_stops = df_stops.rename(columns={duration_col: 'duration_minutes'})
                    else:
                        df_stops['duration_minutes'] = 0
                    
                    # Adicionar line_name
                    if 'line_id' in df_stops.columns:
                        df_stops['line_name'] = df_stops['line_id'].astype(str)
        except Exception as e:
            st.session_state['debug_info']['stops_error'] = str(e)
    
    conn.close()
    return df_prod, df_stops

def main():
    st.markdown('<h1 class="main-header">🏭 DASHBOARD OEE - PRODUÇÃO</h1>', unsafe_allow_html=True)
    
    try:
        df_prod, df_stops = load_data()
        st.success(f"✅ Dados carregados: {len(df_prod)} registros, {len(df_stops)} paradas")
        
        # Debug info
        with st.expander("🔍 Debug - Estrutura Detectada"):
            if 'debug_info' in st.session_state:
                info = st.session_state['debug_info']
                st.write("**Tabelas:**", info.get('tables', []))
                st.write("**Production:**", info.get('production_cols', []))
                st.write("**Daily Metrics:**", info.get('daily_metrics_cols', []))
                st.write("**Downtime:**", info.get('downtime_cols', []))
                if 'metrics_error' in info:
                    st.error(f"Erro métricas: {info['metrics_error']}")
                if 'stops_error' in info:
                    st.error(f"Erro paradas: {info['stops_error']}")
        
    except Exception as e:
        st.error(f"❌ Erro: {e}")
        import traceback
        st.code(traceback.format_exc())
        return
    
    if df_prod.empty:
        st.error("❌ Sem dados")
        return
    
    # Filtros
    st.sidebar.markdown("## 🔧 Filtros")
    
    if 'date' in df_prod.columns:
        min_date = df_prod['date'].min().date()
        max_date = df_prod['date'].max().date()
        date_range = st.sidebar.date_input("Período", value=(min_date, max_date))
    else:
        date_range = (datetime.now().date(), datetime.now().date())
    
    lines = ['Todas'] + sorted(df_prod['line_name'].unique().tolist()) if 'line_name' in df_prod.columns else ['Todas']
    selected_line = st.sidebar.selectbox("Linha", lines)
    
    shifts = ['Todos'] + sorted(df_prod['shift_name'].unique().tolist()) if 'shift_name' in df_prod.columns else ['Todos']
    selected_shift = st.sidebar.selectbox("Turno", shifts)
    
    # Aplicar filtros
    df_filtered = df_prod.copy()
    if 'date' in df_prod.columns:
        df_filtered = df_filtered[
            (df_filtered['date'] >= pd.to_datetime(date_range[0])) &
            (df_filtered['date'] <= pd.to_datetime(date_range[1]))
        ]
    if selected_line != 'Todas' and 'line_name' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['line_name'] == selected_line]
    if selected_shift != 'Todos' and 'shift_name' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['shift_name'] == selected_shift]
    
    if len(df_filtered) == 0:
        st.warning("⚠️ Nenhum dado para os filtros")
        return
    
    # KPIs
    st.markdown("### 📊 Indicadores Principais")
    col1, col2, col3, col4 = st.columns(4)
    
    metrics = {
        'oee': df_filtered['oee'].mean() if 'oee' in df_filtered else 0,
        'availability': df_filtered['availability'].mean() if 'availability' in df_filtered else 0,
        'performance': df_filtered['performance'].mean() if 'performance' in df_filtered else 0,
        'quality': df_filtered['quality'].mean() if 'quality' in df_filtered else 0
    }
    
    colors = {'oee': "#ff4b4b" if metrics['oee'] < 0.6 else "#ffa500" if metrics['oee'] < 0.85 else "#00cc66",
              'availability': "#1f77b4", 'performance': "#ff7f0e", 'quality': "#2ca02c"}
    
    with col1:
        st.markdown(f'<div class="kpi-card" style="background: {colors["oee"]}"><div>OEE</div><div class="kpi-value">{metrics["oee"]:.1%}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="kpi-card" style="background: {colors["availability"]}"><div>Disponibilidade</div><div class="kpi-value">{metrics["availability"]:.1%}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="kpi-card" style="background: {colors["performance"]}"><div>Performance</div><div class="kpi-value">{metrics["performance"]:.1%}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="kpi-card" style="background: {colors["quality"]}"><div>Qualidade</div><div class="kpi-value">{metrics["quality"]:.1%}</div></div>', unsafe_allow_html=True)
    
    # Abas
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📅 Evolução", "🏭 Comparativo", "⏱️ Paradas"])
    
    with tab1:
        if 'date' in df_filtered.columns and 'oee' in df_filtered.columns:
            col1, col2 = st.columns(2)
            with col1:
                daily = df_filtered.groupby('date')['oee'].mean().reset_index()
                fig = go.Figure(go.Scatter(x=daily['date'], y=daily['oee'], mode='lines+markers', fill='tonexty'))
                fig.add_hline(y=0.85, line_dash="dash", line_color="green")
                fig.update_layout(height=400, yaxis_tickformat='.0%', title="OEE ao longo do tempo")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                if 'shift_name' in df_filtered.columns:
                    by_shift = df_filtered.groupby('shift_name')['oee'].mean().reset_index()
                    colors_bar = ['#ff4b4b' if x < 0.6 else '#ffa500' if x < 0.85 else '#00cc66' for x in by_shift['oee']]
                    fig = go.Figure(go.Bar(x=by_shift['shift_name'], y=by_shift['oee'], marker_color=colors_bar))
                    fig.update_layout(height=400, yaxis_tickformat='.0%', title="OEE por Turno")
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        if 'line_name' in df_filtered.columns:
            line_m = df_filtered.groupby('line_name')[list(metrics.keys())].mean().reset_index()
            fig = go.Figure()
            for i, col in enumerate(['availability', 'performance', 'quality', 'oee']):
                if col in line_m.columns:
                    fig.add_trace(go.Bar(name=col.title(), x=line_m['line_name'], y=line_m[col],
                                       marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'][i]))
            fig.update_layout(barmode='group', height=500, yaxis_tickformat='.0%', title="Comparativo por Linha")
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        if not df_stops.empty and 'downtime_reason' in df_stops.columns:
            stops_f = df_stops.copy()
            if 'date' in stops_f.columns:
                stops_f = stops_f[(stops_f['date'] >= pd.to_datetime(date_range[0])) & (stops_f['date'] <= pd.to_datetime(date_range[1]))]
            if selected_line != 'Todas' and 'line_name' in stops_f.columns:
                stops_f = stops_f[stops_f['line_name'] == selected_line]
            
            if not stops_f.empty and 'duration_minutes' in stops_f.columns:
                pareto = stops_f.groupby('downtime_reason')['duration_minutes'].agg(['sum', 'count']).reset_index()
                pareto.columns = ['motivo', 'minutos', 'ocorrencias']
                pareto = pareto.sort_values('minutos', ascending=False).head(10)
                pareto['horas'] = pareto['minutos'] / 60
                pareto['acumulado'] = pareto['horas'].cumsum() / pareto['horas'].sum() * 100
                
                fig = go.Figure()
                fig.add_trace(go.Bar(x=pareto['motivo'], y=pareto['horas'], name='Tempo (h)', marker_color='#e74c3c'))
                fig.add_trace(go.Scatter(x=pareto['motivo'], y=pareto['acumulado'], name='Acumulado %', 
                                       yaxis='y2', line=dict(color='#2c3e50', width=3)))
                fig.update_layout(height=500, xaxis_tickangle=-45, 
                                yaxis2=dict(title="% Acumulado", overlaying='y', side='right', range=[0, 100]))
                fig.add_hline(y=80, line_dash="dash", line_color="orange", yref='y2')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem paradas para o período")
        else:
            st.info("Sem dados de paradas")

if __name__ == "__main__":
    main()