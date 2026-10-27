# Gestão de Pacientes — Streamlit MVP 0.1

Primeira versão demonstrativa com dados fictícios e importação de planilhas.

## Requisitos
- Python 3.10 ou superior
- pip

## Instalação local

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

O Streamlit abrirá a aplicação no navegador, normalmente em `http://localhost:8501`.

## Como testar
1. Inicie com o modo "Usar dados fictícios para demonstração" ativado.
2. Navegue por Dashboard, Pacientes e Importação.
3. Para importar arquivos, desative o modo de dados fictícios na barra lateral e envie um ou mais arquivos XLSX, XLS ou CSV.
4. Confira os campos reconhecidos e os resultados; os cabeçalhos podem variar entre fontes.

## Publicação para demonstração
O projeto pode ser publicado no Streamlit Community Cloud conectando um repositório GitHub e escolhendo `app.py` como arquivo principal.

**Importante:** não publique dados reais, CPF, CNS, nomes ou informações de saúde em um app público. Use somente dados fictícios/anonimizados para demonstrações. Para uso real, implementar autenticação, autorização, armazenamento seguro, gestão de segredos, política de retenção e controles compatíveis com a LGPD antes de disponibilizar a aplicação a profissionais.

## Escopo desta versão
- Dashboard de indicadores
- Importação múltipla de Excel/CSV na sessão
- Mapeamento inicial de cabeçalhos conhecidos
- Agrupamento por CPF, CNS, prontuário ou nome + nascimento
- Filtros e exportação CSV
- Visualização da ficha consolidada e registros de origem
- Regras iniciais de inconsistência

## Ainda não implementado
- Persistência em banco de dados
- Login e permissões por profissional
- Integração com planilhas de óbitos, consultas, exames e programas com regras específicas
- Escrita de volta em sistemas/arquivos de origem
- Regularização automática em lote
- Auditoria persistente
