import streamlit as st
import plotly.express as px
import pandas as pd

# ----- Sample Game Data -----
gameData = {
    "appid": "3332460",
    "name": "My Slime Garden",
    "short_description": (
        "Raise, nurture, and breed adorable slimes in a relaxing adventure where each slime "
        "is unique! Mix traits to create new slime companions and explore endless islands "
        "filled with secrets and surprises. Your perfect slime squad is waiting—how far can they go?"
    ),
    "release_date": "8 Jan, 2025",
    "developers": ["Slimebox Games"],
    "publishers": ["Slimebox Games"],
    "is_free": True,
    "review_stats": {
        "total_collected": 54,
        "positive_count": 47,
    },
    "genres": [
        {"description": "Action"},
        {"description": "Casual"},
        {"description": "Indie"},
        {"description": "Free To Play"},
        {"description": "Early Access"}
    ],
    "ai_summary": (
        "A relaxing slime breeding game with roguelike adventure elements. Players can raise, "
        "customize, and breed unique slimes with different traits and appearances. Key mechanics "
        "include collecting accessories, breeding for better stats, and roguelike island exploration "
        "with procedurally generated challenges."
    ),
    "recent_reviews": [
        {
            "text": "THE best creature collector breeding sim on steam",
            "voted_up": True,
            "playtime_forever": 4826
        },
        {
            "text": "4 hours to get my first SSSSS slime.. till i find out theres also higher letters... aeugh\n\nwill gamba some more",
            "voted_up": True,
            "playtime_forever": 1575
        },
        {
            "text": "starting slime is too weak to even get past the tutorial fight...what a joke",
            "voted_up": False,
            "playtime_forever": 7
        }
    ],
    "derived": {
        "engagement_score": 86,  # 0-100
        "interest_score": 74,
        "playtime_distribution": [
            {"name": "<10h", "value": 23},
            {"name": "10-50h", "value": 18},
            {"name": "50-100h", "value": 8},
            {"name": ">100h", "value": 5}
        ],
        "sentiment_breakdown": [
            {"name": "Positive", "value": 47},
            {"name": "Negative", "value": 7}
        ],
        "feature_sentiment": [
            {"feature": "Breeding", "positive": 92, "negative": 8},
            {"feature": "Combat", "positive": 65, "negative": 35},
            {"feature": "Customization", "positive": 87, "negative": 13},
            {"feature": "Progression", "positive": 71, "negative": 29}
        ],
        "playerbase_trend": [
            {"month": "Jan", "players": 125},
            {"month": "Feb", "players": 350},
            {"month": "Mar", "players": 410},
            {"month": "Apr", "players": 380},
            {"month": "May", "players": 425}
        ],
        "market_analysis": {
            "niche_rating": 72,
            "standout_features": ["Slime Breeding", "Roguelike Exploration", "Customization"],
            "underserved_audience": "Pet Sim + Roguelike players"
        }
    }
}

# ----- Page Config -----
st.set_page_config(
    page_title="My Slime Garden Dashboard",
    layout="wide"
)

