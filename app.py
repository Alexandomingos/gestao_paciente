import io
import re
from datetime import date, datetime

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Gestão de Pacientes",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Visual ----------
st.markdown("""
<style>
    .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
    [data-testid="stMetric"] {
        background: white; border: 1px solid #e3eaf4; padding: 14px;
        border-radius: 12px; box-shadow: 0 1px 4px rgba(20,50,90,.04);
    }
    div[data-testid="stDataFrame"] {border: 1px solid #e3eaf4; border-radius: 10px;}
    .subtitle {color:#64748b; margin-top:-10px;}
    .notice {padding: .8rem 1rem; border-radius: 10px; background:#eff6ff; border-left:4px solid #2563eb;}
</style>
""", unsafe_allow_html=True)

st.title("🩺 Gestão de Pacientes")
st.caption("Consolidação de prontuários, indicadores e identificação inicial de inconsistências")
st.markdown('<div class="notice">MVP demonstrativo: os dados de exemplo são fictícios. Não carregue dados reais de saúde em uma publicação pública na nuvem.</div>', unsafe_allow_html=True)

# ---------- Demo data ----------
def demo_data():
    rows = [
        ["Ana Paula Martins", "898000000000001", "10021", "1964-05-12", 62, 1.62, 78, 29.7, "Não", "Sim", "Sim", "HAS/DIA", "Médio", "Realizado", "7.8", "Pendente", "Realizado", "Sim", "2026-08-10", "Ativo", "Autocontrole glicêmico"],
        ["João Carlos Pereira", "898000000000002", "10022", "1968-11-02", 57, 1.75, 85, 27.8, "Sim", "Sim", "Não", "HAS", "Baixo", "Pendente", "", "Pendente", "Não realizado", "Não", "2026-05-01", "Ativo", "Hipertensão"],
        ["Maria de Lourdes Souza", "898000000000003", "10023", "1949-02-18", 77, 1.55, 68, 28.3, "Não", "Não", "Sim", "DIA", "Alto", "Realizado", "9.2", "Alterado", "Pendente", "Sim", "2026-07-12", "Ativo", "Autocontrole glicêmico"],
        ["Carlos Eduardo Lima", "898000000000004", "10024", "1957-09-29", 69, 1.70, 91, 31.5, "Não", "Sim", "Sim", "HAS/DIA", "Alto", "Alterado", "8.9", "Pendente", "Pendente", "Sim", "2026-09-01", "Óbito", "Autocontrole glicêmico"],
        ["Fernanda Oliveira", "898000000000005", "10025", "1981-01-06", 45, 1.60, 64, 25.0, "Não", "Não", "Não", "", "Baixo", "Realizado", "5.4", "Não se aplica", "Não se aplica", "Não", "2026-03-15", "Ativo", "Nenhum"],
        ["Roberto Almeida", "898000000000006", "10026", "1962-04-20", 64, 1.73, 88, 29.4, "Sim", "Sim", "Não", "HAS", "Médio", "Pendente", "", "Não se aplica", "Não se aplica", "Não", "2026-01-20", "Ativo", "Hipertensão"],
        ["Sônia Cristina Alves", "898000000000007", "10027", "1953-12-09", 72, 1.58, 70, 28.0, "Não", "Não", "Sim", "DIA", "Alto", "Alterado", "8.5", "Pendente", "Alterado", "Sim", "2026-09-18", "Ativo", "Autocontrole glicêmico"],
        ["Pedro Henrique Costa", "898000000000008", "10028", "1990-07-23", 36, 1.80, 82, 25.3, "Não", "Não", "Não", "", "Baixo", "Realizado", "5.2", "Não se aplica", "Não se aplica", "Não", "2026-09-30", "Ativo", "Nenhum"],
        ["Luciana Ferreira", "898000000000009", "10029", "1959-03-14", 67, 1.64, 74, 27.5, "Não", "Sim", "Sim", "HAS/DIA", "Médio", "Pendente", "", "Pendente", "Pendente", "Sim", "2026-04-01", "Ativo", "Autocontrole glicêmico"],
    ]
    cols = ["Pacientes", "Cartão SUS", "Prontuário", "Data de nascimento", "Idade", "Altura (m)", "Peso (kg)", "IMC", "Tabagista", "HAS", "Diabetes", "HAS/DIA", "Risco", "Exame Laboratorial", "HB glicada", "Fundoscopia", "Pé Diabético", "Pcte encaminhado", "Data da última consulta", "Status", "Programa"]
    return pd.DataFrame(rows, columns=cols)

