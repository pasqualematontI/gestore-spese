from datetime import date
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from models import Spesa
from utils import (
    CATEGORIE,
    annulla_ultima_modifica,
    elimina_spesa,
    get_spesa_by_index,      # ← Aggiunto
    modifica_spesa,           # ← Aggiunto
    numero_spese,
    puo_annullare,
    puo_ripetere,
    ripeti_ultima_modifica,
    salva_spesa,
    spese_in_dataframe,
    spese_per_categoria,
    spese_per_mese_categoria,
    totale_spese,
)

ICONE_CATEGORIA = {
    "Alimentari": "🛒",
    "Trasporti": "🚌",
    "Svago": "🎬",
    "Casa": "🏠",
    "Salute": "💊",
    "Altro": "📦",
}

COLORI_GRAFICI = ["#3b82f6", "#10b981", "#f59e0b", "#ec4899", "#06b6d4", "#8b5cf6"]

MESI_IT = {
    "01": "Gen", "02": "Feb", "03": "Mar", "04": "Apr",
    "05": "Mag", "06": "Giu", "07": "Lug", "08": "Ago",
    "09": "Set", "10": "Ott", "11": "Nov", "12": "Dic",
}

STILE_CSS = """
<style>
    [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
    [data-testid="stHeader"], [data-testid="stToolbar"],
    .stDeployButton, .stAppDeployButton, footer, #MainMenu {
        display: none !important;
    }
    .stApp { background-color: #0c1017; }
    .stApp::before, .stApp::after {
        content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
    }
    .stApp::before {
        background: radial-gradient(circle at 15% 20%, rgba(59, 130, 246, 0.18) 0%, transparent 42%),
                    radial-gradient(circle at 85% 75%, rgba(16, 185, 129, 0.14) 0%, transparent 40%),
                    radial-gradient(circle at 50% 50%, rgba(139, 92, 246, 0.08) 0%, transparent 55%);
        animation: sfuma-bg 14s ease-in-out infinite alternate;
    }
    .stApp::after {
        background: radial-gradient(circle at 70% 15%, rgba(6, 182, 212, 0.1) 0%, transparent 35%);
        animation: sfuma-bg 18s ease-in-out infinite alternate-reverse;
    }
    @keyframes sfuma-bg {
        from { opacity: 0.75; transform: scale(1) translate(0, 0); }
        to   { opacity: 1; transform: scale(1.03) translate(1%, -1%); }
    }
    .block-container { position: relative; z-index: 1; padding-top: 1.5rem; max-width: 960px; }
    .brand-title { font-size: 1.35rem; font-weight: 700; background: linear-gradient(90deg, #f9fafb, #93c5fd); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; }
    .brand-sub { font-size: 0.8rem; color: #9ca3af; margin: 0.15rem 0 0 0; }
    .page-title { font-size: 1.5rem; font-weight: 600; color: #f9fafb; margin: 0 0 0.25rem 0; }
    .page-desc { color: #9ca3af; font-size: 0.9rem; margin-bottom: 1.25rem; }
    .stButton > button { border-radius: 10px !important; transition: all 0.15s ease; }
    .stButton > button:hover:not(:disabled) { transform: translateY(-2px); filter: brightness(1.1); }
</style>
"""

def applica_stile() -> None:
    st.markdown(STILE_CSS, unsafe_allow_html=True)

def categoria_con_icona(nome: str) -> str:
    return f"{ICONE_CATEGORIA.get(nome, '📌')} {nome}"

def categoria_da_label(label: str) -> str:
    for cat in CATEGORIE:
        if cat in label:
            return cat
    return label

def mappa_colori_categorie() -> dict[str, str]:
    return {
        categoria_con_icona(cat): COLORI_GRAFICI[i % len(COLORI_GRAFICI)]
        for i, cat in enumerate(CATEGORIE)
    }

def formatta_mese(mese: str) -> str:
    try:
        anno, m = mese.split("-")
        return f"{MESI_IT.get(m, m)} {anno}"
    except ValueError:
        return mese

def applica_layout_grafico(fig: go.Figure, altezza: int = 420) -> go.Figure:
    fig.update_layout(
        height=altezza,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Segoe UI, sans-serif", color="#e5e7eb", size=13),
        margin=dict(t=24, b=72, l=48, r=24),
        legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5,
                    bgcolor="rgba(15, 23, 42, 0.6)", bordercolor="#374151", borderwidth=1),
        hoverlabel=dict(bgcolor="#111827", bordercolor="#4b5563"),
    )
    return fig

