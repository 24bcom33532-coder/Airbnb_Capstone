import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ---------------- PAGE / THEME ----------------
st.set_page_config(page_title="Airbnb Analytics Dashboard", page_icon="🏡", layout="wide")
NAVY = "#172B4D"
TEAL = "#168C8C"
CORAL = "#F28C7B"
PALETTE = [TEAL, NAVY, CORAL, "#8AA6C1", "#D8A657", "#7A9E7E"]
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = PALETTE

st.markdown(f"""
<style>
.stApp {{ background-color: #F7F9FC; }}
[data-testid="stHeader"] {{ background: rgba(247,249,252,0.9); }}
h1, h2, h3 {{ color: {NAVY}; }}
[data-testid="stMetric"] {{ background: white; border: 1px solid #E3EAF2; padding: 14px 16px; border-radius: 12px; }}
[data-testid="stSidebar"] {{ background-color: #EEF3F8; }}
</style>
""", unsafe_allow_html=True)

st.title("Airbnb Revenue & Customer Experience Analytics")
st.caption("An interactive analysis of listing prices, estimated revenue, estimated occupancy and customer experience.")

# ---------------- LOAD DATA ----------------

import os
import gdown
import pandas as pd
import streamlit as st

DATA_FILE = "Airbnb_Cleaned_Data.parquet"
DRIVE_FILE_ID = "1Vz-NHb_xIGmfl2wYE5GxsbqVd8gxq0En"

@st.cache_data
def load_data():
    if not os.path.exists(DATA_FILE):
        url = f"https://drive.google.com/uc?id={DRIVE_FILE_ID}"
        gdown.download(url, DATA_FILE, quiet=False)

    data = pd.read_parquet(DATA_FILE, engine="pyarrow")

    numeric_columns = [
        "price", "estimated_revenue_l365d", "estimated_occupancy_rate_pct",
        "estimated_occupancy_l365d", "review_scores_rating", "number_of_reviews",
        "number_of_reviews_ltm", "number_of_reviews_l30d", "reviews_per_month",
        "accommodates", "bedrooms", "beds", "price_per_guest",
        "estimated_revenue_per_occupied_night", "review_scores_accuracy",
        "review_scores_cleanliness", "review_scores_checkin",
        "review_scores_communication", "review_scores_location", "review_scores_value"
    ]

    for col in numeric_columns:
        if col in data.columns:
            data[col] = pd.to_numeric(
                data[col].astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("$", "", regex=False)
                .str.replace("%", "", regex=False),
                errors="coerce"
            )

    if "price" in data.columns:
        data.loc[data["price"] <= 0, "price"] = float("nan")

    if "room_type" in data.columns:
        data["room_type"] = data["room_type"].astype("string").str.strip()

    if "review_scores_rating" in data.columns:
        data.loc[~data["review_scores_rating"].between(0, 5), "review_scores_rating"] = float("nan")

    if "estimated_occupancy_rate_pct" in data.columns:
        data.loc[~data["estimated_occupancy_rate_pct"].between(0, 100), "estimated_occupancy_rate_pct"] = float("nan")

    return data
try:
    df = load_data()
except Exception as e:
    st.error("Dataset loading failed")
    st.exception(e)
    st.stop()

# Consistent room-type validity rule; keep missing room types out of room-type comparisons.
valid_room_mask = df["room_type"].notna() & df["room_type"].astype(str).str.strip().str.lower().ne("t") if "room_type" in df.columns else pd.Series(True, index=df.index)

# ---------------- FILTERS ----------------
st.sidebar.header("Dashboard Filters")
filtered = df
if "city" in filtered.columns:
    cities = sorted(filtered["city"].dropna().astype(str).unique().tolist())
    selected_cities = st.sidebar.multiselect("City", cities, default=cities)
    filtered = filtered[filtered["city"].astype(str).isin(selected_cities)] if selected_cities else filtered.iloc[0:0]
if "room_type" in filtered.columns:
    room_types = sorted(filtered.loc[valid_room_mask.reindex(filtered.index, fill_value=False), "room_type"].dropna().astype(str).unique().tolist())
    selected_rooms = st.sidebar.multiselect("Room type", room_types, default=room_types)
    filtered = filtered[filtered["room_type"].astype(str).isin(selected_rooms)] if selected_rooms else filtered.iloc[0:0]
