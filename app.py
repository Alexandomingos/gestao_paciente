import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Gestão de Pacientes", page_icon="🩺", layout="wide")
st.markdown("""<style>.block-container{padding-top:1rem} div[data-testid="stMetric"]{background:#fff;border:1px solid #dce6f3;padding:12px;border-radius:12px} div.stButton>button{border-radius:9px;border:1px solid #cbdcf2;font-weight:600}</style>""",unsafe_allow_html=True)
st.title("🩺 Gestão de Pacientes")
st.caption("MVP 0.2 • Consolidação de prontuários • Indicadores interativos • Dados fictícios")

def norm(s):
    s=str(s).strip().lower()
    for a,b in [("á","a"),("à","a"),("ã","a"),("â","a"),("é","e"),("ê","e"),("í","i"),("ó","o"),("ô","o"),("õ","o"),("ú","u"),("ç","c")]: s=s.replace(a,b)
    return re.sub(r"[^a-z0-9]+","",s)
aliases={
"Nome":["Pacientes","Paciente","Nome"],"CNS":["Cartão SUS","CNS"],"CPF":["CPF"],"Prontuário":["Prontuário"],
"Data de nascimento":["Data de nascimento"],"Idade":["Idade"],"Altura (m)":["Altura (m)","Altura"],"Peso (kg)":["Peso (kg)","Peso"],"IMC":["IMC"],
"Tabagista":["Tabagista"],"HAS":["HAS","Hipertensão"],"Diabetes":["Diabetes"],"HAS/DIA":["HAS/DIA"],"Risco":["Risco"],
"Exame Laboratorial":["Exame Laboratorial"],"HB glicada":["HB glicada"],"Fundoscopia":["Fundoscopia"],"Pé Diabético":["Pé Diabético"],
"Encaminhado":["Pcte encaminhado","Paciente encaminhado"],"Bairro":["Bairro"],"Cidade":["Cidade"],"Medicamentos":["Medicamentos","Remédios"],
"Última consulta":["Data da última consulta","Última consulta"],"Data de retorno":["Data de retorno","Próximo retorno"],"Status":["Status","Situação"],"Programa":["Programa","Programas"]}
def find_col(cols,candidates):
    m={norm(c):c for c in cols}
    for c in candidates:
        if norm(c) in m:return m[norm(c)]
    return None
def yes(s): return s.fillna("").astype(str).str.strip().str.lower().isin(["sim","s","1","true","yes","x"])
def read_file(f):
    raw=pd.read_excel(f,dtype=str) if f.name.lower().endswith((".xlsx",".xls")) else pd.read_csv(f,dtype=str,sep=None,engine="python")
    out=pd.DataFrame(index=raw.index)
    for target,cands in aliases.items():
        c=find_col(raw.columns,cands); out[target]=raw[c] if c else ""
    for c in ["Data de nascimento","Última consulta","Data de retorno"]: out[c]=pd.to_datetime(out[c],errors="coerce",dayfirst=True)
    for c in ["Idade","Altura (m)","Peso (kg)","IMC","HB glicada"]: out[c]=pd.to_numeric(out[c].astype(str).str.replace(",",".",regex=False),errors="coerce")
    out["Fonte"]=f.name
    out["Hipertenso"]=yes(out["HAS"]); out["Diabético"]=yes(out["Diabetes"])
    out["Óbito"]=out["Status"].fillna("").astype(str).str.lower().str.contains("óbito|obito|falec|morto",regex=True)
    lab=out["Exame Laboratorial"].fillna("").astype(str).str.lower()
    out["Exame normal"]=lab.str.contains("normal|ok|feito",regex=True)
    out["Exame pendente"]=lab.str.contains("pend|aguard|não realizado|nao realizado",regex=True)
    out["Exame alterado"]=lab.str.contains("alter|anormal|ruim",regex=True)
    return out,raw
def key(r):
    for c in ["CPF","CNS","Prontuário"]:
        v=str(r.get(c,"")).strip()
        if v and v.lower() not in ["nan","none","<na>"]:
            d=re.sub(r"\D","",v)
            if d:return c+":"+d
    name=norm(r.get("Nome","")); dob=r.get("Data de nascimento")
    dob=dob.strftime("%Y-%m-%d") if pd.notna(dob) and hasattr(dob,"strftime") else ""
    return "NOME:"+name+"|NASC:"+dob
