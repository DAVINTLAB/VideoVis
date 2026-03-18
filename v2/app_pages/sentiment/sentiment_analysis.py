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

    st.subheader("Comments by Sentiment")

    def render_sentiment_comments(sentiment_name, sentiment_label):
        filtered_comments = [c for c in data if c.get("sentiment") == sentiment_label]
        show_all_key = f"show_all_sentiment_{sentiment_name}"

        if show_all_key not in st.session_state:
            st.session_state[show_all_key] = False

        st.write(f"Found {len(filtered_comments)} comments.")
        if not filtered_comments:
            st.info("No comments found for this sentiment.")
            return

        comments_to_show = filtered_comments if st.session_state[show_all_key] else filtered_comments[:5]
        for comment in comments_to_show:
            author = comment.get("author", "")
            message = comment.get("message", "")
            st.write(f"- **{author}**: {message}")

        hidden_count = len(filtered_comments) - 5
        if hidden_count > 0 and not st.session_state[show_all_key]:
            if st.button(f"See all ({hidden_count} hidden)", key=f"see_all_{sentiment_name}"):
                st.session_state[show_all_key] = True
                st.rerun()
        elif hidden_count > 0 and st.session_state[show_all_key]:
            if st.button("Show less", key=f"show_less_{sentiment_name}"):
                st.session_state[show_all_key] = False
                st.rerun()

    tab_positive, tab_negative, tab_neutral = st.tabs(["Positive", "Negative", "Neutral"])

    with tab_positive:
        render_sentiment_comments("positive", "POS")

    with tab_negative:
        render_sentiment_comments("negative", "NEG")

    with tab_neutral:
        render_sentiment_comments("neutral", "NEU")
    
        