if "price" in filtered.columns:
    valid_prices = filtered["price"].dropna()
    if not valid_prices.empty and valid_prices.min() < valid_prices.max():
        lo, hi = float(valid_prices.min()), float(valid_prices.max())
        price_range = st.sidebar.slider("Nightly price range (dataset units)", min_value=lo, max_value=hi, value=(lo, hi), step=max((hi-lo)/100, 1.0))
        # Exclude missing prices when a price range filter is active, so all displayed records satisfy it.
        filtered = filtered[filtered["price"].between(price_range[0], price_range[1])]
st.sidebar.caption("All KPIs and charts respond to the selected filters. Listings without a valid price are excluded when the price slider is used.")
if filtered.empty:
    st.warning("No listings match these filters. Please adjust them.")
    st.stop()

business = filtered
if "room_type" in business.columns:
    business = business[business["room_type"].notna() & business["room_type"].astype(str).str.strip().str.lower().ne("t")]

# ---------------- KPI CARDS ----------------
st.subheader("Performance Overview")
total_listings = filtered["id"].nunique() if "id" in filtered.columns else len(filtered)
median_price = filtered["price"].median() if "price" in filtered.columns else float("nan")
mean_revenue = business["estimated_revenue_l365d"].mean() if "estimated_revenue_l365d" in business.columns else float("nan")
mean_occupancy = business["estimated_occupancy_rate_pct"].mean() if "estimated_occupancy_rate_pct" in business.columns else float("nan")
valid_ratings = filtered.loc[filtered["review_scores_rating"].between(0.01, 5), "review_scores_rating"] if "review_scores_rating" in filtered.columns else pd.Series(dtype=float)
median_rating = valid_ratings.median()
k1,k2,k3,k4,k5 = st.columns(5)
k1.metric("Total Listings", f"{total_listings:,.0f}")
k2.metric("Median Nightly Price", f"{median_price:,.2f}" if pd.notna(median_price) else "N/A")
k3.metric("Mean Est. Annual Revenue", f"{mean_revenue:,.0f}" if pd.notna(mean_revenue) else "N/A")
k4.metric("Mean Est. Occupancy", f"{mean_occupancy:,.1f}%" if pd.notna(mean_occupancy) else "N/A")
k5.metric("Median Guest Rating", f"{median_rating:.2f}/5" if pd.notna(median_rating) else "N/A")
st.caption("Revenue and occupancy are dataset estimates, not verified actual results or profit. Price is displayed in the dataset's recorded units. Rating summaries use valid scores above 0 and up to 5.")
st.divider()

# ---------------- REVENUE / OCCUPANCY ----------------
st.subheader("Revenue & Occupancy Analysis")
left,right = st.columns(2)
if {"room_type","estimated_revenue_l365d"}.issubset(business.columns):
    d = business.dropna(subset=["room_type","estimated_revenue_l365d"])
    if not d.empty:
        s = d.groupby("room_type", as_index=False).agg(Mean_Estimated_Revenue=("estimated_revenue_l365d","mean"), Listings=("estimated_revenue_l365d","size"))
        with left:
            fig=px.bar(s,x="room_type",y="Mean_Estimated_Revenue",hover_data=["Listings"],title="Mean Estimated Annual Revenue by Room Type",labels={"room_type":"Room type","Mean_Estimated_Revenue":"Mean estimated annual revenue"})
            st.plotly_chart(fig,use_container_width=True)
        positive = d[d["estimated_revenue_l365d"] > 0]
        if not positive.empty:
            with right:
                fig=px.bar(positive.groupby("room_type",as_index=False).agg(Mean_Positive_Revenue=("estimated_revenue_l365d","mean"),Listings=("estimated_revenue_l365d","size")),x="room_type",y="Mean_Positive_Revenue",hover_data=["Listings"],title="Mean Estimated Revenue Among Listings with Positive Estimates",labels={"room_type":"Room type","Mean_Positive_Revenue":"Mean estimated revenue"})
                st.plotly_chart(fig,use_container_width=True)
