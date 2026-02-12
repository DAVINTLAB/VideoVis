import json
import streamlit as st
from v2.output.charts.sentiment_types_chart import create_sentiment_types_chart
from v2.output.counts.sentiment_type_counts import count_sentiment_types
from v2.output.charts.negativity_gauge_meter import *
from v2.output.peaks.sentiment_peaks import get_sentiments_peak

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
        st.error(f"Erro ao carregar dados: {e}")
        return []

def sentiment_analysis_page():
    """
    Returns page for sentiment types analysis.
    This function sets up the Streamlit page configuration and sidebar selection for sentiment types analysis.
    """
    data = load_and_process_data()
    st.session_state['comments_file'] = data
    
    # Adiciona o tempo em segundos a cada comentário para facilitar a filtragem (o json nao sera modificado)
    for comment in data:
        comment['time_in_seconds'] = time_str_to_seconds(comment.get('time_elapsed', '0:0'))
    
    st.title('Sentiment Analysis using Pysentimiento')

    with st.expander("Negativity Gauge Meter", expanded=True):
        if not data:
            st.warning("No data available.")
            return

        # Define os limites do slider
        min_time = data[0]['time_in_seconds']
        max_time = data[-1]['time_in_seconds']

        # Se min_time e max_time forem iguais, ajusta o max_time para evitar erro no slider
        if min_time >= max_time:
            max_time = min_time + 1

        # Cria o slider de tempo
        selected_seconds = st.slider(
            label="Select the video/stream timestamp:",
            min_value=min_time,
            max_value=max_time,
            value=max_time
        )

        st.info(f"**Timestamp selected:** `{seconds_to_time_str(selected_seconds)}`")

        # Filtra os comentários até o tempo selecionado
        filtered_data = [c for c in data if c['time_in_seconds'] <= selected_seconds]


        # Calcula a porcentagem de negatividade
        if not filtered_data:
            negativity_percentage = 0.0
        else:
            total_comments = len(filtered_data)
            print(f"Total comments considered: {total_comments}")
            print(f"Data 1: {filtered_data[0]}")
            negative_comments = sum(1 for c in filtered_data if c.get('sentiment') == 'NEG')
            print(f"Negative comments: {negative_comments}")
            negativity_percentage = (negative_comments / total_comments) * 100 if total_comments > 0 else 0
            print(f"Negativity percentage: {negativity_percentage:.2f}%")

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

        