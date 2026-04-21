# --- CÓDIGO PARA dashboard_tarea_grupo_X.py ---

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

# ────────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="Supermarket Sales Dashboard",
    page_icon="🛒",
    layout="wide"
)
sns.set_theme(style="whitegrid", palette="muted")

# ────────────────────────────────────────────────
# CARGA DE DATOS
# ────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")
    df["Date"] = pd.to_datetime(df["Date"])
    df["Hour"] = pd.to_datetime(df["Time"], format="%H:%M").dt.hour
    df["DayOfWeek"] = df["Date"].dt.day_name()
    return df

df_full = load_data()

# ────────────────────────────────────────────────
# SIDEBAR — FILTROS GLOBALES
# ────────────────────────────────────────────────
st.sidebar.header("🔍 Filtros")

branch_map = {"A — Yangon": "A", "B — Mandalay": "B", "C — Naypyitaw": "C"}
branches_selected = st.sidebar.multiselect(
    "Sucursal",
    options=list(branch_map.keys()),
    default=list(branch_map.keys())
)
selected_codes = [branch_map[b] for b in branches_selected]

date_min = df_full["Date"].min().date()
date_max = df_full["Date"].max().date()
date_range = st.sidebar.date_input(
    "Rango de fechas",
    value=[date_min, date_max],
    min_value=date_min,
    max_value=date_max
)

if len(date_range) == 2:
    df = df_full[
        (df_full["Branch"].isin(selected_codes)) &
        (df_full["Date"] >= pd.Timestamp(date_range[0])) &
        (df_full["Date"] <= pd.Timestamp(date_range[1]))
    ].copy()
else:
    df = df_full[df_full["Branch"].isin(selected_codes)].copy()

# ────────────────────────────────────────────────
# ENCABEZADO
# ────────────────────────────────────────────────
st.title("🛒 Supermarket Sales — Dashboard de Análisis")
st.markdown("Explore las principales métricas de ventas, productos y experiencia de cliente de la cadena.")

# KPIs rápidos
col1, col2, col3, col4 = st.columns(4)
col1.metric("Transacciones", f"{len(df):,}")
col2.metric("Ventas totales", f"${df['Total'].sum():,.0f}")
col3.metric("Ticket promedio", f"${df['Total'].mean():,.1f}")
col4.metric("Rating promedio", f"{df['Rating'].mean():.2f} / 10")

st.divider()

# ────────────────────────────────────────────────
# ANÁLISIS 1 — EVOLUCIÓN TEMPORAL
# ────────────────────────────────────────────────
st.subheader("📈 Análisis 1: Evolución temporal de ventas")
st.caption("Gráfico de líneas con media móvil de 7 días para suavizar la variabilidad diaria.")

ventas_diarias = df.groupby("Date")["Total"].sum().reset_index().sort_values("Date")
ventas_diarias["MA7"] = ventas_diarias["Total"].rolling(window=7, center=True).mean()

fig1, ax1 = plt.subplots(figsize=(12, 4))
ax1.fill_between(ventas_diarias["Date"], ventas_diarias["Total"], alpha=0.25, color="steelblue")
ax1.plot(ventas_diarias["Date"], ventas_diarias["Total"], color="steelblue", lw=1.2, alpha=0.7, label="Ventas diarias")
ax1.plot(ventas_diarias["Date"], ventas_diarias["MA7"], color="tomato", lw=2, label="Media móvil 7d")
ax1.set_xlabel("Fecha")
ax1.set_ylabel("Ventas totales (USD)")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
ax1.legend()
ax1.tick_params(axis="x", rotation=30)
sns.despine(ax=ax1)
plt.tight_layout()
st.pyplot(fig1)

st.divider()

# ────────────────────────────────────────────────
# ANÁLISIS 2 — LÍNEAS DE PRODUCTO (MÉTRICA SELECCIONABLE)
# ────────────────────────────────────────────────
st.subheader("📦 Análisis 2: Rendimiento por línea de producto")

metrica = st.radio(
    "Selecciona la métrica de comparación:",
    options=["Total", "Quantity", "gross income"],
    horizontal=True
)
label_metrica = {"Total": "Ventas totales (USD)", "Quantity": "Unidades vendidas", "gross income": "Ingreso bruto (USD)"}[metrica]

rendimiento = df.groupby("Product line")[metrica].sum().sort_values(ascending=True).reset_index()

fig2, ax2 = plt.subplots(figsize=(9, 4))
bars = ax2.barh(rendimiento["Product line"], rendimiento[metrica],
                color=sns.color_palette("muted", 6), edgecolor="white")