if {"room_type","estimated_occupancy_rate_pct"}.issubset(business.columns):
    d=business.dropna(subset=["room_type","estimated_occupancy_rate_pct"])
    if not d.empty:
        s=d.groupby("room_type",as_index=False).agg(Mean_Estimated_Occupancy=("estimated_occupancy_rate_pct","mean"),Listings=("estimated_occupancy_rate_pct","size"))
        fig=px.bar(s,x="room_type",y="Mean_Estimated_Occupancy",hover_data=["Listings"],title="Mean Estimated Occupancy by Room Type",labels={"room_type":"Room type","Mean_Estimated_Occupancy":"Mean estimated occupancy (%)"})
        st.plotly_chart(fig,use_container_width=True)

for xcol,ycol,title,xlabel,ylabel in [
    ("price","estimated_revenue_l365d","Nightly Price vs Estimated Annual Revenue","Nightly price (dataset units)","Estimated annual revenue (dataset units)"),
    ("estimated_occupancy_rate_pct","estimated_revenue_l365d","Estimated Occupancy vs Estimated Annual Revenue","Estimated occupancy rate (%)","Estimated annual revenue (dataset units)")]:
    if {xcol,ycol}.issubset(business.columns):
        d=business.dropna(subset=[xcol,ycol]).copy()
        if xcol=="price": d=d[d[xcol]>0]
        else: d=d[d[xcol].between(0,100)]
        d=d[d[ycol]>=0]
        if len(d)>10000: d=d.sample(10000,random_state=42)
        if not d.empty:
            fig=px.scatter(d,x=xcol,y=ycol,color="room_type" if "room_type" in d.columns else None,title=title,labels={xcol:xlabel,ycol:ylabel,"room_type":"Room type"},opacity=.55)
            st.plotly_chart(fig,use_container_width=True)
st.divider()

# ---------------- LISTING PROFILE / DISTRIBUTIONS ----------------
st.subheader("Listing Profile & Distributions")
c1,c2=st.columns(2)
if "room_type" in business.columns:
    s=business["room_type"].value_counts().rename_axis("Room type").reset_index(name="Listings")
    with c1:
        st.plotly_chart(px.bar(s,x="Room type",y="Listings",title="Number of Listings by Room Type"),use_container_width=True)
if "accommodates" in filtered.columns:
    d=filtered[filtered["accommodates"].between(1,16)].dropna(subset=["accommodates"]).copy()
    if not d.empty:
        d["Guest capacity"]=d["accommodates"].astype(int).astype(str)
        s=d["Guest capacity"].value_counts().sort_index().rename_axis("Guest capacity").reset_index(name="Listings")
        with c2: st.plotly_chart(px.bar(s,x="Guest capacity",y="Listings",title="Listings by Guest Capacity"),use_container_width=True)
c1,c2=st.columns(2)
if "bedrooms" in filtered.columns:
    d=filtered[filtered["bedrooms"].between(0,10)].dropna(subset=["bedrooms"]).copy()
    if not d.empty:
        d["Bedrooms"]=d["bedrooms"].astype(int).astype(str)
        s=d["Bedrooms"].value_counts().sort_index().rename_axis("Bedrooms").reset_index(name="Listings")
        with c1: st.plotly_chart(px.bar(s,x="Bedrooms",y="Listings",title="Listings by Number of Bedrooms"),use_container_width=True)
if "price" in filtered.columns:
    d=filtered.dropna(subset=["price"])
    if not d.empty:
        with c2: st.plotly_chart(px.histogram(d,x="price",nbins=50,title="Nightly Price Distribution",labels={"price":"Nightly price (dataset units)"}),use_container_width=True)
# 99th percentile display cap
for col,title,xlabel in [("price","Nightly Price Distribution — Up to 99th Percentile","Nightly price (dataset units)"),("estimated_revenue_l365d","Estimated Annual Revenue Distribution — Up to 99th Percentile","Estimated annual revenue (dataset units)")]:
    source=filtered if col=="price" else business
    if col in source.columns:
        d=source.dropna(subset=[col])
        if col=="price": d=d[d[col]>0]
        if not d.empty:
            p99=d[col].quantile(.99); cap=d[d[col]<=p99]
            fig=px.histogram(cap,x=col,nbins=50,marginal="box",title=title,labels={col:xlabel})
            st.plotly_chart(fig,use_container_width=True)
            extra=f"Skewness: {d[col].skew():.2f} | 99th percentile: {p99:,.2f}"
            if col=="estimated_revenue_l365d": extra+=f" | Median: {d[col].median():,.2f}"
            st.caption(extra)
