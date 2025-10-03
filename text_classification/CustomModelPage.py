import os
import pandas as pd
import pathlib
from datetime import datetime
import streamlit as st

from text_classification.Task import Task

"""
    Text Classification Page
    Implements the complete text classification workflow in 3 steps
"""
def custom_model_classification_page():
    # Check if there is a current task being edited
    if 'currentTaskInEdition' not in st.session_state or st.session_state.currentTaskInEdition is None:
        # Create a new task if none exists
        st.session_state.currentTaskInEdition = Task("Text Classification", "Text Classification")

    # Check if the current task is of the correct type
    if st.session_state.currentTaskInEdition.taskType != "Text Classification":
        st.session_state.currentTaskInEdition = Task("Text Classification", "Text Classification")

    # Initialize dataset state
    if 'datasetLoaded' not in st.session_state:
        st.session_state.datasetLoaded = False

    # Page tittle
    st.title("📝 Text Classification")
    st.markdown("Execute text classification using Machine Learning models in a simple and intuitive way.")
    st.markdown("---")

    # =============================================================================
    # Step 1: Dataset Selection
    # =============================================================================
    st.markdown("### Step 1: Dataset Selection")
    st.markdown("Using comments data loaded from the main page.")

    # Check if comments data is available
    if st.session_state.get('comments_file') is None:
        st.error("❌ No comments data found. Please upload a JSON file on the main page first.")
        st.info("💡 Go to 'Upload Json' page to load your comments data.")
        return

    # Load comments data into DataFrame automatically
    try:
        # Convert comments list to DataFrame
        comments_df = pd.DataFrame(st.session_state['comments_file'])
        
        # Configure dataset in current task
        st.session_state.currentTaskInEdition.inputDataset = comments_df
        st.session_state.datasetLoaded = True
        
        st.success("✅ Comments data loaded successfully!")

    except Exception as e:
        st.error(f"❌ Error loading comments data: {str(e)}")
        return

    # Preview the dataset if loaded
    if st.session_state.datasetLoaded and st.session_state.currentTaskInEdition is not None:
        st.markdown("#### Dataset Preview")

        dataset = st.session_state.currentTaskInEdition.inputDataset

        if dataset is not None:
            # General information
            column1, column2, column3 = st.columns(3)

            with column1:
                st.metric("Rows", len(dataset))
            with column2:
                st.metric("Columns", len(dataset.columns))
            with column3:
                st.metric("Memory", f"{dataset.memory_usage(deep=True).sum() / 1048576:.2f} MB")

            # Preview the data
            st.markdown("**First 10 rows:**")
            st.dataframe(dataset.head(10), use_container_width=True)

            # Suggested text columns
            textColumns = [col for col in dataset.columns if dataset[col].dtype == 'object']

            selectedTextColumn = st.selectbox(
                "Select the column containing the text for classification:",
                options=textColumns,
                help="This column will be used as input for the classification model"
            )

            # Store selected column in session state
            if 'selectedTextColumn' not in st.session_state:
                st.session_state['selectedTextColumn'] = None

            if selectedTextColumn:
                st.session_state['selectedTextColumn'] = selectedTextColumn
                st.success(f"✅ Comments data loaded successfully and target column selected: {selectedTextColumn}")

    st.markdown("---")

    # =============================================================================
    # Step 2: Model Selection
    # =============================================================================
    st.markdown("### Step 2: Model Selection")
    st.markdown("Choose a Hugging Face model for text classification.")

    # Default model
    defaultModel = "zurawski/bertweetbr-binary-classifier-toldbr"

    # Check if model is loaded
    modelLoaded = (st.session_state.currentTaskInEdition.model is not None and
                    st.session_state.currentTaskInEdition.tokenizer is not None)

    # Field with current or default value (disabled if model is loaded)
    modelId = st.text_input(
        "Enter the Hugging Face model ID:",
        value=st.session_state.currentTaskInEdition.modelID or defaultModel,
        placeholder="Ex: distilbert-base-uncased-finetuned-sst-2-english",
        help="You can find models at: https://huggingface.co/models" if not modelLoaded else "Field disabled - model loaded. Use 'Remove Model' button to edit.",
        disabled=modelLoaded
    )

    # Update model ID in task (only if not disabled)
    if not modelLoaded:
        st.session_state.currentTaskInEdition.SetModelID(modelId.strip() or None)

    # Buttons layout
    col1, col2 = st.columns([1, 1])

    with col1:
        # Button to load model (disabled if already loaded)
        load_button = st.button(
            "📥 Load Model",
            use_container_width=True,
            disabled=modelLoaded
        )

    with col2:
        # Button to remove loaded model (only visible if model is loaded)
        remove_button = st.button(
            "🗑️ Remove Model",
            use_container_width=True,
            disabled=not modelLoaded,
            help="Remove the current model from memory to load another one"
        )

    # Handle remove model button
    if remove_button and modelLoaded:
        # Clear model from memory
        st.session_state.currentTaskInEdition.model = None
        st.session_state.currentTaskInEdition.tokenizer = None
        st.session_state.currentTaskInEdition.pipeline = None
        st.session_state.currentTaskInEdition.SetModelID(None)

        st.success("🗑️ Model removed from memory successfully!")
        st.info("💡 Now you can load a new model.")
        st.rerun()

    # Handle load model button
    if load_button and not modelLoaded:
        if modelId and modelId.strip():
            # Create terminal output
            st.markdown("#### 💻 Loading Terminal")
            terminalOutput = st.empty()

            # Initial messages
            terminalMessages = [
                f"🔄 Starting model download: {modelId.strip()}",
                "⏳ Preparing environment..."
            ]

            # Callback function to update terminal
            def UpdateProgressCallback(step, message):
                # Update terminal messages
                if step == 1:
                    terminalMessages.append("🔍 Checking model availability... ✅")
                elif step == 2:
                    terminalMessages.append("📦 Starting tokenizer download...")
                elif step == 3:
                    terminalMessages.append("📦 Tokenizer downloaded successfully ✅")
                elif step == 4:
                    terminalMessages.append("🤖 Starting model download...")
                    terminalMessages.append("⏳ This may take a few minutes depending on model size...")
                elif step == 5:
                    terminalMessages.append("🤖 Model downloaded successfully ✅")
                elif step == 6:
                    terminalMessages.append(f"💻 {message}")
                elif step == 7:
                    terminalMessages.append("⚙️ Setting up classification pipeline...")
                elif step == 8:
                    terminalMessages.append("⚙️ Pipeline configured successfully ✅")
                elif step == 9:
                    terminalMessages.append("🧪 Running functionality test...")
                elif step == 10:
                    terminalMessages.append("🧪 Test completed successfully ✅")
                    terminalMessages.append("🎉 Loading finished!")

                # Update terminal display
                terminalOutput.code("\n".join(terminalMessages), language="bash")

            # Display initial terminal state
            terminalOutput.code("\n".join(terminalMessages), language="bash")

            # Try to load the model with progress callback
            success, message = st.session_state.currentTaskInEdition.LoadModel(
                progress_callback = UpdateProgressCallback
            )

            # Update terminal with final result
            if success:
                finalMessages = terminalMessages + [
                    "",
                    "=" * 50,
                    message,
                    "=" * 50
                ]
            else:
                finalMessages = terminalMessages + [
                    "",
                    "❌ ERROR DURING LOADING:",
                    message,
                    "",
                    "💡 Suggestions:",
                    "- Check if the model ID is correct",
                    "- Try a different model",
                    "- Check your internet connection",
                    "- Some models may not be available"
                ]

            terminalOutput.code("\n".join(finalMessages), language="bash")
        else:
            st.error("⚠️ Enter a valid model ID")

    # Verify if model was loaded (update status after operations)
    modelLoaded = (st.session_state.currentTaskInEdition.model is not None and
                   st.session_state.currentTaskInEdition.tokenizer is not None)

    if modelLoaded:
            # Show model information
            st.markdown("#### Model Information")

            modelInfo = st.session_state.currentTaskInEdition.GetModelInfo()

            infoColumn1, infoColumn2, infoColumn3, infoColumn4, infoColumn5 = st.columns(5)

            with infoColumn1:
                st.metric("🤖 Type", modelInfo.get("model_type", "N/A"))

            with infoColumn2:
                st.metric("📝 Vocabulary", f"{modelInfo.get('vocab_size', 0):,}")

            with infoColumn3:
                st.metric("📏 Max Length", modelInfo.get('max_length', 0))

            with infoColumn4:
                st.metric("🏷️ Classes", modelInfo.get('num_labels', 'N/A'))

            # Performance indicator
            device = modelInfo.get('device', 'CPU')
            if device == 'GPU':
                st.success("💡 Running on GPU 🚀")
            else:
                st.info("💡 Running on CPU 🐌")

            # Quick test
            st.markdown("#### 🧪 Quick Test")

            # Layout with text input and button side by side
            col_text, col_button = st.columns([4, 1])

            with col_text:
                testText = st.text_input(
                    "Enter text to test the model:",
                    placeholder="This product is very good!",
                    label_visibility="visible"
                )

            with col_button:
                st.markdown("<div style='margin-top: 29px;'></div>", unsafe_allow_html=True)  # Align button with text input
                test_button = st.button("🔍 Test", key="test_model", use_container_width=True)

            if testText and test_button:
                try:
                    with st.spinner("Processing..."):
                        results = st.session_state.currentTaskInEdition.pipeline(testText)

                    st.markdown("**Result:**")
                    for result in results[0]:
                        label = result['label']
                        score = result['score']
                        st.write(f"- **{label}**: {score:.3f} ({score*100:.1f}%)")

                except Exception as e:
                    st.error(f"❌ Test error: {str(e)}")

            st.success("✅ Model loaded successfully!")

    else:
        if modelId.strip():
            st.warning("⚠️ Load the model to continue")
        else:
            st.info("💡 Enter a model ID and click 'Load Model'")

    st.markdown("---")

    if modelLoaded:
            # Obter as labels do modelo e armazenar no session_state
            modelInfo = st.session_state.currentTaskInEdition.GetModelInfo()
            print(modelInfo)
            if 'labels' in modelInfo:
                st.session_state['model_labels'] = modelInfo['labels']
            else:
                st.session_state['model_labels'] = []

    # =============================================================================
    # Step 3: Configuration and Execution
    # =============================================================================
    st.markdown("### Step 3: Configuration and Execution")

    # Check if required components are available
    currentTask = st.session_state.currentTaskInEdition
    hasDataset = currentTask.inputDataset is not None
    hasModel = currentTask.pipeline is not None

    if not hasDataset:
        st.warning("⚠️ Dataset not loaded. Complete previous steps.")
        return

    if not hasModel:
        st.warning("⚠️ Model not loaded. Complete previous steps.")
        return

    # Check if text column was selected in Step 2
    if 'selectedTextColumn' not in st.session_state or st.session_state.selectedTextColumn is None:
        st.warning("⚠️ Text column not selected. Complete previous steps.")
        return

    selectedTextColumn = st.session_state['selectedTextColumn']

    # Set Downloads folder as fixed output directory
    outputDirectory = str(pathlib.Path.home() / "Downloads")

    # Initialize output settings in session state if not exists
    if 'outputFileName' not in st.session_state:
        st.session_state.outputFileName = ""
    if 'outputFormat' not in st.session_state:
        st.session_state.outputFormat = "csv"

    # Create two columns for file name and format
    nameCol, formatCol = st.columns([8.5, 1.5])

    with nameCol:
        # Default file name with timestamp
        defaultFileName = f"text_classification_{datetime.now().strftime('%d-%m-%Y')}"

        outputFileName = st.text_input(
            "File name (without extension):",
            value=st.session_state.outputFileName or defaultFileName,
            placeholder=defaultFileName,
            help="Enter the desired name for the classified file"
        )

        # Update output file name in session state
        st.session_state.outputFileName = outputFileName

    with formatCol:
        # File format selector
        outputFormat = st.selectbox(
            "File format:",
            options=['csv', 'xlsx', 'json', 'parquet'],
            index=['csv', 'xlsx', 'json', 'parquet'].index(st.session_state.outputFormat),
            help="Choose the export format for the classified data"
        )

        # Update output format in session state
        st.session_state.outputFormat = outputFormat

    # Show preview of full file name and location
    if outputFileName.strip():
        fullFileName = f"{outputFileName.strip()}.{outputFormat}"
        st.info(f"💡 **Final file with classification**: {fullFileName}")

    # Check if configuration is complete
    if outputFileName.strip():
        st.success("✅ Output configuration completed!")
    else:
        st.warning("⚠️ Fill in the file name to continue.")

    # Initialize session state for execution
    if 'isExecuting' not in st.session_state:
        st.session_state.isExecuting = False
    if 'executionResults' not in st.session_state:
        st.session_state.executionResults = None

    # Execution button
    st.markdown("#### Execution")

    # Get configuration from session state
    outputFileName = st.session_state.outputFileName
    outputFormat = st.session_state.outputFormat

    canExecute = (selectedTextColumn and
                  outputFileName.strip() and
                  not st.session_state.isExecuting)

    executeButton = st.button(
        "▶️ Start Classification",
        disabled=not canExecute,
        use_container_width=True,
        help="Start the classification process for the entire dataset" if canExecute else "Complete the output configuration to continue"
    )

    # Execute classification
    if executeButton and canExecute:
        st.session_state.isExecuting = True

        # Use Downloads directory
        try:
            # Create directory if it doesn't exist (though Downloads should always exist)
            if not os.path.exists(outputDirectory):
                os.makedirs(outputDirectory, exist_ok=True)

            # Create output file path with user-defined name and format
            fullFileName = f"{outputFileName.strip()}.{outputFormat}"
            outputFilePath = os.path.join(outputDirectory, fullFileName)

        except Exception as e:
            st.error(f"❌ Error configuring output directory: {str(e)}")
            st.session_state.isExecuting = False
            return

        # Create progress containers
        progressBar = st.progress(0, text="Progress: 0%")
        terminalContainer = st.empty()

        # Initialize progress tracking
        terminalMessages = [
            "🚀 Starting text classification...",
            f"📊 Dataset: {len(currentTask.inputDataset)} rows",
            f"📝 Text column: {selectedTextColumn}",
            f"🤖 Model: {currentTask.modelID}",
            f"💾 Output: {outputFilePath}",
            "",
            "⏳ Processing..."
        ]

        # Progress callback function
        def progressCallback(currentRow, totalRows, lastLabel):
            percentage = (currentRow / totalRows) * 100
            # Update only a single progress bar for the whole process
            progressBar.progress(percentage / 100, text=f"Progress: {percentage:.1f}%")
            # Update terminal messages every 50 rows or at the end
            if currentRow % 50 == 0 or currentRow == totalRows:
                terminalMessages.append(f"✅ Processed {currentRow:,}/{totalRows:,} rows ({percentage:.1f}%)")
                terminalContainer.code("\n".join(terminalMessages), language="bash")

        # Display initial progress
        terminalContainer.code("\n".join(terminalMessages), language="bash")

        # Start classification task
        currentTask.StartExecution()

        # Execute classification
        success, message = currentTask.ExecuteClassification(
            textColumn=selectedTextColumn,
            progressCallback=progressCallback
        )

        # Save results if successful
        if success and currentTask.outputDataset is not None:
            st.session_state['comments_file'] = currentTask.outputDataset.to_dict(orient='records')
            try:
                # Save in the selected format
                if outputFormat == 'csv':
                    currentTask.outputDataset.to_csv(outputFilePath, index=False)
                elif outputFormat == 'xlsx':
                    currentTask.outputDataset.to_excel(outputFilePath, index=False, engine='openpyxl')
                elif outputFormat == 'json':
                    currentTask.outputDataset.to_json(outputFilePath, orient='records', indent=2)
                elif outputFormat == 'parquet':
                    currentTask.outputDataset.to_parquet(outputFilePath, index=False)

                currentTask.SetOutputDatasetPath(outputFilePath)
                currentTask.CompleteTask(outputFilePath)

                finalMessages = terminalMessages + [
                    "",
                    "=" * 50,
                    "✅ CLASSIFICATION COMPLETED SUCCESSFULLY!",
                    f"📁 File saved at: {outputFilePath}",
                    f"📊 Total rows processed: {len(currentTask.outputDataset):,}",
                    f"📄 File format: {outputFormat.upper()}",
                    "=" * 50
                ]

                st.session_state.executionResults = {
                    'success': True,
                    'outputPath': outputFilePath,
                    'totalRows': len(currentTask.outputDataset),
                    'outputFormat': outputFormat
                }

            except Exception as saveError:
                success = False
                message = f"❌ Error saving file: {str(saveError)}"
                finalMessages = terminalMessages + [
                    "",
                    "❌ ERROR SAVING RESULT:",
                    str(saveError),
                ]

                st.session_state.executionResults = {
                    'success': False,
                    'error': str(saveError)
                }
        else:
            currentTask.FailTask(message)
            finalMessages = terminalMessages + [
                "",
                "❌ ERROR DURING CLASSIFICATION:",
                message
            ]

            st.session_state.executionResults = {
                'success': False,
                'error': message
            }

        # Update final terminal display
        terminalContainer.code("\n".join(finalMessages), language="bash")

        # Update execution state
        st.session_state.isExecuting = False

    # Show execution results
    if st.session_state.executionResults:
        results = st.session_state.executionResults

        if results['success']:
            st.markdown("---")
            # Show results summary
            st.markdown("#### Results Summary")

            if currentTask.outputDataset is not None:
                # Show sample results with all probability columns
                st.markdown("**Results Sample:**")

                # Get all probability columns (columns starting with 'prob_')
                prob_columns = [col for col in currentTask.outputDataset.columns if col.startswith('prob_')]

                # Select columns to show in sample
                display_columns = [selectedTextColumn, 'predicted_label', 'confidence_score'] + prob_columns
                available_columns = [col for col in display_columns if col in currentTask.outputDataset.columns]

                sampleResults = currentTask.outputDataset[available_columns].head(10)
                st.dataframe(sampleResults, use_container_width=True)

                # Show information about probability columns
                if prob_columns:
                    st.info(f"💡 **Probability Columns**: The model returned probabilities for {len(prob_columns)} classes: {', '.join([col.replace('prob_', '') for col in prob_columns])}")

                # Add download button for the classified dataset
                st.markdown("**Download Results:**")

                # Get file path and create download button based on format
                outputPath = results.get('outputPath', '')
                outputFormat = results.get('outputFormat', 'csv')

                if os.path.exists(outputPath):
                    # Read file content for download
                    try:
                        if outputFormat == 'csv':
                            file_data = currentTask.outputDataset.to_csv(index=False).encode('utf-8')
                            mime_type = 'text/csv'
                        elif outputFormat == 'xlsx':
                            import io
                            buffer = io.BytesIO()
                            currentTask.outputDataset.to_excel(buffer, index=False, engine='openpyxl')
                            file_data = buffer.getvalue()
                            mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                        elif outputFormat == 'json':
                            file_data = currentTask.outputDataset.to_json(orient='records', indent=2).encode('utf-8')
                            mime_type = 'application/json'
                        elif outputFormat == 'parquet':
                            import io
                            buffer = io.BytesIO()
                            currentTask.outputDataset.to_parquet(buffer, index=False)
                            file_data = buffer.getvalue()
                            mime_type = 'application/octet-stream'

                        # Extract filename from path
                        filename = os.path.basename(outputPath)

                        st.download_button(
                            label=f"📥 Download {filename}",
                            data=file_data,
                            file_name=filename,
                            mime=mime_type,
                            use_container_width=True,
                            help=f"Download the classified dataset in {outputFormat.upper()} format"
                        )

                        st.success(f"✅ File ready for download: {filename}")

                    except Exception as e:
                        st.error(f"❌ Error preparing download: {str(e)}")
                        st.info(f"💡 File saved locally at: {outputPath}")
                else:
                    st.warning(f"⚠️ Output file not found at: {outputPath}")

        else:
            st.error(f"❌ Execution error: {results['error']}")

    st.markdown("---")

    # =============================================================================
    # Final Information
    # =============================================================================
    st.markdown("### About this Task")

    infoColumn1, infoColumn2 = st.columns(2)

    with infoColumn1:
        st.markdown("""
        **Text Classification** is a fundamental Machine Learning task that allows:
    
        - 📍 **Sentiment Analysis**: Determine if text is positive, negative, or neutral
        - 🏷️ **Categorization**: Classify texts into predefined categories
        - 🔍 **Spam Detection**: Identify unwanted messages
        - 🎯 **Topic Classification**: Organize documents by subject
        """)

    with infoColumn2:
        st.markdown("""
        **Recommended Models:**
    
        - 🌟 **BERT**: Excellent for sentiment analysis
        - ⚡ **DistilBERT**: Faster version of BERT
        - 🌍 **Multilingual**: For texts in multiple languages
        - 🎯 **Fine-tuned**: Models specific to your needs
        """)
