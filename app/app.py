import streamlit as st
from statsbombpy import sb
import pandas as pd
import seaborn as sns
from mplsoccer import Pitch
import matplotlib.pyplot as plt

@st.cache_data
def carregar_competicoes():
    return sb.competitions()
 
 
@st.cache_data
def carregar_partidas(season_id, competition_id):
    return sb.matches(season_id=season_id, competition_id=competition_id)
 
 
@st.cache_data
def carregar_eventos(match_id):
    return sb.events(match_id=match_id)


st.header('Python para Sport Analytics')

st.caption(
    'Projeto Academico visando desenvolver a habilidade de desenvolver '
    'um programa utilizando Streamlit para analisar dados esportivos reais.'
)

st.divider()

with st.spinner('Carregando competições...'):
    df_comp = sb.competitions()

df_comp_nat = df_comp[
    df_comp['competition_international'] == False
]

df_comp_nat[['year1', 'year2']] = df_comp_nat[
    'season_name'
].str.split('/', expand=True)

competition_names = df_comp_nat[
    'competition_name'
].unique()

with st.sidebar:
    competition_selected = st.selectbox(
        'Selecione a competição',
        competition_names
    )

df_comp_sel = df_comp_nat[
    df_comp_nat['competition_name'] == competition_selected
]

season_names = df_comp_sel.sort_values(
    'year1'
)['season_name']

with st.sidebar:
    season_selected = st.selectbox(
        'Escolha a temporada',
        season_names
    )

df_comp_season_sel = df_comp_sel[
    (df_comp_sel['competition_name'] == competition_selected) &
    (df_comp_sel['season_name'] == season_selected)
]

with st.spinner('Carregando partidas...'):
    matches = sb.matches(
        season_id=df_comp_season_sel['season_id'].iloc[0],
        competition_id=df_comp_season_sel['competition_id'].iloc[0]
    )

matches['jogo'] = (
    matches['home_team'] +
    ' x ' +
    matches['away_team']
)

with st.sidebar:
    match_selected = st.selectbox(
        'Escolha a partida',
        matches['jogo']
    )

match_id = matches[
    matches['jogo'] == match_selected
]['match_id'].iloc[0]

with st.container():
    st.subheader('Partida Selecionada')
    st.write(match_selected)

t1, t2 = st.tabs(['Resumo', 'Analise'])

with t1:
    st.write('Informações da partida')

with t2:
    st.write('Analise da partida')

c1, c2 = st.columns(2)

with c1:
    st.subheader(
        matches.loc[
            matches['jogo'] == match_selected,
            'home_team'
        ].iloc[0]
    )

with c2:
    st.subheader(
        matches.loc[
            matches['jogo'] == match_selected,
            'away_team'
        ].iloc[0]
    )

with st.spinner(f'Carregando eventos da partida "{match_selected}"...'):
    events = sb.events(match_id=match_id)

st.subheader('Estatisticas da partida')

total_shots = len(
    events[events['type'] == 'Shot']
)

total_passes = len(
    events[events['type'] == 'Pass']
)

total_duel = len(
    events[events['type'] == 'Duel']
)

c1, c2, c3 = st.columns(3)

with c1:
    st.metric('Shots', total_shots)

with c2:
    st.metric('Passes', total_passes)

with c3:
    st.metric('Duel', total_duel)

st.header('Eventos da partida')

with st.form('form_filtro_eventos'):
    st.write('Filtros de visualização')

    jogador_filtro = st.selectbox(
        'Filtrar eventos por jogador',
        ['Todos'] + sorted(events['player'].dropna().unique().tolist()),
        key='filtro_eventos'
    )

    minuto_min, minuto_max = st.slider(
        'Intervalo de tempo (minutos)',
        min_value=int(events['minute'].min()),
        max_value=int(events['minute'].max()),
        value=(int(events['minute'].min()), int(events['minute'].max()))
    )

    tipo_evento = st.radio(
        'Tipo de evento',
        ['Todos', 'Pass', 'Shot', 'Duel'],
        horizontal=True
    )

    qtd_eventos = st.number_input(
        'Quantidade máxima de eventos a exibir',
        min_value=5, max_value=500, value=50, step=5
    )

    apenas_gols = st.checkbox('Mostrar apenas gols')

    aplicar = st.form_submit_button('Aplicar filtros')

events_filtrado = events[
    (events['minute'] >= minuto_min) & (events['minute'] <= minuto_max)
]