def consolidate(df):
    df=df.copy(); df["Chave"]=df.apply(key,axis=1); result=[]
    df["Última consulta"]=pd.to_datetime(df["Última consulta"],errors="coerce")
    for _,g in df.groupby("Chave",sort=False,dropna=False):
        row=g.assign(_sort=g["Última consulta"].fillna(pd.Timestamp("1900-01-01"))).sort_values("_sort").iloc[-1].drop(labels=["_sort"]).to_dict()
        row["Registros agrupados"]=len(g); row["Hipertenso"]=bool(g["Hipertenso"].any()); row["Diabético"]=bool(g["Diabético"].any()); row["Óbito"]=bool(g["Óbito"].any())
        row["Sem movimentação"]=bool(g["Última consulta"].isna().all() or (g["Última consulta"].dropna() < (pd.Timestamp.today().normalize()-pd.Timedelta(days=60))).all())
        row["Divergência"]=bool(row["Óbito"] and str(row["Status"]).lower() in ["ativo","ativa"])
        result.append(row)
    return pd.DataFrame(result)
def metric_card(label,value,card_id,color):
    st.markdown(f"<div style='border:1px solid {color};border-radius:12px;padding:12px;background:#fff;min-height:88px'><div style='font-size:13px;color:#475569'>{label}</div><div style='font-size:27px;font-weight:750;color:{color}'>{value}</div></div>",unsafe_allow_html=True)
    if st.button("Ver lista",key="btn_"+card_id,use_container_width=True):
        st.session_state["card_filter"]=card_id
        st.rerun()

with st.sidebar:
    st.header("Navegação")
    if "active_page" not in st.session_state:st.session_state["active_page"]="Dashboard"
    page=st.radio("Tela",["Dashboard","Pacientes","Importação e dados"],key="active_page")
    st.divider(); st.subheader("Importação")
    uploads=st.file_uploader("Enviar planilhas",type=["xlsx","xls","csv"],accept_multiple_files=True)
    st.caption("Sem upload, a aplicação usa a planilha fictícia incluída no projeto.")
    st.subheader("Filtros")
    search=st.text_input("Buscar nome, CNS ou prontuário")
    conditions=st.multiselect("Condições",["Hipertenso","Diabético"])
    status_choice=st.selectbox("Status",["Todos","Ativo","Inativo","Óbito"])
    exam_choice=st.selectbox("Exame",["Todos","Normal","Pendente","Alterado"])
    program=st.text_input("Programa contém")
    days=st.select_slider("Sem movimentação há mais de (dias)",options=[10,15,20,30,45,60,90,120,180],value=60)
    only_inactive=st.checkbox("Aplicar filtro de sem movimentação")

frames=[]
if uploads:
    for f in uploads:
        try: frames.append(read_file(f)[0])
        except Exception as e: st.error(f"Falha ao ler {f.name}: {e}")
else:
    try:
        demo=pd.read_excel("planilha_prontuario_dados_ficticios.xlsx",dtype=str)
        from io import BytesIO
        b=BytesIO(); demo.to_excel(b,index=False); b.seek(0); b.name="Prontuario_ficticio.xlsx"
        frames.append(read_file(b)[0])
    except Exception:
        st.error("Inclua planilha_prontuario_dados_ficticios.xlsx no mesmo repositório do app.py ou envie um arquivo pela barra lateral.")
