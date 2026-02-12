import streamlit as st
import pandas as pd
from detoxify import Detoxify
from transformers import pipeline
from tqdm import tqdm
from v2.utils.scream_index_calc import calc_scream_index
tqdm.pandas()

@st.cache_resource
def carregar_modelo():
    with st.spinner("Downloading Detoxify model... this can take a few seconds the first time."):
        return Detoxify("multilingual", device="cpu")

@st.cache_resource
def carregar_modelo_sentimentos():
    with st.spinner("Downloading sentiment model... this can take a few seconds the first time."):
        return pipeline(
            "text-classification",
            model="nlptown/bert-base-multilingual-uncased-sentiment"
        )

@st.cache_data
def classificar(texto, _modelo):
    predicoes = _modelo.predict(texto)
    return {rotulo: float(valor) for rotulo, valor in predicoes.items()}

def classificar_sentimento(texto, _modelo):
    """Classifica sentimento em POS, NEU ou NEG"""
    try:
        # Trunca a mensagem se necessário (máximo 512 caracteres)
        texto_truncado = texto[:512] if len(texto) > 512 else texto
        result = _modelo(texto_truncado)
        
        # Mapeamento do modelo multilíngue
        # Resultado: [1 star, 2 stars, 3 stars, 4 stars, 5 stars]
        # Agrupando em: NEG (1-2), NEU (3), POS (4-5)
        score_label = result[0]['label']  # '1 star', '2 stars', etc
        num_stars = int(score_label.split()[0])
        
        if num_stars <= 2:
            sentiment = 'NEG'
        elif num_stars == 3:
            sentiment = 'NEU'
        else:  # 4 ou 5
            sentiment = 'POS'
            
        sentiment_score = float(result[0]['score'])
        
        return {'sentiment': sentiment, 'sentiment_score': sentiment_score}
    except Exception as e:
        st.warning(f"Erro ao classificar sentimento: {str(e)}")
        return {'sentiment': 'NEU', 'sentiment_score': 0.0}

def classification_page():
    st.title("Toxicity Detection")
    
    if "comments_file" not in st.session_state or not st.session_state.comments_file:
        st.warning('No data uploaded, please upload some data before checking this page')
        return

    #file_name = st.selectbox('Uploaded archives', st.session_state.comments_file.keys())
    dfComentarios = pd.DataFrame(st.session_state['comments_file'])

    # Remove colunas de toxicidade se já existirem
    cols_to_drop = ['toxicity', 'severe_toxicity', 'obscene', 'identity_attack',
                'insult', 'threat', 'sexual_explicit', 'sentiment', 'sentiment_score', 'scream_index']
    dfComentarios = dfComentarios.drop(columns=[c for c in cols_to_drop if c in dfComentarios], errors="ignore")


    modelo = carregar_modelo() 
    modelo_sentimentos = carregar_modelo_sentimentos()
    if st.button("Run Classification"):
        with st.spinner("Analysing toxicity..."):
            seriePredicoes = dfComentarios["message"].progress_apply(lambda msg: classificar(msg, modelo))
            # Converte para DataFrame e concatena aos comentários originais
            dfPredicoes = pd.json_normalize(seriePredicoes)

            serieSentimentos = dfComentarios["message"].progress_apply(lambda msg: classificar_sentimento(msg, modelo_sentimentos))
            dfSentimentos = pd.json_normalize(serieSentimentos)
            
            # Concatena tudo
            dfFinal = pd.concat([dfComentarios, dfPredicoes, dfSentimentos], axis=1)

            dfFinal['scream_index'] = dfFinal['message'].apply(calc_scream_index)
            st.success("Analysis finished!")

        json_resultado = dfFinal.to_json(orient="records", force_ascii=False, indent=2)
        st.session_state['comments_file'] = dfFinal.to_dict(orient="records")
        
        st.download_button(
            label="Download result as JSON",
            data=json_resultado,
            file_name="resultado_toxicidade.json",
            mime="application/json"
        )