if jogador_filtro != 'Todos':
    events_filtrado = events_filtrado[events_filtrado['player'] == jogador_filtro]

if tipo_evento != 'Todos':
    events_filtrado = events_filtrado[events_filtrado['type'] == tipo_evento]

if apenas_gols:
    events_filtrado = events_filtrado[events_filtrado['shot_outcome'] == 'Goal']

events_show = events_filtrado[
    ['minute', 'team', 'player', 'type']
].head(qtd_eventos)

st.dataframe(events_show)

csv_data = events_show.to_csv(index=False).encode('utf-8')

st.download_button(
    label='📥 Baixar dados filtrados (CSV)',
    data=csv_data,
    file_name=f'eventos_{match_selected.replace(" ", "_")}.csv',
    mime='text/csv'
)

st.subheader('Comparação entre Jogadores')

col_comp1, col_comp2 = st.columns(2)

lista_jogadores = sorted(events['player'].dropna().unique().tolist())

with col_comp1:
    jogador_comp1 = st.selectbox('Jogador 1', lista_jogadores, key='comp1')

with col_comp2:
    jogador_comp2 = st.selectbox(
        'Jogador 2', lista_jogadores,
        index=1 if len(lista_jogadores) > 1 else 0, key='comp2'
    )


def estatisticas_jogador(nome):
    dados = events[events['player'] == nome]
    passes_j = dados[dados['type'] == 'Pass']
    chutes_j = dados[dados['type'] == 'Shot']
    gols_j = chutes_j[chutes_j['shot_outcome'] == 'Goal']
    return {
        'Passes': len(passes_j),
        'Chutes': len(chutes_j),
        'Gols': len(gols_j)
    }


stats1 = estatisticas_jogador(jogador_comp1)
stats2 = estatisticas_jogador(jogador_comp2)

col_comp1, col_comp2 = st.columns(2)

with col_comp1:
    st.metric(f'Passes — {jogador_comp1}', stats1['Passes'])
    st.metric(f'Chutes — {jogador_comp1}', stats1['Chutes'])
    st.metric(f'Gols — {jogador_comp1}', stats1['Gols'])

with col_comp2:
    st.metric(
        f'Passes — {jogador_comp2}', stats2['Passes'],
        delta=stats2['Passes'] - stats1['Passes']
    )
    st.metric(
        f'Chutes — {jogador_comp2}', stats2['Chutes'],
        delta=stats2['Chutes'] - stats1['Chutes']
    )
    st.metric(
        f'Gols — {jogador_comp2}', stats2['Gols'],
        delta=stats2['Gols'] - stats1['Gols']
    )

passes = events[
    events['type'] == 'Pass'
].copy()

passes['x'] = passes['location'].apply(
    lambda posicao: posicao[0]
)

passes['y'] = passes['location'].apply(
    lambda posicao: posicao[1]
)

passes['end_x'] = passes['pass_end_location'].apply(
    lambda posicao: posicao[0]
)

passes['end_y'] = passes['pass_end_location'].apply(
    lambda posicao: posicao[1]
)

with st.sidebar:
    jogador = st.selectbox(
        'Escolha o jogador para visualizar os passes',
        passes['player'].dropna().unique(),
        key='jogador_passes'
    )

passes_jogador = passes[
    passes['player'] == jogador
].tail(30)

st.subheader('Mapa de Passes')

if len(passes_jogador) == 0:
    st.info('Sem passes registrados para este jogador.')
else:
    completed = passes_jogador[passes_jogador['pass_outcome'].isna()]
    incomplete = passes_jogador[passes_jogador['pass_outcome'].notna()]

    pitch = Pitch(
        pitch_type='statsbomb',
        pitch_color='#0E1117',
        line_color='white'
    )

    fig, ax = pitch.draw(
        figsize=(12, 7)
    )

    pitch.arrows(
        completed['x'], completed['y'], completed['end_x'], completed['end_y'],
        ax=ax, width=2, headwidth=5, headlength=5,
        color='cyan', alpha=0.8, label=f'Certo ({len(completed)})'
    )

    pitch.arrows(
        incomplete['x'], incomplete['y'], incomplete['end_x'], incomplete['end_y'],
        ax=ax, width=2, headwidth=5, headlength=5,
        color='red', alpha=0.6, label=f'Errado ({len(incomplete)})'
    )

    ax.set_title(
        f'Mapa de Passes — {jogador} (últimos {len(passes_jogador)})',
        color='white', fontsize=14
    )
    ax.legend(loc='upper left', facecolor='#0E1117', labelcolor='white')

    st.pyplot(fig)