for bar in bars:
    w = bar.get_width()
    ax2.text(w + w * 0.01, bar.get_y() + bar.get_height() / 2,
             f"{w:,.0f}", va="center", ha="left", fontsize=9)
ax2.set_xlabel(label_metrica)
ax2.set_xlim(0, rendimiento[metrica].max() * 1.15)
sns.despine(ax=ax2, left=True)
ax2.yaxis.set_tick_params(length=0)
plt.tight_layout()
st.pyplot(fig2)
st.caption("Gráfico de barras horizontales ordenadas. Selecciona la métrica en el control de radio.")

st.divider()

# ────────────────────────────────────────────────
# ANÁLISIS 4 — RATING POR SUCURSAL
# ────────────────────────────────────────────────
st.subheader("⭐ Análisis 4: Distribución del rating por sucursal")
st.caption("Violin plot: muestra la forma completa de la distribución del rating.")

branch_label_map = {"A": "A — Yangon", "B": "B — Mandalay", "C": "C — Naypyitaw"}
df_plot4 = df.copy()
df_plot4["Branch_label"] = df_plot4["Branch"].map(branch_label_map)

fig4, ax4 = plt.subplots(figsize=(8, 4))
order4 = [branch_label_map[b] for b in ["A", "B", "C"] if b in selected_codes]
sns.violinplot(data=df_plot4, x="Branch_label", y="Rating", ax=ax4,
               palette="muted", order=order4, inner="quartile", cut=0)
ax4.set_xlabel("Sucursal")
ax4.set_ylabel("Rating (1–10)")
ax4.set_ylim(0, 11)
sns.despine(ax=ax4)
plt.tight_layout()
st.pyplot(fig4)

st.divider()

# ────────────────────────────────────────────────
# ANÁLISIS 6 — MEDIOS DE PAGO (SEGMENTACIÓN VARIABLE)
# ────────────────────────────────────────────────
st.subheader("💳 Análisis 6: Preferencia de medios de pago")

seg_col = st.selectbox(
    "Dimensión de segmentación:",
    options=["Branch", "Gender", "Customer type", "Product line"]
)

pay_seg = (df.groupby([seg_col, "Payment"]).size().unstack(fill_value=0))
pay_seg_pct = pay_seg.div(pay_seg.sum(axis=1), axis=0) * 100

fig6, ax6 = plt.subplots(figsize=(10, 4))
pay_seg_pct.plot(kind="barh", stacked=True, ax=ax6,
                 color=["#4C72B0", "#DD8452", "#55A868"], edgecolor="white")
ax6.set_xlabel("Participación (%)")
ax6.set_ylabel(seg_col)
ax6.xaxis.set_major_formatter(mticker.PercentFormatter())
ax6.legend(title="Medio de pago", fontsize=9, loc="lower right")
sns.despine(ax=ax6)
plt.tight_layout()
st.pyplot(fig6)
st.caption("Barras apiladas al 100%. Cambia la dimensión de segmentación con el selectbox.")

st.divider()

# ────────────────────────────────────────────────
# ANÁLISIS 8 — MAPA DE CALOR HORA × DÍA
# ────────────────────────────────────────────────
st.subheader("🕐 Análisis 8: Mapa de calor de ventas — Hora × Día")
st.caption("Identifica los momentos de mayor demanda durante la semana.")

day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
day_order_es = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

heatmap_data = (df.groupby(["DayOfWeek", "Hour"])["Total"]
                .sum().unstack(fill_value=0)
                .reindex([d for d in day_order if d in df["DayOfWeek"].unique()]))
heatmap_data.index = [day_order_es[day_order.index(d)] for d in heatmap_data.index]

fig8, ax8 = plt.subplots(figsize=(13, 4))
sns.heatmap(heatmap_data, ax=ax8, cmap="YlOrRd", linewidths=0.3, linecolor="white",
            cbar_kws={"label": "Ventas totales (USD)"})
ax8.set_xlabel("Hora del día")
ax8.set_ylabel("Día de la semana")
ax8.tick_params(axis="x", rotation=0)
ax8.tick_params(axis="y", rotation=0)
plt.tight_layout()
st.pyplot(fig8)

# ────────────────────────────────────────────────
# PIE DE PÁGINA
# ────────────────────────────────────────────────
st.divider()
st.caption("Fuente: Supermarket Sales Dataset (Kaggle) | Visualización de Datos en Python") 