def crea_grafico_categorie(df_cat, colori: dict[str, str]) -> go.Figure:
    df = df_cat.copy()
    df["etichetta"] = df["categoria"].apply(categoria_con_icona)
    totale = df["importo"].sum()

    fig = px.pie(df, names="etichetta", values="importo", color="etichetta",
                 color_discrete_map=colori, hole=0.52)

    fig.update_traces(textposition="outside", textinfo="percent", pull=[0.03]*len(df),
                      hovertemplate="<b>%{label}</b><br>Importo: € %{value:,.2f}<extra></extra>")
    
    fig.add_annotation(text=f"<b>€ {totale:,.2f}</b><br><span style='font-size:11px'>Totale</span>",
                       x=0.5, y=0.5, showarrow=False, font=dict(size=18))
    return applica_layout_grafico(fig, 400)

def crea_grafico_mesi(df_mese_cat, colori: dict[str, str]) -> go.Figure:
    df = df_mese_cat.copy()
    df["etichetta"] = df["categoria"].apply(categoria_con_icona)
    df["mese_label"] = df["mese"].apply(formatta_mese)
    ordine_mesi = sorted(df["mese"].unique())
    ordine_label = [formatta_mese(m) for m in ordine_mesi]

    fig = px.bar(df, x="mese_label", y="importo", color="etichetta",
                 color_discrete_map=colori, barmode="stack",
                 category_orders={"mese_label": ordine_label})

    fig.update_traces(marker_line_width=0, marker_cornerradius=5)
    return applica_layout_grafico(fig, 400)

def titolo_grafico(titolo: str, sottotitolo: str) -> None:
    st.markdown(f'<p class="chart-card-title">{titolo}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="chart-card-sub">{sottotitolo}</p>', unsafe_allow_html=True)

def barra_navigazione() -> None:
    if "pagina" not in st.session_state:
        st.session_state.pagina = "aggiungi"

    with st.container(border=True):
        col_logo, col_undo, col_redo, col_a, col_b, col_c = st.columns([1.85, 0.7, 0.7, 1, 1, 1])
        
        with col_logo:
            st.markdown("""<p class="brand-title">Gestore Spese Personali</p>
                           <p class="brand-sub">Controllo spese · Progetto Python</p>""", unsafe_allow_html=True)

        with col_undo:
            if st.button("← Indietro", key="nav_annulla", use_container_width=True,
                         disabled=not puo_annullare(), help="Annulla ultima modifica"):
                if annulla_ultima_modifica():
                    st.toast("Modifica annullata", icon="↩️")
                    st.rerun()

        with col_redo:
            if st.button("Avanti →", key="nav_ripeti", use_container_width=True,
                         disabled=not puo_ripetere(), help="Ripristina modifica"):
                if ripeti_ultima_modifica():
                    st.toast("Modifica ripristinata", icon="↪️")
                    st.rerun()

        for col, chiave, etichetta in [(col_a, "aggiungi", "Aggiungi"), 
                                      (col_b, "visualizza", "Elenco"), 
                                      (col_c, "dashboard", "Dashboard")]:
            with col:
                attiva = st.session_state.pagina == chiave
                if st.button(etichetta, key=f"nav_{chiave}", use_container_width=True,
                             type="primary" if attiva else "secondary"):
                    st.session_state.pagina = chiave
                    st.rerun()

def intestazione_pagina(titolo: str, descrizione: str) -> None:
    st.markdown(f'<p class="page-title">{titolo}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="page-desc">{descrizione}</p>', unsafe_allow_html=True)

# ====================== PAGINE ======================

def pagina_aggiungi() -> None:
    intestazione_pagina("Aggiungi Spesa", "Inserisci una nuova uscita di denaro.")
    with st.form("form_spesa"):
        c1, c2, c3 = st.columns(3)
        with c1: data_spesa = st.date_input("Data", value=date.today())
        with c2: importo = st.number_input("Importo (€)", min_value=0.01, step=0.01, format="%.2f")
        with c3: 
            opzioni = [categoria_con_icona(c) for c in CATEGORIE]
            categoria_ui = st.selectbox("Categoria", opzioni)
        
        descrizione = st.text_input("Descrizione", placeholder="Es. Spesa al supermercato")
        
        if st.form_submit_button("💾 Salva spesa", type="primary", use_container_width=True):
            categoria = categoria_da_label(categoria_ui)
            salva_spesa(Spesa.nuova(importo=importo, categoria=categoria,
                                   descrizione=descrizione, data=data_spesa.strftime("%Y-%m-%d")))
            st.success(f"✅ Spesa di € {importo:.2f} salvata!")
            st.rerun()