if "estimated_occupancy_rate_pct" in business.columns:
    d=business.dropna(subset=["estimated_occupancy_rate_pct"])
    d=d[d["estimated_occupancy_rate_pct"].between(0,100)]
    if not d.empty:
        fig=px.histogram(d,x="estimated_occupancy_rate_pct",nbins=50,marginal="box",title="Estimated Occupancy Rate Distribution",labels={"estimated_occupancy_rate_pct":"Estimated occupancy rate (%)"})
        st.plotly_chart(fig,use_container_width=True)
        st.caption(f"Median: {d['estimated_occupancy_rate_pct'].median():.2f}% | Mean: {d['estimated_occupancy_rate_pct'].mean():.2f}% | Skewness: {d['estimated_occupancy_rate_pct'].skew():.2f}")
st.divider()

# ---------------- PRICING ANALYSIS ----------------
st.subheader("Pricing Analysis")
c1,c2=st.columns(2)
if {"price","room_type"}.issubset(business.columns):
    d=business.dropna(subset=["price","room_type"])
    if not d.empty:
        s=d.groupby("room_type",as_index=False).agg(Median_Price=("price","median"),Listings=("price","size"))
        with c1: st.plotly_chart(px.bar(s,x="room_type",y="Median_Price",hover_data=["Listings"],title="Median Nightly Price by Room Type",labels={"room_type":"Room type","Median_Price":"Median nightly price (dataset units)"}),use_container_width=True)
if {"accommodates","price"}.issubset(filtered.columns):
    d=filtered[filtered["accommodates"].between(1,16)].dropna(subset=["accommodates","price"])
    if len(d)>10000: d=d.sample(10000,random_state=42)
    if not d.empty:
        with c2: st.plotly_chart(px.box(d,x="accommodates",y="price",points=False,title="Nightly Price by Guest Capacity",labels={"accommodates":"Guests accommodated","price":"Nightly price (dataset units)"}),use_container_width=True)
if {"price","review_scores_rating"}.issubset(filtered.columns):
    d=filtered[(filtered["price"]>0)&(filtered["review_scores_rating"].between(.01,5))].dropna(subset=["price","review_scores_rating"])
    if len(d)>10000: d=d.sample(10000,random_state=42)
    if not d.empty:
        fig=px.scatter(d,x="price",y="review_scores_rating",color="room_type" if "room_type" in d.columns else None,title="Nightly Price vs Guest Rating",labels={"price":"Nightly price (dataset units)","review_scores_rating":"Guest rating (out of 5)","room_type":"Room type"},opacity=.55)
        st.plotly_chart(fig,use_container_width=True)
if {"city","price"}.issubset(filtered.columns):
    d=filtered.dropna(subset=["city"])
    if not d.empty:
        top=d["city"].value_counts().head(10).index
        s=d[d["city"].isin(top)].dropna(subset=["price"]).groupby("city",as_index=False).agg(Median_Price=("price","median"),Listings=("price","size")).sort_values("Listings")
        if not s.empty:
            fig=px.bar(s,x="Median_Price",y="city",orientation="h",hover_data=["Listings"],title="Median Nightly Price in Top 10 Cities by Listing Count",labels={"city":"City","Median_Price":"Median nightly price (dataset units)"})
            st.plotly_chart(fig,use_container_width=True)
st.divider()

# ---------------- CUSTOMER EXPERIENCE ----------------
st.subheader("Customer Experience Analytics")
valid_rating_rows=filtered[filtered["review_scores_rating"].between(.01,5)] if "review_scores_rating" in filtered.columns else pd.DataFrame()
c1,c2=st.columns(2)
if not valid_rating_rows.empty:
    with c1: st.plotly_chart(px.histogram(valid_rating_rows,x="review_scores_rating",nbins=30,title="Guest Rating Distribution",labels={"review_scores_rating":"Guest rating (out of 5)"}),use_container_width=True)
    if "room_type" in valid_rating_rows.columns:
        d=valid_rating_rows[valid_rating_rows["room_type"].notna()&valid_rating_rows["room_type"].astype(str).str.lower().ne("t")]
        s=d.groupby("room_type",as_index=False).agg(Median_Rating=("review_scores_rating","median"),Rated_Listings=("review_scores_rating","size")).sort_values("Median_Rating",ascending=False)
        if not s.empty:
            with c2:
                fig=px.bar(s,x="room_type",y="Median_Rating",hover_data=["Rated_Listings"],title="Median Guest Rating by Room Type",labels={"room_type":"Room type","Median_Rating":"Median guest rating (out of 5)"})
                fig.update_yaxes(range=[0,5]); st.plotly_chart(fig,use_container_width=True)
