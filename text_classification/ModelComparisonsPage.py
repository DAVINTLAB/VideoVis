import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go

def model_comparisons_page():
    st.title("Model Comparisons")
    st.markdown("Compare results between Detoxify (pre-analyzed) and Custom Model classifications")
    st.markdown("---")

    if 'comments_file' not in st.session_state or st.session_state['comments_file'] is None:
        st.error("❌ No comments data found. Please upload JSON data first.")
        return

    comments_list = st.session_state['comments_file']
    
    if 'selectedTextColumn' not in st.session_state or st.session_state['selectedTextColumn'] is None:
        st.warning("⚠️ No text column selected. Please go to Custom Model page and select a text column first.")
        return
    
    selected_column = st.session_state['selectedTextColumn']
    
    if 'currentTaskInEdition' not in st.session_state or st.session_state['currentTaskInEdition'] is None:
        st.warning("⚠️ No custom model results found. Please run classification on Custom Model page first.")
        return
    
    current_task = st.session_state['currentTaskInEdition']
    
    if current_task.outputDataset is None:
        st.warning("⚠️ Custom model has not been executed yet. Please run classification on Custom Model page first.")
        return

    st.success(f"✅ Comparing results using column: **{selected_column}**")
    
    detoxify_df = pd.DataFrame(comments_list)
    custom_df = current_task.outputDataset
    
    st.markdown("### 📊 Data Overview")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Comments", len(detoxify_df))
    
    with col2:

        detoxify_toxic = 0
        for c in comments_list:
            try:
                toxicity_value = float(c.get('toxicity', 0))
                if toxicity_value >= 0.5:
                    detoxify_toxic += 1
            except (ValueError, TypeError):
                continue
        st.metric("Detoxify Toxic (≥0.5)", detoxify_toxic)
    
    with col3:
  
        if 'predicted_label' in custom_df.columns:
            custom_negative = len(custom_df[custom_df['predicted_label'].str.upper().isin(['NEGATIVE', 'NEG', 'TOXIC'])])
            st.metric("Custom Model Negative", custom_negative)
        else:
            st.metric("Custom Model Results", "N/A")
    

    st.markdown("### Comparison Filters")
    

    toxicity_threshold = st.slider(
        "Detoxify Toxicity Threshold:",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.1,
        help="Filter comments by Detoxify toxicity score"
    )
    
    
    detoxify_filtered = []
    for c in comments_list:
        try:
            toxicity_value = float(c.get('toxicity', 0))
            if toxicity_value >= toxicity_threshold:
                detoxify_filtered.append(c)
        except (ValueError, TypeError):
            continue  
    
    st.info(f" Found **{len(detoxify_filtered)}** comments with Detoxify toxicity ≥ {toxicity_threshold}")

    # # === SEÇÃO 3: COMPARAÇÃO LADO A LADO ===
    # st.markdown("### 🔄 Side-by-Side Comparison")
    
    # if detoxify_filtered:
    #     # Mostrar primeiros N comentários para comparação
    #     num_to_show = st.number_input(
    #         "Number of comments to compare:",
    #         min_value=1,
    #         max_value=min(50, len(detoxify_filtered)),
    #         value=min(10, len(detoxify_filtered))
    #     )
        
        # st.markdown(f"**Showing first {num_to_show} toxic comments:**")
        
        # for i, comment in enumerate(detoxify_filtered[:num_to_show]):
        #     # Função auxiliar para obter valores seguros
        #     def get_safe_value(data, key, default='N/A'):
        #         try:
        #             value = data.get(key, default)
        #             if isinstance(value, (int, float)):
        #                 return f"{value:.3f}"
        #             return str(value)
        #         except:
        #             return default
            
        #     author = comment.get('author', 'Unknown')
        #     toxicity_score = get_safe_value(comment, 'toxicity', '0.000')
            
        #     with st.expander(f"Comment {i+1} - Author: {author} | Detoxify Score: {toxicity_score}"):
                
        #         # Texto original - usando get() para evitar KeyError
        #         text_content = comment.get(selected_column, comment.get('message', 'Text not found'))
        #         st.markdown(f"**Text ({selected_column}):** {text_content}")
                
        #         # Resultados do Detoxify
        #         col_detox, col_custom = st.columns(2)
                
        #         with col_detox:
        #             st.markdown("**🔬 Detoxify Results:**")
                    
        #             # Função auxiliar para formatar valores numéricos
        #             def format_score(value):
        #                 if value is None or value == 'N/A':
        #                     return 'N/A'
        #                 try:
        #                     return f"{float(value):.3f}"
        #                 except (ValueError, TypeError):
        #                     return str(value)
                    
        #             st.write(f"• Toxicity: {format_score(comment.get('toxicity'))}")
        #             st.write(f"• Sentiment: {comment.get('sentiment', 'N/A')}")
        #             st.write(f"• Severe Toxicity: {format_score(comment.get('severe_toxicity'))}")
        #             st.write(f"• Obscene: {format_score(comment.get('obscene'))}")
        #             st.write(f"• Insult: {format_score(comment.get('insult'))}")
                    
        #             # Campos opcionais
        #             if 'threat' in comment:
        #                 st.write(f"• Threat: {format_score(comment['threat'])}")
        #             if 'identity_attack' in comment:
        #                 st.write(f"• Identity Attack: {format_score(comment['identity_attack'])}")
        #             if 'sexual_explicit' in comment:
        #                 st.write(f"• Sexual Explicit: {format_score(comment['sexual_explicit'])}")
                
        #         with col_custom:
        #             st.markdown("**🤖 Custom Model Results:**")
                    
        #             # Encontrar o resultado correspondente no modelo customizado
        #             # Assumindo que os dados estão na mesma ordem ou usando algum identificador
        #             if i < len(custom_df) and selected_column in custom_df.columns:
        #                 custom_row = custom_df.iloc[i]
                        
        #                 if 'predicted_label' in custom_df.columns:
        #                     st.write(f"• Predicted Label: {custom_row['predicted_label']}")
                        
        #                 if 'confidence_score' in custom_df.columns:
        #                     st.write(f"• Confidence: {custom_row['confidence_score']:.3f}")
                        
        #                 # Mostrar probabilidades se disponíveis
        #                 prob_columns = [col for col in custom_df.columns if col.startswith('prob_')]
        #                 if prob_columns:
        #                     st.write("• Probabilities:")
        #                     for prob_col in prob_columns:
        #                         label = prob_col.replace('prob_', '')
        #                         st.write(f"  - {label}: {custom_row[prob_col]:.3f}")
        #             else:
        #                 st.write("No corresponding result found")
                
        #         # Comparação direta
        #         if i < len(custom_df) and 'predicted_label' in custom_df.columns:
        #             custom_result = custom_df.iloc[i]['predicted_label'].upper()
                    
        #             # Usar função segura para obter toxicity
        #             try:
        #                 toxicity_value = float(comment.get('toxicity', 0))
        #                 detoxify_result = "TOXIC" if toxicity_value >= toxicity_threshold else "NON-TOXIC"
        #             except (ValueError, TypeError):
        #                 detoxify_result = "UNKNOWN"
                    
        #             if detoxify_result != "UNKNOWN":
        #                 if (custom_result in ['NEGATIVE', 'TOXIC'] and detoxify_result == "TOXIC") or \
        #                    (custom_result in ['POSITIVE', 'NON-TOXIC'] and detoxify_result == "NON-TOXIC"):
        #                     st.success("✅ Models agree on classification")
        #                 else:
        #                     st.error("❌ Models disagree on classification")
        #             else:
        #                 st.warning("⚠️ Cannot compare - invalid toxicity data")
    
    st.markdown("### 📈 Agreement Statistics")
    
    json_data = []
    agreements = 0
    total_compared = 0
    
    if 'predicted_label' in custom_df.columns and len(custom_df) > 0:
        agreements = 0
        total_compared = min(len(detoxify_filtered), len(custom_df))
        
        for i in range(total_compared):
            if i < len(custom_df) and i < len(detoxify_filtered):
                custom_result = custom_df.iloc[i]['predicted_label'].upper()
                comment = detoxify_filtered[i]
                custom_row = custom_df.iloc[i]
                
                try:
                    toxicity_value = float(comment.get('toxicity', 0))
                    detoxify_result = "TOXIC" if toxicity_value >= toxicity_threshold else "NON-TOXIC"
                except (ValueError, TypeError):
                    detoxify_result = "UNKNOWN"
                    continue

                models_agree = False
                if detoxify_result != "UNKNOWN":
                    if (custom_result in ['NEGATIVE', 'TOXIC'] and detoxify_result == "TOXIC") or \
                    (custom_result in ['POSITIVE', 'NON-TOXIC'] and detoxify_result == "NON-TOXIC"):
                        models_agree = True
                        agreements += 1

                    
                    comment_dict = {
                        "id": comment.get('id', f'comment_{i}'),
                        "author": comment.get('author', 'Unknown'),
                        "message": comment.get('message', ''),
                        
                        "detoxify_toxicity": comment.get('toxicity', 0),
                        "detoxify_sentiment": comment.get('sentiment', 'N/A'),
                        
                        "custom_predicted_label": custom_row['predicted_label'],
                        
                        "detoxify_result": detoxify_result,
                        "custom_result": custom_result,
                        "models_agree": (models_agree),
                    }
                    
                
                
                    json_data.append(comment_dict)
        if json_data:         
            json_string = json.dumps(json_data, indent=2, ensure_ascii=False)
            st.download_button(
                label = "Download Toxic Comments JSON",
                data = json_string,
                file_name = f"toxic_comments_{len(json_data)}_items.json",
                mime = "application/json"
            )
        
        if total_compared > 0:  
            st.markdown("### 📊 Comparison Charts")
        
            disagreements = total_compared - agreements
            
            agreement_labels = ['Models Agree', 'Models Disagree'] 
            agreement_values = [agreements, disagreements]
            agreement_colors = ['#2ecc71', '#e74c3c']
            
            fig_agreement = go.Figure(data=[go.Pie(
                labels=agreement_labels,
                values=agreement_values,
                hole=0.4,
                marker_colors=agreement_colors,
                textinfo='label+percent+value',
                textfont_size=12,
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            )])
            
            fig_agreement.update_layout(
                title={
                    'text': 'Model Agreement vs Disagreement',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 16}
                },
                font=dict(size=14),
                showlegend=True,
                height=400,
                margin=dict(t=60, b=20, l=20, r=20)
            )
            
            st.plotly_chart(fig_agreement, use_container_width=True)
            
            
            agreement_rate = (agreements / total_compared) * 100
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Compared", total_compared)
            
            with col2:
                st.metric("Agreements", agreements)
            
            with col3:
                st.metric("Agreement Rate", f"{agreement_rate:.1f}%")
            
            if agreement_rate >= 80:
                st.success(f"High agreement rate: {agreement_rate:.1f}%")
            elif agreement_rate >= 60:
                st.warning(f"Moderate agreement rate: {agreement_rate:.1f}%")
            else:
                st.error(f"Low agreement rate: {agreement_rate:.1f}%")
                
            
                
    
    
    st.markdown("---")
    st.markdown("### 💡 Tips for Comparison")
    st.info("""
    • **High Agreement**: Models are consistent in their classifications
    • **Low Agreement**: Consider reviewing model parameters or training data
    • **Detoxify**: Specialized for toxicity detection with multiple categories
    • **Custom Model**: General-purpose sentiment/classification model
    """)