def pagina_modifica() -> None:
    intestazione_pagina("Modifica Spesa", "Cambia i dati di una spesa esistente.")
    df = spese_in_dataframe()
    if df.empty:
        st.warning("Nessuna spesa da modificare.")
        return

    etichette = [f"{r['data']} · {r['categoria']} · € {r['importo']:.2f} · {r['descrizione'][:60]}..."
                 for _, r in df.iterrows()]
    
    indice = st.selectbox("Seleziona spesa da modificare", range(len(etichette)),
                         format_func=lambda i: etichette[i])

    spesa = get_spesa_by_index(indice)
    if spesa:
        with st.form("form_modifica"):
            c1, c2, c3 = st.columns(3)
            with c1: data_spesa = st.date_input("Data", value=date.fromisoformat(spesa.data))
            with c2: importo = st.number_input("Importo (€)", value=float(spesa.importo),
                                              min_value=0.01, step=0.01, format="%.2f")
            with c3:
                opzioni = [categoria_con_icona(c) for c in CATEGORIE]
                idx = opzioni.index(categoria_con_icona(spesa.categoria)) if categoria_con_icona(spesa.categoria) in opzioni else 0
                categoria_ui = st.selectbox("Categoria", opzioni, index=idx)

            descrizione = st.text_input("Descrizione", value=spesa.descrizione)

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Salva Modifiche", type="primary", use_container_width=True):
                    nuova_spesa = Spesa(
                        data=data_spesa.strftime("%Y-%m-%d"),
                        importo=importo,
                        categoria=categoria_da_label(categoria_ui),
                        descrizione=descrizione
                    )
                    if modifica_spesa(indice, nuova_spesa):
                        st.success("✅ Spesa modificata con successo!")
                        st.rerun()
            with col2:
                if st.form_submit_button("❌ Annulla", use_container_width=True):
                    st.rerun()

def pagina_visualizza() -> None:
    intestazione_pagina("Visualizza Spese", "Elenco completo con filtri avanzati.")
    df = spese_in_dataframe()
    if df.empty:
        st.info("Nessuna spesa presente. Vai su **Aggiungi**.")
        return

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        filtro_cat = st.selectbox("Categoria", ["Tutte"] + CATEGORIE)
    with col2:
        d1, d2 = st.columns(2)
        with d1: data_inizio = st.date_input("Da", value=date.today().replace(day=1))
        with d2: data_fine = st.date_input("A", value=date.today())
    with col3:
        st.download_button("📥 Scarica CSV", df.to_csv(index=False).encode("utf-8"),
                          "spese.csv", "text/csv", use_container_width=True)

    df_f = df.copy()
    if filtro_cat != "Tutte":
        df_f = df_f[df_f["categoria"] == filtro_cat]
    df_f = df_f[
        (pd.to_datetime(df_f["data"]) >= pd.to_datetime(data_inizio)) &
        (pd.to_datetime(df_f["data"]) <= pd.to_datetime(data_fine))
    ].reset_index(drop=True)

    if df_f.empty:
        st.warning("Nessuna spesa trovata con questi filtri.")
        return

    df_show = df_f.copy()
    df_show["categoria"] = df_show["categoria"].apply(categoria_con_icona)
    st.dataframe(df_show, use_container_width=True, hide_index=True,
                 column_config={"importo": st.column_config.NumberColumn(format="€ %.2f")})

    st.divider()
    tab1, tab2 = st.tabs(["🗑️ Elimina", "✏️ Modifica"])

    with tab1:
        etichette = [f"{r['data']} · {r['categoria']} · € {r['importo']:.2f} · {r['descrizione']}"
                     for _, r in df.iterrows()]
        idx = st.selectbox("Seleziona spesa da eliminare", range(len(etichette)),
                          format_func=lambda i: etichette[i])
        if st.button("🗑️ Elimina spesa selezionata", type="secondary"):
            if st.checkbox("Confermi l'eliminazione?", key="conf_elim"):
                if elimina_spesa(idx):
                    st.success("Spesa eliminata.")
                    st.rerun()

    with tab2:
        if st.button("✏️ Vai alla pagina di Modifica", type="primary", use_container_width=True):
            st.session_state.pagina = "modifica"
            st.rerun()

def pagina_dashboard() -> None:
    intestazione_pagina("Dashboard", "Riepilogo e analisi delle tue spese.")
    c1, c2 = st.columns(2)
    with c1: st.metric("Spesa totale", f"€ {totale_spese():.2f}")
    with c2: st.metric("Numero spese", numero_spese())

    st.divider()
    df_cat = spese_per_categoria()
    df_mese = spese_per_mese_categoria()
    colori = mappa_colori_categorie()

    g1, g2 = st.columns(2)
    with g1:
        titolo_grafico("Distribuzione per categoria", "Come si dividono le spese")
        if not df_cat.empty:
            st.plotly_chart(crea_grafico_categorie(df_cat, colori), use_container_width=True, config={"displayModeBar": False})
    with g2:
        titolo_grafico("Andamento mensile", "Spese per mese e categoria")
        if not df_mese.empty:
            st.plotly_chart(crea_grafico_mesi(df_mese, colori), use_container_width=True, config={"displayModeBar": False})

# ====================== AVVIO ======================
st.set_page_config(page_title="Gestore Spese Personali", page_icon="💰", layout="wide")
applica_stile()
barra_navigazione()

if st.session_state.pagina == "aggiungi":
    pagina_aggiungi()
elif st.session_state.pagina == "visualizza":
    pagina_visualizza()
elif st.session_state.pagina == "modifica":
    pagina_modifica()
else:
    pagina_dashboard()