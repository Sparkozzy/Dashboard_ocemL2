# dash_guru_vendas_dashboard.py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
from urllib.parse import quote

# Função para ler Google Sheets publicamente via CSV
sheet_id = "1R13wt5QT5tgiWHM1YJNBe44ew-e_7xdfrSn2AmS19Fw"
metricas_sheet = quote("Métricas")
pagina1_sheet = quote("Página1")
metricas_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={metricas_sheet}"
pagina1_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={pagina1_sheet}"

def carregar_dados():
    metricas_df = pd.read_csv(metricas_url)
    pagina1_df = pd.read_csv(pagina1_url)

    # Formatando colunas e valores
    metricas_df.columns = metricas_df.columns.str.strip()
    pagina1_df.rename(columns={"Estado": "estado", "valor convertido": "valor", "Nome": "nome", "data de criação": "data", "Produtos": "plano"}, inplace=True)
    pagina1_df['valor'] = (
        pagina1_df['valor']
        .astype(str)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
        .astype(float)
    )
    pagina1_df["data"] = pd.to_datetime(pagina1_df["data"], dayfirst=True, errors='coerce')
    return metricas_df, pagina1_df

# App
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.title = "Dashboard - Escritório Milionário"

app.layout = dbc.Container([
    dcc.Interval(id='atualiza-dados', interval=60*1000, n_intervals=0),

    html.H1("Os Códigos do Escritório Milionário", className="text-center mt-4 mb-2 text-warning"),
    html.H4("Segundo Lançamento", className="text-center mb-4 text-light"),

    dbc.Row(id="cards-planos"),

    html.Div([
        dcc.Dropdown(id='dropdown-dia', className="mb-4", style={"color": "#2c2c2c", "backgroundColor": "#ffffff"}, placeholder="Selecione o dia", searchable=True)
    ], style={"color": "#ffffff"}),

    dbc.Row(id='indicadores-dia'),

    dbc.Row([
        dbc.Col(dcc.Graph(id="funnel-fig", style={"height": "700px"}))
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("valor convertido", className="text-center text-light mb-1"),
                html.H2(id="valor-total", className="text-center text-white")
            ])
        ], className="text-center"), md=4)
    ], className="mb-4"),

    html.Hr(),

    dbc.Row([
        dbc.Col(dcc.Graph(id="valor-estado"), md=6),
        dbc.Col(dcc.Graph(id="alunos-estado"), md=6)
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id="valor-tempo"), md=12)
    ])

], fluid=True)