review_col="number_of_reviews_ltm" if "number_of_reviews_ltm" in filtered.columns else "number_of_reviews"
if review_col in business.columns and "room_type" in business.columns:
    d=business.dropna(subset=["room_type",review_col])
    if not d.empty:
        s=d.groupby("room_type",as_index=False).agg(Mean_Review_Activity=(review_col,"mean"),Listings=(review_col,"size"))
        st.plotly_chart(px.bar(s,x="room_type",y="Mean_Review_Activity",hover_data=["Listings"],title="Mean Reviews per Listing in the Selected Review Period",labels={"room_type":"Room type","Mean_Review_Activity":"Mean number of reviews"}),use_container_width=True)
if {"room_type","price","review_scores_rating"}.issubset(filtered.columns):
    d=business[business["price"].notna()&business["review_scores_rating"].between(.01,5)]
    if not d.empty:
        s=d.groupby("room_type",as_index=False).agg(Median_Price=("price","median"),Median_Rating=("review_scores_rating","median"),Listing_Count=("id","nunique") if "id" in d.columns else ("price","size"))
        fig=go.Figure()
        fig.add_trace(go.Bar(x=s["room_type"],y=s["Median_Price"],name="Median nightly price",marker_color=TEAL,yaxis="y"))
        fig.add_trace(go.Scatter(x=s["room_type"],y=s["Median_Rating"],name="Median guest rating",mode="lines+markers",line=dict(color=CORAL,width=3),marker=dict(size=9),yaxis="y2"))
        fig.update_layout(title="Room Type Comparison: Median Price and Guest Rating",xaxis_title="Room type",yaxis=dict(
    title=dict(
        text="Median nightly price (dataset units)",
        font=dict(color=NAVY)
    )
),yaxis2=dict(title="Median guest rating (out of 5)",overlaying="y",side="right",range=[0,5]),legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="left",x=0))
        st.plotly_chart(fig,use_container_width=True)
        st.caption("The two measures use separate vertical axes because they have different scales.")
st.divider()

# ---------------- CORRELATION ----------------
st.subheader("Relationships & Correlations")
candidates=["price","accommodates","bedrooms","beds","number_of_reviews","review_scores_rating","estimated_revenue_l365d","estimated_occupancy_l365d","estimated_occupancy_rate_pct"]
cols=[c for c in candidates if c in filtered.columns]
if len(cols)>=2:
    d=filtered[cols].copy()
    if "price" in d.columns: d.loc[d["price"]<=0,"price"]=float("nan")
    corr=d.apply(pd.to_numeric,errors="coerce").corr(method="pearson",min_periods=2)
    fig=px.imshow(corr,text_auto=".2f",aspect="auto",color_continuous_scale=[[0,"#C45A56"],[.5,"#FFFFFF"],[1,TEAL]],zmin=-1,zmax=1,title="Pearson Correlation Heatmap")
    st.plotly_chart(fig,use_container_width=True)
    st.caption("Correlation measures linear association, not causation. Pairwise missing values are excluded. Occupancy count and occupancy percentage may be conceptually related, so interpret both together.")
else: st.info("Not enough numeric fields are available to calculate correlations.")
st.divider()

# ---------------- LISTING TABLE ----------------
st.subheader("Explore Individual Listings")
preferred=["name","city","neighbourhood","room_type","property_type","price","accommodates","bedrooms","estimated_revenue_l365d","estimated_occupancy_rate_pct","review_scores_rating","number_of_reviews"]
shown=[c for c in preferred if c in filtered.columns]
if shown:
    st.dataframe(filtered[shown].head(1000),use_container_width=True,hide_index=True)
    st.caption(f"Showing up to 1,000 listings from {len(filtered):,} filtered records.")
st.caption("Prepared for academic analysis. Estimated metrics are not audited financial results, and observed associations should not be interpreted as causal relationships.")