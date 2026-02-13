import json
import streamlit as st
from v2.output.charts.sentiment_types_chart import create_sentiment_types_chart
from v2.output.counts.sentiment_type_counts import count_sentiment_types
from v2.output.charts.negativity_gauge_meter import create_negativity_gauge

def load_and_process_data():
    """
    Loads the JSON and returns the data
    """
    try:
        return st.session_state['comments_file']
    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.error(f"Erro ao carregar dados: {e}")
        return []

def sentiment_analysis_page():
    """
    Returns page for sentiment types analysis.
    This function sets up the Streamlit page configuration and sidebar selection for sentiment types analysis.
    """
    data = load_and_process_data()
    st.session_state['comments_file'] = data
    
    st.title('Sentiment Analysis using Pysentimiento')

    with st.expander("Negativity Gauge Meter", expanded=True):
        if not data:
            st.warning("No data available.")
            return

        total_comments = len(data)
        negative_comments = sum(1 for c in data if c.get('sentiment') == 'NEG')
        negativity_percentage = (negative_comments / total_comments) * 100 if total_comments > 0 else 0

        # Cria e exibe o gauge       
        st.plotly_chart(
            create_negativity_gauge(negativity_percentage),
            use_container_width=True
        )

    # Grafico de barra com porcentagens de todos sentimentos em geral
    with st.expander('Sentiment Types in General', expanded=True):
        st.plotly_chart(
            create_sentiment_types_chart(
                count_sentiment_types(data)
            ),
            use_container_width=True
        )

    st.subheader("Filter Comments by Sentiment")
    sentiment_filter = st.selectbox(
        label="Choose sentiment:",
        options=["positive", "negative", "neutral"]
    )

    sentiment_map = {
        "positive": "POS",
        "negative": "NEG",
        "neutral": "NEU"
    }
    selected_label = sentiment_map[sentiment_filter]
    filtered_comments = [c for c in data if c.get("sentiment") == selected_label]

    st.write(f"Found {len(filtered_comments)} comments.")
    if filtered_comments:
        for comment in filtered_comments:
            author = comment.get("author", "")
            message = comment.get("message", "")
            st.write(f"- **{author}**: {message}")
    
        

