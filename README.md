# Gestão de Pacientes — MVP 0.2

## Arquivos
- `app.py`: aplicação Streamlit com filtros dinâmicos e cards clicáveis.
- `planilha_prontuario_dados_ficticios.xlsx`: 60 registros fictícios.
- `requirements.txt`: dependências.

## Execução local
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

## Publicação no Streamlit Cloud
Envie os três arquivos (`app.py`, `requirements.txt` e `planilha_prontuario_dados_ficticios.xlsx`) ao repositório GitHub usado pelo app publicado. Mantenha `app.py` como arquivo principal.

**Segurança:** a planilha é fictícia. Não use nem publique dados reais de saúde em uma aplicação pública. Antes de uso real, implemente autenticação, permissões, armazenamento seguro, auditoria e controles LGPD.

Os cards filtram a lista; os resumos são recalculados conforme os filtros da barra lateral. A seleção de um card funciona junto com os filtros atuais.