# ---------- Helpers ----------
def norm_col(s):
    s = str(s).strip().lower()
    s = (s.replace("á","a").replace("à","a").replace("ã","a").replace("â","a")
           .replace("é","e").replace("ê","e").replace("í","i").replace("ó","o")
           .replace("ô","o").replace("õ","o").replace("ú","u").replace("ç","c"))
    return re.sub(r"[^a-z0-9]+", "", s)

ALIASES = {
    "name": ["pacientes", "paciente", "nome", "nomecompleto", "nomedopaciente"],
    "cns": ["cartaosus", "cns", "cartao nacional de saude"],
    "cpf": ["cpf"],
    "record": ["prontuario", "numeroprontuario"],
    "dob": ["datadenascimento", "nascimento"],
    "age": ["idade"],
    "height": ["alturam", "altura"],
    "weight": ["pesokg", "peso"],
    "bmi": ["imc"],
    "smoker": ["tabagista"],
    "has": ["has", "hipertensao", "hipertenso"],
    "diabetes": ["diabetes", "diabetico", "diabetica"],
    "risk": ["risco"],
    "lab": ["exam elaboratorial", "examelaboratorial"],
    "hba1c": ["hbglicada", "hemoglobinaglicada"],
    "fundoscopy": ["fundoscopia"],
    "diabetic_foot": ["pediabetico", "avaliacaopediabetico"],
    "referral": ["pct encaminhado", "pct encaminhado", "pctencaminhado", "pacienteencaminhado"],
    "last_visit": ["datadaultimaconsulta", "ultimaconsulta", "dataconsulta", "ultimamovimentacao"],
    "status": ["status", "situacao", "situacaocadastral"],
    "program": ["programa", "programas", "programadesaude"],
    "neighborhood": ["bairro"],
    "city": ["cidade", "municipio"],
    "medication": ["medicamentos", "medicamento", "remedios"],
    "return_date": ["dataderetorno", "retorno", "proximoretorno"],
}

def find_col(df, candidates):
    normalized = {norm_col(c): c for c in df.columns}
    for cand in candidates:
        nc = norm_col(cand)
        if nc in normalized:
            return normalized[nc]
    # partial match to tolerate longer headings
    for nc, original in normalized.items():
        for cand in candidates:
            cc = norm_col(cand)
            if cc and (cc in nc or nc in cc):
                return original
    return None

def truthy(v):
    if pd.isna(v): return False
    s = str(v).strip().lower()
    return s in {"sim", "s", "1", "true", "yes", "x", "ativo", "hipertenso", "diabetico", "diabético"}

def is_status_dead(v):
    if pd.isna(v): return False
    s = str(v).strip().lower()
    return any(x in s for x in ["obito", "óbito", "falec", "morto"])