@app.callback(
    Output('dropdown-dia', 'options'),
    Output('dropdown-dia', 'value'),
    Output('cards-planos', 'children'),
    Output('funnel-fig', 'figure'),
    Output('valor-total', 'children'),
    Output('valor-estado', 'figure'),
    Output('alunos-estado', 'figure'),
    Output('valor-tempo', 'figure'),
    Input('atualiza-dados', 'n_intervals')
)
def atualizar_dashboard(n):
    metricas_df, pagina1_df = carregar_dados()

    # Planos
    titanium = int(metricas_df.loc[metricas_df['Produtos'] == 'Titanium', 'Vendas'].values[0])
    iron = int(metricas_df.loc[metricas_df['Produtos'] == 'Iron', 'Vendas'].values[0])
    palladium = int(metricas_df.loc[metricas_df['Produtos'] == 'Palladium', 'Vendas'].values[0])

    cards = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([html.H5("Iron", className="card-title text-light"), html.H2(f"{iron}", className="card-text")]), color="secondary", className="text-center"), md=4),
        dbc.Col(dbc.Card(dbc.CardBody([html.H5("Titanium", className="card-title text-light"), html.H2(f"{titanium}", className="card-text")]), color="primary", className="text-center"), md=4),
        dbc.Col(dbc.Card(dbc.CardBody([html.H5("Palladium", className="card-title text-light"), html.H2(f"{palladium}", className="card-text")]), color="#CE9334", className="text-center"), md=4)
    ])

    # Funnel
    ingressos = metricas_df.loc[metricas_df['Etapas'] == 'Compradores de ingresso', 'Número'].values[0]
    checkin = metricas_df.loc[metricas_df['Etapas'] == 'Check in', 'Número'].values[0]
    participacao = metricas_df.loc[metricas_df['Etapas'] == 'Compradores que Compareceram', 'Número'].values[0]
    sinais = metricas_df.loc[metricas_df['Etapas'] == 'Pagaram sinal', 'Número'].values[0]
    conversao = metricas_df.loc[metricas_df['Etapas'] == 'Fechado', 'Número'].values[0]

    funnel_fig = go.Figure(go.Funnel(
        y=["Ingressos", "Check in", "Participação", "Sinais", "Conversão"],
        x=[ingressos, checkin, participacao, sinais, conversao],
        textinfo="label+value+percent previous",
        marker={"color": ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"]},
        opacity=0.9
    ))
    funnel_fig.update_layout(title="Funil do Evento", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")

    # Valor total convertido
    total_convertido = pagina1_df['valor'].sum()
    total_convertido_fmt = f"R$ {total_convertido/1000:,.2f} mil".replace(".", "@").replace(",", ".").replace("@", ",")

    # Valor por estado
    valor_estado = pagina1_df.groupby("estado")["valor"].sum().sort_values(ascending=False).reset_index()
    bar_valor_estado = px.bar(valor_estado, x="estado", y="valor", title="Valor / Estado")
    bar_valor_estado.update_layout(paper_bgcolor="#1e1e1e", plot_bgcolor="#1e1e1e", font_color="white")

    # Alunos por estado
    alunos_estado = pagina1_df.groupby("estado")["nome"].count().reset_index(name="alunos")
    bar_alunos_estado = px.bar(alunos_estado, x="estado", y="alunos", title="Alunos / Estado")
    bar_alunos_estado.update_layout(paper_bgcolor="#1e1e1e", plot_bgcolor="#1e1e1e", font_color="white")

    # Valor ao longo do tempo
    tempo_valor = pagina1_df.groupby(pagina1_df["data"].dt.date)["valor"].sum().reset_index()
    valor_tempo_fig = px.line(tempo_valor, x="data", y="valor", title="Valor Convertido ao Longo do Tempo")
    valor_tempo_fig.update_traces(mode="lines+markers", hovertemplate='R$ %{y:,.2f}<extra></extra>')
    valor_tempo_fig.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat=",.2f", paper_bgcolor="#1e1e1e", plot_bgcolor="#1e1e1e", font_color="white")

    secoes = metricas_df['Seções'].dropna().unique().tolist()

    return ([{"label": s, "value": s} for s in secoes], secoes[0], cards, funnel_fig, total_convertido_fmt, bar_valor_estado, bar_alunos_estado, valor_tempo_fig)

@app.callback(
    Output('indicadores-dia', 'children'),
    Input('dropdown-dia', 'value'),
    Input('atualiza-dados', 'n_intervals')
)
def atualizar_indicadores(dia, n):
    metricas_df, _ = carregar_dados()
    dados = metricas_df.loc[metricas_df['Seções'] == dia].iloc[0]
    return dbc.Col([
        html.Div([
            html.H5("Entradas", className="text-light"),
            html.H2(f"{int(dados['Entradas'])}", className="text-white")
        ], className="mb-3"),
        html.Div([
            html.H5("Máximo de audiência", className="text-light"),
            html.H2(f"{int(dados['Máximo de audiência'])}", className="text-white")
        ], className="mb-3"),
        html.Div([
            html.H5("Média de retenção", className="text-light"),
            html.H2(dados['Média de retenção'], className="text-white")
        ])
    ], md=3)


import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8050))
    app.run_server(host="0.0.0.0", port=port, debug=True)