shots = events[
    events['type'] == 'Shot'
].copy()

shots['x'] = shots['location'].apply(
    lambda posicao: posicao[0]
)

shots['y'] = shots['location'].apply(
    lambda posicao: posicao[1]
)

with st.sidebar:
    player_shot = st.selectbox(
        'Escolha o jogador para visualizar os chutes',
        shots['player'].dropna().unique(),
        key='jogador_shots'
    )

shots_player = shots[
    shots['player'] == player_shot
]

total_gols = len(
    events[(events['type'] == 'Shot') & (events['shot_outcome'] == 'Goal')]
)

passes_jogador_total = events[
    (events['type'] == 'Pass') & (events['player'] == jogador)
]
passes_certos = passes_jogador_total[passes_jogador_total['pass_outcome'].isna()]

taxa_passes = (
    len(passes_certos) / len(passes_jogador_total) * 100
    if len(passes_jogador_total) > 0 else 0
)

chutes_jogador_total = events[
    (events['type'] == 'Shot') & (events['player'] == player_shot)
]
gols_jogador = chutes_jogador_total[chutes_jogador_total['shot_outcome'] == 'Goal']

taxa_conversao = (
    len(gols_jogador) / len(chutes_jogador_total) * 100
    if len(chutes_jogador_total) > 0 else 0
)

st.subheader('Indicadores de Desempenho')

m1, m2, m3 = st.columns(3)

with m1:
    st.metric(
        'Total de Gols na Partida',
        total_gols,
        delta='⚽ Placar' if total_gols > 0 else None,
        delta_color='off'
    )

with m2:
    st.metric(
        f'Passes Certos ({jogador})',
        f'{len(passes_certos)}/{len(passes_jogador_total)}',
        delta=f'{taxa_passes:.1f}%',
        delta_color='normal' if taxa_passes >= 70 else 'inverse'
    )

with m3:
    st.metric(
        f'Conversão de Chutes ({player_shot})',
        f'{len(gols_jogador)}/{len(chutes_jogador_total)}',
        delta=f'{taxa_conversao:.1f}%',
        delta_color='normal' if taxa_conversao >= 15 else 'inverse'
    )

st.subheader('Mapa de Chutes')

if len(shots_player) == 0:
    st.info('Sem chutes registrados para este jogador.')
else:
    pitch_shot = Pitch(
        pitch_type='statsbomb',
        pitch_color='#0E1118',
        line_color='white'
    )

    fig_shot, ax_shot = pitch_shot.draw(
        figsize=(12, 7)
    )

    gols = shots_player[shots_player['shot_outcome'] == 'Goal']
    outros = shots_player[shots_player['shot_outcome'] != 'Goal']

    pitch_shot.scatter(
        outros['x'], outros['y'],
        ax=ax_shot, s=120, color='red',
        edgecolors='white', linewidth=1.5, label=f'Chutes ({len(outros)})'
    )

    pitch_shot.scatter(
        gols['x'], gols['y'],
        ax=ax_shot, s=180, color='gold', marker='*',
        edgecolors='white', linewidth=1.5, label=f'Gols ({len(gols)})'
    )

    ax_shot.set_title(f'Mapa de Chutes — {player_shot}', color='white', fontsize=14)
    ax_shot.legend(loc='upper left', facecolor='#0E1117', labelcolor='white')

    st.pyplot(fig_shot)

st.subheader('Relação entre Passes e Finalizações por Jogador')

resumo_jogador = events.groupby('player').agg(
    passes=('type', lambda x: (x == 'Pass').sum()),
    chutes=('type', lambda x: (x == 'Shot').sum()),
    gols=('shot_outcome', lambda x: (x == 'Goal').sum())
).reset_index()

resumo_jogador = resumo_jogador[
    (resumo_jogador['passes'] > 0) | (resumo_jogador['chutes'] > 0)
]

fig_rel, ax_rel = plt.subplots(figsize=(8, 5))
sns.scatterplot(
    data=resumo_jogador, x='passes', y='chutes',
    size='gols', hue='gols', sizes=(50, 300),
    palette='viridis', ax=ax_rel
)
ax_rel.set_title('Passes vs Finalizações (tamanho/cor = gols)')
ax_rel.set_xlabel('Passes')
ax_rel.set_ylabel('Finalizações')
st.pyplot(fig_rel)

st.dataframe(
    resumo_jogador.sort_values('gols', ascending=False)
)