# ----- Inject Custom CSS -----
st.markdown("""
<style>
/* General Background */
body, .block-container {
    background-color: #f8f9fc !important;
    font-family: "Open Sans", sans-serif;
}

/* Hide the default Streamlit header/footer */
header, footer {visibility: hidden;}

/* Top Bar (Header) */
.top-bar {
    background-color: #4F46E5; /* Purple-ish color */
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.top-bar-left h1 {
    margin: 0;
    font-size: 1.8rem;
}
.top-bar-left p {
    margin: 0;
    font-size: 0.9rem;
    color: #e2e2ff;
}
.top-bar-right {
    display: flex;
    gap: 1.5rem;
}
.metric-box {
    background-color: rgba(255,255,255,0.2);
    padding: 0.6rem 1rem;
    border-radius: 0.4rem;
    text-align: center;
}
.metric-box h2 {
    margin: 0;
    font-size: 1.4rem;
    font-weight: bold;
}
.metric-box p {
    margin: 0;
    font-size: 0.8rem;
}

/* Card container */
.card {
    background-color: #ffffff;
    padding: 1rem;
    margin-bottom: 1rem;
    border-radius: 0.5rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.card h2 {
    margin-top: 0;
    font-size: 1.2rem;
    margin-bottom: 0.5rem;
}
.card h3 {
    margin: 0.6rem 0 0.4rem;
    font-size: 1rem;
}

/* Some spacing for sub-sections */
.section {
    margin-top: 1rem;
}
.section h3 {
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
}

/* Make Plotly charts background white */
.element-container .element-container svg {
    background-color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)


# ----- Build the Header (Top Bar) -----
positive_count = gameData["review_stats"]["positive_count"]
total_reviews = gameData["review_stats"]["total_collected"]
pos_percent = (positive_count / total_reviews) * 100 if total_reviews > 0 else 0

st.markdown(f"""
<div class="top-bar">
    <div class="top-bar-left">
        <h1>{gameData["name"]}</h1>
        <p>{", ".join(gameData["developers"])} • {gameData["release_date"]} • {"Free to Play" if gameData["is_free"] else "Paid"}</p>
    </div>
    <div class="top-bar-right">
        <div class="metric-box">
            <h2>{pos_percent:.0f}%</h2>
            <p>Positive</p>
        </div>
        <div class="metric-box">
            <h2>{total_reviews}</h2>
            <p>Reviews</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ----- Tabs -----
tab_overview, tab_features, tab_community, tab_market = st.tabs([
    "Overview", "Features & Mechanics", "Community & Reviews", "Market Analysis"
])

# ====== TAB 1: Overview ======
with tab_overview:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Game Summary")
        st.write(gameData["short_description"])
        st.write("**AI Analysis:**", gameData["ai_summary"])

        st.markdown("**Genres:** " + ", ".join([g["description"] for g in gameData["genres"]]))
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Key Metrics")

        # Engagement Score
        st.write(f"**Player Engagement** ({gameData['derived']['engagement_score']}%)")
        st.progress(gameData["derived"]["engagement_score"] / 100)

        # Market Interest
        st.write(f"**Market Interest** ({gameData['derived']['interest_score']}%)")
        st.progress(gameData["derived"]["interest_score"] / 100)

        # Niche Rating
        niche = gameData["derived"]["market_analysis"]["niche_rating"]
        st.write(f"**Niche Rating** ({niche}%)")
        st.progress(niche / 100)
        st.markdown("</div>", unsafe_allow_html=True)

    col3, col4 = st.columns([2, 1])

    with col3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Recent Reviews")
        for review in gameData["recent_reviews"]:
            vote_status = "Positive" if review["voted_up"] else "Negative"
            hours = review["playtime_forever"] / 60
            st.markdown(f"**[{vote_status}]** {review['text']}")
            st.caption(f"Playtime: {hours:.1f}h")
        st.markdown("</div>", unsafe_allow_html=True)

    with col4:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Playtime Distribution")
        df_play = pd.DataFrame(gameData["derived"]["playtime_distribution"])
        fig_play = px.pie(df_play, names="name", values="value", hole=0.3)
        fig_play.update_layout(margin=dict(l=0, r=0, b=0, t=30))
        st.plotly_chart(fig_play, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Player Growth Trend")
    df_trend = pd.DataFrame(gameData["derived"]["playerbase_trend"])
    fig_trend = px.line(df_trend, x="month", y="players", markers=True)
    fig_trend.update_layout(margin=dict(l=0, r=0, b=0, t=30))
    st.plotly_chart(fig_trend, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ====== TAB 2: Features & Mechanics ======
with tab_features:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Feature Sentiment")
        df_feat = pd.DataFrame(gameData["derived"]["feature_sentiment"])
        # We'll plot stacked bar: positive vs negative
        fig_feat = px.bar(
            df_feat,
            y="feature",
            x=["positive", "negative"],
            orientation="h",
            barmode="stack",
            labels={"value": "Sentiment (%)", "feature": "Feature"},
            color_discrete_map={"positive": "#4caf50", "negative": "#f44336"}
        )
        fig_feat.update_layout(margin=dict(l=0, r=0, b=0, t=30))
        st.plotly_chart(fig_feat, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Standout Features")
        standout = gameData["derived"]["market_analysis"]["standout_features"]
        for s in standout:
            st.markdown(f"- **{s}**")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Similar Games")
    # You could store them in gameData; here we just show static examples
    similar_games = ["Slime Rancher", "Chao Garden", "Monster Sanctuary", "Ooblets"]
    cols = st.columns(len(similar_games))
    for idx, game in enumerate(similar_games):
        with cols[idx]:
            st.markdown(f"**{game}**")
            st.caption("Short descriptor here")
    st.markdown("</div>", unsafe_allow_html=True)


# ====== TAB 3: Community & Reviews ======
with tab_community:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Review Sentiment")
        df_sent = pd.DataFrame(gameData["derived"]["sentiment_breakdown"])
        fig_sent = px.pie(df_sent, names="name", values="value", hole=0.4)
        fig_sent.update_layout(margin=dict(l=0, r=0, b=0, t=30))
        st.plotly_chart(fig_sent, use_container_width=True)
        st.markdown(
            f"**{df_sent.iloc[0]['value']}** Positive, **{df_sent.iloc[1]['value']}** Negative"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Top Community Feedback")
        st.markdown("**Strengths**")
        st.write("- Addictive breeding mechanics with genetic inheritance")
        st.write("- Charming slime customization and accessorizing options")
        st.write("- Nostalgic Chao Garden feel with modern roguelike elements")

        st.markdown("**Areas for Improvement**")
        st.write("- Initial difficulty curve too steep for new players")
        st.write("- Missing tutorial or onboarding experience")
        st.write("- Controller support needs improvement")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Community Engagement")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Reviews", value=total_reviews)
    with c2:
        st.metric("Active Players", value=425)  # example
    with c3:
        st.metric("Positive Reviews", f"{pos_percent:.0f}%")
    with c4:
        st.metric("Avg. Playtime", "42.5h")  # example
    st.markdown("</div>", unsafe_allow_html=True)


# ====== TAB 4: Market Analysis ======
with tab_market:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Market Position")
        st.write(
            "This game occupies a unique position by combining pet simulation "
            "(slime breeding) with roguelike adventure elements, appealing to multiple "
            "audience segments."
        )
        underserved = gameData["derived"]["market_analysis"]["underserved_audience"]
        st.markdown(f"**Underserved Audience:** {underserved}")

        st.markdown("### Competitive Advantage")
        st.write("- Free-to-play model lowers barrier to entry")
        st.write("- More extensive breeding system than other creature collectors")
        st.write("- Action-oriented gameplay appeals to a broader audience")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Feature Implementation Quality")
        # Hard-coded sample data
        features_q = {
            "Breeding System": 85,
            "Combat Mechanics": 70,
            "Progression System": 65,
            "Customization Options": 90,
            "Visual Design": 80
        }
        for feat, score in features_q.items():
            st.write(f"**{feat}** ({score}%)")
            st.progress(score / 100)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Feature Validation Summary")
    colA, colB = st.columns(2)

    with colA:
        st.markdown("**Features Worth Implementing**")
        st.markdown("""
        - **Complex Breeding Systems**  
          Players highly value genetic inheritance and trait combination mechanics (92% positive).
        - **Extensive Customization**  
          Cosmetic personalization is extremely popular with 87% positive reception.
        """)

    with colB:
        st.markdown("**Features to Approach with Caution**")
        st.markdown("""
        - **Difficulty Balancing**  
          35% negative sentiment on combat suggests difficulty issues.
        - **Tutorial Integration**  
          Many negative reviews cite confusion about mechanics.
        """)

    st.markdown("</div>", unsafe_allow_html=True)