def normalize_frame(df, source):
    df = df.copy()
    mapping = {}
    for key, candidates in ALIASES.items():
        c = find_col(df, candidates)
        if c is not None:
            mapping[key] = c
    out = pd.DataFrame(index=df.index)
    out["Nome"] = df[mapping["name"]].astype("string").str.strip() if "name" in mapping else ""
    out["CNS"] = df[mapping["cns"]].astype("string").str.replace(r"\.0$", "", regex=True).str.strip() if "cns" in mapping else ""
    out["CPF"] = df[mapping["cpf"]].astype("string").str.replace(r"\D", "", regex=True).str.strip() if "cpf" in mapping else ""
    out["Prontuário"] = df[mapping["record"]].astype("string").str.strip() if "record" in mapping else ""
    out["Data de nascimento"] = pd.to_datetime(df[mapping["dob"]], errors="coerce", dayfirst=True) if "dob" in mapping else pd.NaT
    out["Idade"] = pd.to_numeric(df[mapping["age"]], errors="coerce") if "age" in mapping else pd.NA
    out["Altura (m)"] = pd.to_numeric(df[mapping["height"]].astype(str).str.replace(",", ".", regex=False), errors="coerce") if "height" in mapping else pd.NA
    out["Peso (kg)"] = pd.to_numeric(df[mapping["weight"]].astype(str).str.replace(",", ".", regex=False), errors="coerce") if "weight" in mapping else pd.NA
    out["IMC"] = pd.to_numeric(df[mapping["bmi"]].astype(str).str.replace(",", ".", regex=False), errors="coerce") if "bmi" in mapping else pd.NA
    out["Tabagista"] = df[mapping["smoker"]].astype("string") if "smoker" in mapping else ""
    out["HAS"] = df[mapping["has"]].astype("string") if "has" in mapping else ""
    out["Diabetes"] = df[mapping["diabetes"]].astype("string") if "diabetes" in mapping else ""
    out["Risco"] = df[mapping["risk"]].astype("string") if "risk" in mapping else ""
    out["Exame Laboratorial"] = df[mapping["lab"]].astype("string") if "lab" in mapping else ""
    out["HB glicada"] = df[mapping["hba1c"]].astype("string") if "hba1c" in mapping else ""
    out["Fundoscopia"] = df[mapping["fundoscopy"]].astype("string") if "fundoscopy" in mapping else ""
    out["Pé Diabético"] = df[mapping["diabetic_foot"]].astype("string") if "diabetic_foot" in mapping else ""
    out["Encaminhado"] = df[mapping["referral"]].astype("string") if "referral" in mapping else ""
    out["Última consulta"] = pd.to_datetime(df[mapping["last_visit"]], errors="coerce", dayfirst=True) if "last_visit" in mapping else pd.NaT
    out["Status informado"] = df[mapping["status"]].astype("string") if "status" in mapping else ""
    out["Programa"] = df[mapping["program"]].astype("string") if "program" in mapping else ""
    out["Bairro"] = df[mapping["neighborhood"]].astype("string") if "neighborhood" in mapping else ""
    out["Cidade"] = df[mapping["city"]].astype("string") if "city" in mapping else ""
    out["Medicamentos"] = df[mapping["medication"]].astype("string") if "medication" in mapping else ""
    out["Data de retorno"] = pd.to_datetime(df[mapping["return_date"]], errors="coerce", dayfirst=True) if "return_date" in mapping else pd.NaT
    out["Fonte"] = source
    return out

def patient_key(row):
    for col in ["CPF", "CNS", "Prontuário"]:
        v = str(row.get(col, "")).strip()
        if v and v.lower() not in {"<na>", "nan", "none", "nat"}:
            digits = re.sub(r"\D", "", v)
            if digits:
                return f"{col}:{digits}"
    name = norm_col(row.get("Nome", ""))
    dob = row.get("Data de nascimento")
    dobstr = dob.strftime("%Y-%m-%d") if pd.notna(dob) else ""
    return f"NOME:{name}|NASC:{dobstr}" if name else f"SEM_ID:{row.name}"

def yes_series(s):
    return s.fillna("").astype(str).str.strip().str.lower().isin(["sim", "s", "1", "true", "yes", "x"])

def consolidate(df):
    df = df.copy()
    df["Chave do paciente"] = df.apply(patient_key, axis=1)
    grouped = []
    for key, g in df.groupby("Chave do paciente", dropna=False, sort=False):
        # Most recent consultation row is preferred for current values, but all source rows remain visible in raw records.
        g = g.copy()
        g["_date_sort"] = g["Última consulta"].fillna(pd.Timestamp("1900-01-01"))
        g = g.sort_values("_date_sort")
        r = g.iloc[-1].drop(labels=["_date_sort"]).to_dict()
        r["Fontes"] = ", ".join(sorted(set(g["Fonte"].dropna().astype(str))))
        r["Quantidade de registros"] = len(g)
        r["Hipertenso"] = any(yes_series(g["HAS"]))
        r["Diabético"] = any(yes_series(g["Diabetes"]))
        r["Falecido na fonte"] = any(g["Status informado"].apply(is_status_dead))
        r["Divergências"] = []
        if r["Falecido na fonte"] and str(r.get("Status informado", "")).strip().lower() in {"ativo", "ativa"}:
            r["Divergências"].append("Registro marcado como ativo apesar de constar como óbito")
        if len(g) > 1:
            for col in ["Nome", "Data de nascimento"]:
                vals = g[col].dropna().astype(str).unique()
                if len(vals) > 1:
                    r["Divergências"].append(f"Valores divergentes em {col}")
        r["Divergências"] = "; ".join(r["Divergências"])
        grouped.append(r)
    return pd.DataFrame(grouped)

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Navegação")
    page = st.radio("Ir para", ["Dashboard", "Pacientes", "Importação de planilhas", "Regras e informações"], label_visibility="collapsed")
    st.divider()
    st.caption("Gestão de Pacientes · MVP 0.1")
    demo_mode = st.toggle("Usar dados fictícios para demonstração", value=True)
    st.caption("Para apresentação, use apenas dados fictícios ou anonimizados.")

