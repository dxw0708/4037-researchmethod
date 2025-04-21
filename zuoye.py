
import dash, dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px

kcal = pd.read_csv('Results_21Mar2022.csv')
cap  = pd.read_csv('Results_21MAR2022_nokcaladjust.csv')
kcal['scenario'] = 'Per 1000 kcal'
cap['scenario']  = 'Per capita'
df = pd.concat([kcal, cap], ignore_index=True)

metrics = ['mean_ghgs','mean_land','mean_watscar','mean_eut',
           'mean_ghgs_ch4','mean_ghgs_n2o','mean_bio',
           'mean_watuse','mean_acid']

DIET_LABELS = {
    "meat100" : "High meat‑eaters",
    "meat"    : "Medium meat‑eaters",
    "meat50"  : "Low meat‑eaters",
    "fish"    : "Fish‑eaters",
    "veggie"  : "Vegetarians",
    "vegan"   : "Vegans"
}
DISPLAY = {
    "mean_ghgs"      : "GHG emissions (kg CO₂‑eq)",
    "mean_land"      : "Agricultural land use (m²)",
    "mean_watscar"   : "Water scarcity index",
    "mean_eut"       : "Eutrophication (g PO₄‑eq)",
    "mean_ghgs_ch4"  : "CH₄ from livestock (kg)",
    "mean_ghgs_n2o"  : "N₂O from fertiliser (kg)",
    "mean_bio"       : "Biodiversity loss (species⋅day)",
    "mean_watuse"    : "Irrigation water use (m³)",
    "mean_acid"      : "Acidification potential"
}


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.JOURNAL])

app.layout = dbc.Container([
    html.H4("Environmental Footprint Treemap (Scarborough et al 2023)",
            className="mt-3"),

    dbc.Row([
        dbc.Col([
            dbc.Input(id="search-box", placeholder="Search diet groups/ age groups / gender groups",
                      debounce=True, size="sm")
        ], md=4),

    dbc.Col(
        dcc.Dropdown(
        options=[{"label": DISPLAY[m], "value": m} for m in metrics],
        value="mean_ghgs",
        id="size-metric", clearable=False), md=3),
        # dbc.Col([
        #
        #     dcc.Dropdown(metrics, value="mean_ghgs",
        #                  id="size-metric", clearable=False,
        #                  style={"width":"100%"})
        # ], md=3),
        dbc.Col([
            dcc.Dropdown(
                options=[{"label": DISPLAY[m], "value": m} for m in metrics],
                value="mean_land",
                id="color-metric", clearable=False)
        ], md=3),

        dbc.Col([
            dcc.Dropdown(["Per 1000 kcal","Per capita"],
                         value="Per 1000 kcal",
                         id="scenario", clearable=False)
        ], md=2),
    ], className="mb-2"),

    dcc.Graph(id="treemap", config={"displayModeBar":False}, style={"height":"650px"}),
], fluid=True)

# ---------- 回调 ----------
@app.callback(
    Output("treemap", "figure"),
    [Input("scenario","value"),
     Input("size-metric","value"),
     Input("color-metric","value"),
     Input("search-box","value")]
)
def update_treemap(scen, size_col, color_col, keyword):

    d = df[df["scenario"]==scen].copy()

    if keyword:
        kw = keyword.lower()
        mask = (d['diet_group'].str.contains(kw, case=False) |
                d['age_group'].str.contains(kw, case=False) |
                d['sex'].str.contains(kw, case=False))
        d = d[mask]

    # 三级聚合，避免节点过多
    d = (d
         .groupby(['diet_group','age_group','sex'], as_index=False)
         [metrics].mean())

    d['diet_label'] = d['diet_group'].map(DIET_LABELS)

    fig = px.treemap(
        d,
        path=['diet_label', 'age_group', 'sex'],
        values=size_col,
        color=color_col,
        color_continuous_scale= "Reds",
        range_color=[d[color_col].min(), d[color_col].max()],
        height=650,
        labels=DISPLAY
    )

    # fig.update_traces(marker=dict(line=dict(color="#eceff5", width=1)))
    fig.update_traces(
        marker=dict(line=dict(color="#eceff5", width=1)),
        hovertemplate=(
                "<b>%{label}</b><br>" +
                f"{DISPLAY[size_col]}: %{{value:.4f}}<br>" +
                f"{DISPLAY[color_col]}: %{{customdata[0]:.4f}}<extra></extra>"
        ),
        customdata=d[[color_col]].values
    )

    fig.update_layout(margin=dict(t=30,l=0,r=0,b=0))
    return fig


if __name__ == "__main__":
    app.run(debug=True)