if frames:
    raw=pd.concat(frames,ignore_index=True); patients=consolidate(raw); base=patients.copy()
    if search:
        q=search.lower().strip(); base=base[base[["Nome","CNS","CPF","Prontuário"]].fillna("").astype(str).apply(lambda c:c.str.lower().str.contains(q,regex=False)).any(axis=1)]
    for c in conditions:base=base[base[c]]
    if status_choice=="Óbito":base=base[base["Óbito"]]
    elif status_choice!="Todos":base=base[base["Status"].fillna("").str.lower()==status_choice.lower()]
    if exam_choice!="Todos":base=base[base[{"Normal":"Exame normal","Pendente":"Exame pendente","Alterado":"Exame alterado"}[exam_choice]]]
    if program:base=base[base["Programa"].fillna("").astype(str).str.contains(program,case=False,regex=False)]
    cutoff=pd.Timestamp.today().normalize()-pd.Timedelta(days=days)
    inactive=base["Última consulta"].isna()|(base["Última consulta"]<cutoff)
    if only_inactive:base=base[inactive]
    cards=[
      ("Pacientes únicos",len(base),"all","#1769e0",base),
      ("Hipertensos",int(base["Hipertenso"].sum()),"has","#dc2626",base[base["Hipertenso"]]),
      ("Diabéticos",int(base["Diabético"].sum()),"dia","#dc2626",base[base["Diabético"]]),
      ("Diabéticos + hipertensos",int((base["Diabético"]&base["Hipertenso"]).sum()),"both","#7c3aed",base[base["Diabético"]&base["Hipertenso"]]),
      ("Óbitos",int(base["Óbito"].sum()),"dead","#64748b",base[base["Óbito"]]),
      ("Exames normais",int(base["Exame normal"].sum()),"normal","#16a34a",base[base["Exame normal"]]),
      ("Exames pendentes",int(base["Exame pendente"].sum()),"pending","#ca8a04",base[base["Exame pendente"]]),
      ("Exames alterados",int(base["Exame alterado"].sum()),"altered","#dc2626",base[base["Exame alterado"]]),
      ("Sem movimentação",int(inactive.sum()),"inactive","#ca8a04",base[inactive]),
      ("Divergências",int(base["Divergência"].sum()),"divergence","#dc2626",base[base["Divergência"]]),
    ]
    card_map={x[2]:x[4] for x in cards}
    if page=="Dashboard":
        st.subheader("Dashboard — Pacientes")
        st.caption(f"Todos os resumos são recalculados conforme os filtros laterais. Pacientes na base filtrada: {len(base)}.")
        for start in [0,5]:
            cols=st.columns(5)
            for col,item in zip(cols,cards[start:start+5]):
                with col:metric_card(item[0],item[1],item[2],item[3])
        selected=st.session_state.get("card_filter","")
        shown=card_map.get(selected,base)
        st.divider(); st.subheader("Lista de pacientes")
        if selected:
            st.info("Card selecionado: "+next((x[0] for x in cards if x[2]==selected),"")+" — lista combinada com os filtros atuais.")
            if st.button("Limpar seleção do card"):
                st.session_state["card_filter"]=""; st.rerun()
        st.caption(f"{len(shown)} paciente(s) exibidos.")
        cols=["Nome","CNS","Prontuário","Idade","Hipertenso","Diabético","Status","Exame Laboratorial","Última consulta","Divergência"]
        st.dataframe(shown[[c for c in cols if c in shown.columns]],use_container_width=True,hide_index=True)
        st.download_button("Exportar lista exibida (CSV)",shown.to_csv(index=False).encode("utf-8-sig"),"pacientes_filtrados.csv","text/csv")
    elif page=="Pacientes":
        st.subheader("Ficha consolidada do paciente")
        if not base.empty:
            selected_name=st.selectbox("Paciente",base["Nome"].fillna("Sem nome").astype(str).tolist())
            p=base[base["Nome"].fillna("Sem nome").astype(str)==selected_name].iloc[0]
            if p["Divergência"]:st.error("Possível divergência: consta como óbito e o status está ativo. Confirme identidade e fonte antes de corrigir.")
            elif p["Óbito"]:st.warning("Consta como óbito em pelo menos um registro.")
            else:st.success("Nenhuma divergência de óbito detectada pelas regras iniciais.")
            a,b,c,d=st.columns(4);a.metric("Hipertenso","Sim" if p["Hipertenso"] else "Não");b.metric("Diabético","Sim" if p["Diabético"] else "Não");c.metric("Status",str(p["Status"]));d.metric("Registros",int(p["Registros agrupados"]))
            st.dataframe(pd.DataFrame({"Campo":p.index,"Valor":[str(v) for v in p.values]}),use_container_width=True,hide_index=True)
        else:st.info("Nenhum paciente encontrado.")
    else:
        st.subheader("Importação e dados")
        st.write(f"Registros carregados: **{len(raw)}** | Pacientes consolidados: **{len(patients)}**")
        st.dataframe(raw,use_container_width=True,hide_index=True)
        st.download_button("Baixar base consolidada (CSV)",patients.to_csv(index=False).encode("utf-8-sig"),"base_consolidada.csv","text/csv")
else:st.info("Envie uma planilha para começar.")