uploaded_files = []
if not demo_mode:
    with st.sidebar:
        uploaded_files = st.file_uploader(
            "Importar planilhas",
            type=["xlsx", "xls", "csv"],
            accept_multiple_files=True,
            help="Selecione uma ou mais planilhas. A versão inicial lê os arquivos enviados nesta sessão."
        )

if demo_mode:
    raw_frames = [normalize_frame(demo_data(), "Prontuário (dados fictícios)")]
else:
    raw_frames = []
    for f in uploaded_files:
        try:
            if f.name.lower().endswith(".csv"):
                raw = pd.read_csv(f, dtype=str, sep=None, engine="python")
            else:
                raw = pd.read_excel(f, dtype=str)
            raw_frames.append(normalize_frame(raw, f.name))
        except Exception as e:
            st.error(f"Não foi possível ler {f.name}: {e}")

if raw_frames:
    raw_all = pd.concat(raw_frames, ignore_index=True)
    patients = consolidate(raw_all)
else:
    raw_all = pd.DataFrame()
    patients = pd.DataFrame()

# ---------- Filters ----------
if not patients.empty:
    with st.sidebar:
        st.subheader("Filtros")
        search = st.text_input("Nome, CNS, CPF ou prontuário")
        conditions = st.multiselect("Condições", ["Hipertenso", "Diabético"], default=[])
        status_filter = st.selectbox("Status informado", ["Todos", "Ativo", "Inativo", "Óbito"])
        exam_filter = st.selectbox("Exame laboratorial", ["Todos", "Alterado", "Pendente", "Realizado/OK"])
        program_search = st.text_input("Programa contém")
        inactivity_days = st.select_slider("Sem consulta há mais de (dias)", options=[10, 15, 20, 30, 45, 60, 90, 120, 180], value=60)

    filtered = patients.copy()
    if search:
        q = search.strip().lower()
        cols = ["Nome", "CNS", "CPF", "Prontuário"]
        mask = filtered[cols].fillna("").astype(str).apply(lambda s: s.str.lower().str.contains(q, regex=False)).any(axis=1)
        filtered = filtered[mask]
    for condition in conditions:
        filtered = filtered[filtered[condition]]
    if status_filter != "Todos":
        if status_filter == "Óbito":
            filtered = filtered[filtered["Falecido na fonte"]]
        else:
            filtered = filtered[filtered["Status informado"].fillna("").str.lower() == status_filter.lower()]
    if exam_filter != "Todos":
        vals = filtered["Exame Laboratorial"].fillna("").astype(str).str.lower()
        if exam_filter == "Alterado":
            filtered = filtered[vals.str.contains("alter|anormal|ruim", regex=True)]
        elif exam_filter == "Pendente":
            filtered = filtered[vals.str.contains("pend|não|nao|aguard", regex=True)]
        else:
            filtered = filtered[vals.str.contains("realiz|normal|ok|feito", regex=True)]
    if program_search:
        filtered = filtered[filtered["Programa"].fillna("").astype(str).str.contains(program_search, case=False, regex=False)]

    cutoff = pd.Timestamp.today().normalize() - pd.Timedelta(days=int(inactivity_days))
    inactivity_mask = filtered["Última consulta"].isna() | (filtered["Última consulta"] < cutoff)
    # Only show inactivity as a filter if user enables it, so default dashboard does not hide recent patients.
    show_inactive_only = st.sidebar.checkbox(f"Somente sem consulta há mais de {inactivity_days} dias", value=False)
    if show_inactive_only:
        filtered = filtered[inactivity_mask]

    # ---------- Pages ----------
    if page == "Dashboard":
        st.subheader("Dashboard — Pacientes")
        st.caption("Indicadores calculados sobre pacientes consolidados; revise as regras antes de usar em produção.")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Pacientes únicos", f"{len(patients):,}".replace(",", "."))
        c2.metric("Hipertensos", int(patients["Hipertenso"].sum()))
        c3.metric("Diabéticos", int(patients["Diabético"].sum()))
        c4.metric("Ambas condições", int((patients["Hipertenso"] & patients["Diabético"]).sum()))
        c5.metric("Com divergências", int(patients["Divergências"].ne("").sum()))
        e1, e2, e3, e4 = st.columns(4)
        lab = patients["Exame Laboratorial"].fillna("").astype(str).str.lower()
        e1.metric("Exames alterados", int(lab.str.contains("alter|anormal|ruim", regex=True).sum()))
        e2.metric("Exames pendentes", int(lab.str.contains("pend|não|nao|aguard", regex=True).sum()))
        e3.metric("Óbitos identificados", int(patients["Falecido na fonte"].sum()))
        dates = patients["Última consulta"]
        e4.metric(f"Sem consulta > {inactivity_days} dias", int((dates.isna() | (dates < cutoff)).sum()))
        st.divider()
        st.markdown("#### Pacientes conforme os filtros")
        st.caption(f"{len(filtered)} paciente(s) correspondem aos filtros selecionados.")
        display_cols = ["Nome", "CNS", "Prontuário", "Idade", "Hipertenso", "Diabético", "Status informado", "Exame Laboratorial", "Última consulta", "Divergências"]
        st.dataframe(filtered[[c for c in display_cols if c in filtered.columns]], use_container_width=True, hide_index=True)
        st.download_button("⬇️ Exportar lista filtrada (CSV)", filtered.to_csv(index=False).encode("utf-8-sig"), "pacientes_filtrados.csv", "text/csv")
    elif page == "Pacientes":
        st.subheader("Pacientes — ficha consolidada")
        st.caption("Selecione um paciente para visualizar os campos e as fontes disponíveis.")
        options = filtered["Nome"].fillna("Sem nome").astype(str).tolist()
        if options:
            selected = st.selectbox("Paciente", options)
            row = filtered[filtered["Nome"].fillna("Sem nome").astype(str) == selected].iloc[0]
            if row["Divergências"]:
                st.error("Divergência identificada: " + row["Divergências"])
            elif row["Falecido na fonte"]:
                st.warning("Consta como óbito em pelo menos uma fonte. Confira os registros de origem.")
            else:
                st.success("Nenhuma divergência administrativa identificada pelas regras iniciais.")
            a, b, c = st.columns(3)
            a.metric("Hipertenso", "Sim" if row["Hipertenso"] else "Não")
            b.metric("Diabético", "Sim" if row["Diabético"] else "Não")
            c.metric("Registros agrupados", int(row["Quantidade de registros"]))
            st.markdown("#### Dados consolidados")
            st.dataframe(pd.DataFrame({"Campo": row.index, "Valor": [str(v) for v in row.values]}), use_container_width=True, hide_index=True)
            st.markdown("#### Registros de origem")
            st.dataframe(raw_all[raw_all.apply(lambda r: patient_key(r) == row["Chave do paciente"], axis=1)], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum paciente corresponde aos filtros.")
    elif page == "Importação de planilhas":
        st.subheader("Importação de planilhas")
        st.write("Desative **Usar dados fictícios para demonstração** na barra lateral para carregar arquivos reais.")
        if demo_mode:
            st.info("A aplicação está em modo de demonstração com dados fictícios.")
        if not patients.empty:
            st.markdown("#### Colunas reconhecidas após o mapeamento")
            st.dataframe(pd.DataFrame({"Campo consolidado": list(patients.columns)}), use_container_width=True, hide_index=True)
            st.markdown("#### Prévia dos dados importados")
            st.dataframe(raw_all.head(100), use_container_width=True, hide_index=True)
    else:
        st.subheader("Regras e informações")
        st.markdown("""
**Regras atualmente implementadas no MVP**
- Agrupamento por CPF, CNS ou prontuário; na ausência desses campos, nome + data de nascimento.
- Filtros para hipertensão, diabetes, status, programa, exame laboratorial e ausência de consulta.
- Detecção inicial de registros marcados como ativos apesar de conterem status de óbito em registros agrupados.
- Exportação da lista filtrada em CSV.

**Limitações importantes**
- Os nomes de colunas são reconhecidos por aproximação; confirme o mapeamento após cada importação.
- A planilha de prontuário fornecida até agora não inclui, necessariamente, CPF, status, data de consulta ou todos os campos exibidos.
- Resultados de exames precisam de regras e intervalos de referência validados por profissionais responsáveis.
- A aplicação ainda não persiste dados no PostgreSQL, não tem login e não escreve de volta nos arquivos de origem.
- A regularização automática está propositalmente desabilitada; esta versão apenas identifica e exibe informações para revisão.
        """)
else:
    st.subheader("Aguardando planilhas")
    st.info("Ative os dados fictícios ou envie uma ou mais planilhas na barra lateral.")
    st.markdown("Formatos aceitos: XLSX, XLS e CSV.")
