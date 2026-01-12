import json
import streamlit as st
from v2.output.charts.sentiment_types_chart import create_sentiment_types_chart
from v2.output.counts.sentiment_type_counts import count_sentiment_types
from v2.output.charts.negativity_gauge_meter import *
from v2.output.peaks.sentiment_peaks import get_sentiments_peak

# Lazy import for pysentimiento to avoid loading it if not needed
def get_sentiment_analyzer():
    """Lazy load sentiment analyzer"""
    try:
        from pysentimiento import create_analyzer
        return create_analyzer(task="sentiment", lang="pt")
    except ImportError:
        st.error("pysentimiento not installed. Run: pip install pysentimiento")
        return None

@st.cache_data
def load_and_process_data():
    """
    Loads the JSON, converts time strings to seconds and returns the data
    """
    try:
        data = st.session_state['comments_file']
        
        for comment in data:
            comment['time_in_seconds'] = time_str_to_seconds(comment.get('time_elapsed', '0:0'))
        
        return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.error(f"Erro ao carregar o arquivo JSON em '{path}': {e}")
        return []

def classify_sentiments(comments_list):
    """
    Classifies sentiments for all comments in the list.
    Adds or updates the 'sentiment' field with 'POS', 'NEG', or 'NEU'.
    """
    analyzer = get_sentiment_analyzer()
    if analyzer is None:
        return comments_list, 0
    
    classified_count = 0
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, comment in enumerate(comments_list):
        message = comment.get("message", "")
        
        if not message.strip():
            comment["sentiment"] = "NEU"
        else:
            try:
                result = analyzer.predict(message)
                comment["sentiment"] = result.output  # 'POS', 'NEU', 'NEG'
                classified_count += 1
            except Exception as e:
                st.warning(f"Error classifying comment {idx}: {e}")
                comment["sentiment"] = "NEU"
        
        # Update progress
        progress = (idx + 1) / len(comments_list)
        progress_bar.progress(progress)
        status_text.text(f"Classifying: {idx + 1}/{len(comments_list)} comments...")
    
    progress_bar.empty()
    status_text.empty()
    
    return comments_list, classified_count

def sentiment_analysis_page():
    """
    Returns page for sentiment types analysis.
    This function sets up the Streamlit page configuration and sidebar selection for sentiment types analysis.
    """
    
    if 'comments_file' not in st.session_state or st.session_state['comments_file'] is None:
        st.error("No comments data loaded. Please upload a JSON file first.")
        return
    
    data = st.session_state['comments_file']
    
    for comment in data:
        if 'time_in_seconds' not in comment:
            comment['time_in_seconds'] = time_str_to_seconds(comment.get('time_elapsed', '0:0'))
    
    st.title('Sentiment Analysis using Pysentimiento')
    
    has_sentiment = all('sentiment' in comment for comment in data) if data else False
    
    with st.expander("Sentiment Classification", expanded=not has_sentiment):
        if not has_sentiment:
            st.warning("Comments do not have sentiment classification yet.")
        else:
            total_classified = sum(1 for c in data if 'sentiment' in c and c['sentiment'] in ['POS', 'NEG', 'NEU'])
            st.info(f"{total_classified} of {len(data)} comments are classified.")
        
        st.markdown("""
        **Classification Options:**
        - **Classify All**: Analyzes all comments and adds sentiment (POS/NEG/NEU)
        - **Reclassify**: Re-analyzes all comments (overwrites existing classifications)
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Classify All Comments", use_container_width=True):
                with st.spinner("Classifying comments using Pysentimiento..."):
                    load_and_process_data.clear()
                    
                    classified_data, count = classify_sentiments(data)
                    
                    st.session_state['comments_file'] = classified_data
                    
                    st.success(f"Successfully classified {count} comments!")
                    st.rerun()
        
        with col2:
            if st.button("Download Classified JSON", use_container_width=True, disabled=not has_sentiment):
                if has_sentiment:
                    json_str = json.dumps(data, ensure_ascii=False, indent=2)
                    st.download_button(
                        label="Download JSON",
                        data=json_str,
                        file_name="comments_classified.json",
                        mime="application/json"
                    )
    
    st.markdown("---")
    
    if not has_sentiment:
        st.info("Please classify the comments first to see the analysis.")
        return

    with st.expander("Negativity Gauge Meter", expanded=True):
        if not data:
            st.warning("No data available.")
            return

        # Define os limites do slider
        min_time = data[0]['time_in_seconds']
        max_time = data[-1]['time_in_seconds']

        if min_time >= max_time:
            selected_seconds = max_time
            st.info(f"Only one timestamp available: `{seconds_to_time_str(selected_seconds)}`")
        else:
            selected_seconds = st.slider(
                label="Select the video/stream timestamp:",
                min_value=min_time,
                max_value=max_time,
                value=max_time
            )
            st.info(f"**Timestamp selected:** `{seconds_to_time_str(selected_seconds)}`")

        filtered_data = [c for c in data if c['time_in_seconds'] <= selected_seconds]

        # Calcula a porcentagem de negatividade
        if not filtered_data:
            negativity_percentage = 0.0
        else:
            total_comments = len(filtered_data)
            negative_comments = sum(1 for c in filtered_data if c.get('sentiment') == 'NEG')
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


    sentiment = st.selectbox(
            label="Select the sentiment to analyze:",
            options=["positive", "negative", "neutral"]
        )
    match sentiment:
        case "positive":
            peaks = get_sentiments_peak("POS", data)
        case "negative":
            peaks = get_sentiments_peak("NEG", data)
        case "neutral":
            peaks = get_sentiments_peak("NEU", data)

    for peak in peaks:
        with st.expander(f"Peak from {seconds_to_time_str(peak['start_time'])} to {seconds_to_time_str(peak['end_time'])}"):
            st.write(f"{sentiment.capitalize()}: {peak['sentiment']/ peak['count']:.2f}%")
            for comment in data:
                if peak['start_time'] <= comment['time_in_seconds'] < peak['end_time']:
                    st.write(f"- {comment['message']} (at {seconds_to_time_str(comment['time_in_seconds'])})")

        
