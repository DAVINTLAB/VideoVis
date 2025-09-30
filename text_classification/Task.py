# =============================================================================
# IMPORTS
# =============================================================================
import streamlit as st
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
import uuid
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch

# =============================================================================
# Task Status
# =============================================================================
class TaskStatus(Enum):
    """Possible task states"""

    PREPARATION = "preparation"
    EXECUTION = "execution"
    FINISHED = "finished"
    ERROR = "error"

# =============================================================================
# Task
# =============================================================================
class Task:
    """Class that represents an ML task"""

    def __init__(self, taskName: str = None, taskType: str = None):
        self.id = str(uuid.uuid4())
        self.status = TaskStatus.PREPARATION

        self.taskName = taskName
        self.taskType = taskType

        self.inputDatasetPath = None
        self.outputDatasetPath = None
        self.inputDataset : pd.DataFrame = None
        self.outputDataset : pd.DataFrame = None

        self.modelID: str = None
        self.model = None
        self.tokenizer = None
        self.pipeline = None

        # self.environment = None
        self.targetColumn: str = None

        self.startedAt: Optional[datetime] = None
        self.finishedAt: Optional[datetime] = None
        self.errorMessage: Optional[str] = None
        self.progress: int = 0  # Progresso de 0 a 100
        self.metadata: Dict[str, Any] = {}  # Dados adicionais específicos da task

        self.firstStep: bool = False
        self.secondStep: bool = False
        self.thirdStep: bool = False
        self.fourthStep: bool = False

    # =============================================================================
    # First Step: Task Creation
    # =============================================================================

    def SetTaskName(self, name: str):
        """Define o nome da task"""

        self.taskName = name

    def SetTaskType(self, taskType: str):
        """Define o tipo da task"""

        self.taskType = taskType

    # =============================================================================
    # Second Step: Dataset Selection
    # =============================================================================
    def SetInputDatasetPath(self, path: str):
        """Define o caminho do dataset de entrada para a task"""

        self.inputDatasetPath = path

    def LoadInputDataset(self):
        """Carrega o dataset de entrada para a task"""

        if self.inputDatasetPath is None:
            raise ValueError("Dataset path not set")

        try:
            if self.inputDatasetPath.endswith('.csv'):
                self.inputDataset = pd.read_csv(self.inputDatasetPath)
            elif self.inputDatasetPath.endswith('.json'):
                self.inputDataset = pd.read_json(self.inputDatasetPath)
            elif self.inputDatasetPath.endswith(('.xlsx', '.xls')):
                self.inputDataset = pd.read_excel(self.inputDatasetPath)
            else:
                raise ValueError("Unsupported file format")

            self.firstStep = True
        except Exception as e:
            raise ValueError(f"Error loading dataset: {str(e)}")

    # =============================================================================
    # Third Step: Model Selection
    # =============================================================================
    def SetModelID(self, modelID: str):
        """Define o ID do modelo para a task"""
        if modelID is not None and isinstance(modelID, str):
            self.modelID = modelID.strip()
        else:
            self.modelID = None

    def LoadModel(self, progress_callback=None) -> Tuple[bool, str]:
        """
        Carrega o modelo do Hugging Face para a task
        Retorna: (sucesso: bool, mensagem: str)
        progress_callback: função para atualizar progresso (opcional)
        """
        # Validação rigorosa do modelID
        if not self.modelID or not isinstance(self.modelID, str) or not self.modelID.strip():
            return False, "❌ Model ID não definido ou inválido"

        # Garantir que o modelID é uma string limpa
        model_id_clean = str(self.modelID).strip()

        if not model_id_clean:
            return False, "❌ Model ID está vazio"

        try:
            # Função para atualizar progresso
            def update_progress(step, message):
                if progress_callback:
                    progress_callback(step, message)

            # Verificar se CUDA está disponível
            device = 0 if torch.cuda.is_available() else -1
            device_name = "GPU (CUDA)" if device == 0 else "CPU"

            # Limpar modelo anterior se existir
            self.model = None
            self.tokenizer = None
            self.pipeline = None

            update_progress(1, "🔍 Checking model availability...")

            # Load tokenizer with error handling
            update_progress(2, "📦 Baixando tokenizer...")
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(
                    model_id_clean,
                    use_fast=True,
                    trust_remote_code=True
                )
                update_progress(3, "📦 Tokenizer downloaded successfully")
            except Exception as tokenizer_error:
                # Tentar sem use_fast se falhar
                update_progress(3, "📦 Tentando tokenizer alternativo...")
                try:
                    self.tokenizer = AutoTokenizer.from_pretrained(
                        model_id_clean,
                        use_fast=False,
                        trust_remote_code=True
                    )
                    update_progress(3, "📦 Alternative tokenizer downloaded successfully")
                except Exception as tokenizer_error2:
                    return False, f"❌ Error loading tokenizer: {str(tokenizer_error2)}"

            # Verificar se tokenizer foi carregado corretamente
            if self.tokenizer is None:
                return False, "❌ Tokenizer não foi carregado corretamente"

            # Load model
            update_progress(4, "🤖 Baixando modelo (pode demorar alguns minutos)...")
            try:
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    model_id_clean,
                    trust_remote_code=True
                )
                update_progress(5, "🤖 Model downloaded successfully")
            except Exception as model_error:
                return False, f"❌ Error loading model: {str(model_error)}"

            # Verificar se modelo foi carregado corretamente
            if self.model is None:
                return False, "❌ Modelo não foi carregado corretamente"

            # Mover modelo para o dispositivo correto
            update_progress(6, f"💻 Setting up model for {device_name}...")
            if torch.cuda.is_available() and device == 0:
                try:
                    self.model = self.model.to('cuda')
                    update_progress(6, "💻 Model configured for GPU")
                except Exception as cuda_error:
                    # Se falhar com CUDA, usar CPU
                    device = -1
                    device_name = "CPU (CUDA falhou)"
                    self.model = self.model.to('cpu')
                    update_progress(6, "💻 Model configured for CPU (GPU failed)")

            # Criar pipeline para classificação
            update_progress(7, "⚙️ Setting up pipeline...")
            try:
                self.pipeline = pipeline(
                    "text-classification",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    device=device,
                    return_all_scores=True
                )
                update_progress(8, "⚙️ Pipeline configured successfully")
            except Exception as pipeline_error:
                return False, f"❌ Error creating pipeline: {str(pipeline_error)}"

            # Basic pipeline test
            update_progress(9, "🧪 Testing functionality...")
            try:
                test_result = self.pipeline("test")
                if not test_result:
                    return False, "❌ Pipeline not working correctly"
                update_progress(10, "🧪 Test completed successfully")
            except Exception as test_error:
                return False, f"❌ Error in pipeline test: {str(test_error)}"

            self.secondStep = True

            return True, f"✅ Model '{model_id_clean}' loaded successfully on {device_name}"

        except Exception as e:
            # Clear states in case of error
            self.model = None
            self.tokenizer = None
            self.pipeline = None
            error_msg = f"❌ General error loading model '{model_id_clean}': {str(e)}"
            return False, error_msg

    def GetModelInfo(self) -> Dict[str, Any]:
        """Retorna informações sobre o modelo carregado"""
        if not self.model or not self.tokenizer:
            return {}

        info = {
            "model_id": self.modelID,
            "model_type": self.model.config.model_type if hasattr(self.model, 'config') else "Unknown",
            "vocab_size": self.tokenizer.vocab_size,
            "max_length": self.tokenizer.model_max_length,
            "num_labels": self.model.config.num_labels if hasattr(self.model, 'config') else "Unknown",
            "device": "GPU" if torch.cuda.is_available() and next(self.model.parameters()).is_cuda else "CPU"
        }

        return info

    # =============================================================================
    # Fourth Step: Target Column Selection and Execution
    # =============================================================================
    def SetOutputDatasetPath(self, path: str):
        """Define o caminho do dataset de saída para a task"""

        self.outputDatasetPath = path

    def SetTargetColumn(self, targetColumn: str):
        """Define a coluna alvo para a task"""

        self.targetColumn = targetColumn

    def ExecuteClassification(self, textColumn: str, progressCallback=None) -> Tuple[bool, str]:
        """
        Execute text classification on the dataset
        Args:
            textColumn: Column name containing the text to classify
            progressCallback: Optional callback function for progress updates
        Returns:
            (success: bool, message: str)
        """
        if not self.inputDataset is not None:
            return False, "❌ No input dataset loaded"

        if not self.pipeline:
            return False, "❌ No model pipeline loaded"

        if textColumn not in self.inputDataset.columns:
            return False, f"❌ Column '{textColumn}' not found in dataset"

        try:
            # Create output dataset as copy of input
            self.outputDataset = self.inputDataset.copy()
            totalRows = len(self.inputDataset)

            # Get available labels by testing with sample text
            sample_text = "test sample"
            sample_results = self.pipeline(sample_text)
            available_labels = [result['label'] for result in sample_results[0]]

            # Initialize classification result columns
            self.outputDataset['predicted_label'] = ''
            self.outputDataset['confidence_score'] = 0.0

            # Create columns for each label probability
            for label in available_labels:
                self.outputDataset[f'prob_{label.lower()}'] = 0.0

            # Process each row
            for index, row in self.inputDataset.iterrows():
                try:
                    # Get text from specified column
                    text = str(row[textColumn])

                    # Skip empty texts
                    if not text.strip():
                        self.outputDataset.at[index, 'predicted_label'] = 'EMPTY_TEXT'
                        self.outputDataset.at[index, 'confidence_score'] = 0.0
                        # Set all probabilities to 0 for empty text
                        for label in available_labels:
                            self.outputDataset.at[index, f'prob_{label.lower()}'] = 0.0
                        continue

                    # Classify text
                    results = self.pipeline(text)

                    # Get best prediction
                    bestPrediction = max(results[0], key=lambda x: x['score'])

                    # Store main prediction results
                    self.outputDataset.at[index, 'predicted_label'] = bestPrediction['label']
                    self.outputDataset.at[index, 'confidence_score'] = bestPrediction['score']

                    # Store all probabilities
                    for result in results[0]:
                        label = result['label']
                        score = result['score']
                        self.outputDataset.at[index, f'prob_{label.lower()}'] = score

                    # Update progress
                    if progressCallback:
                        progressCallback(index + 1, totalRows, bestPrediction['label'])

                except Exception as e:
                    # Handle individual row errors
                    self.outputDataset.at[index, 'predicted_label'] = f'ERROR: {e}'
                    self.outputDataset.at[index, 'confidence_score'] = 0.0

                    # Set all probabilities to 0 for error cases
                    for label in available_labels:
                        self.outputDataset.at[index, f'prob_{label.lower()}'] = 0.0

                    if progressCallback:
                        progressCallback(index + 1, totalRows, f"ERROR: {str(e)[:50]}")

            return True, f"✅ Classification completed successfully! Processed {totalRows} rows with {len(available_labels)} labels."

        except Exception as e:
            return False, f"❌ Error during classification: {str(e)}"

    # def SetEnvironment(self, environment: ExecutionEnvironment):
    #     """Define o ambiente de execução para a task"""

    #     self.environment = environment

    def StartExecution(self):
        """Inicia a execução da task"""

        self.status = TaskStatus.EXECUTION
        self.startedAt = datetime.now()
        self.progress = 0

    def UpdateProgress(self, progress: int):
        """Atualiza o progresso da task (0-100)"""

        self.progress = max(0, min(100, progress))

    def GetDuration(self) -> Optional[str]:
        """Retorna a duração da execução formatada"""

        if self.startedAt and self.finishedAt:
            duration = self.finishedAt - self.startedAt
            totalSeconds = int(duration.total_seconds())
            minutes, seconds = divmod(totalSeconds, 60)
            return f"{minutes}m {seconds}s"
        elif self.startedAt:
            duration = datetime.now() - self.startedAt
            totalSeconds = int(duration.total_seconds())
            minutes, seconds = divmod(totalSeconds, 60)
            return f"{minutes}m {seconds}s (em execução)"
        return None

    def GetStatusIcon(self) -> str:
        """Retorna o ícone correspondente ao status"""

        icons = {
            TaskStatus.PREPARATION: "⚙️",
            TaskStatus.EXECUTION: "🔄",
            TaskStatus.FINISHED: "✅",
            TaskStatus.ERROR: "❌"
        }
        return icons.get(self.status, "❓")

    def GetStatusColor(self) -> str:
        """Retorna a cor correspondente ao status"""

        colors = {
            TaskStatus.PREPARATION: "#ffc107",  # Amarelo
            TaskStatus.EXECUTION: "#007bff",    # Azul
            TaskStatus.FINISHED: "#28a745",  # Verde
            TaskStatus.ERROR: "#dc3545"         # Vermelho
        }
        return colors.get(self.status, "#6c757d")

    def CompleteTask(self, outputDataset: str):
        """Completa a task com sucesso"""

        self.status = TaskStatus.FINISHED
        self.finishedAt = datetime.now()
        self.outputDatasetPath = outputDataset
        self.progress = 100
        self.thirdStep = True

    def SaveOutputDataset(self, outputPath: str):
        """Salva o dataset de saída da task"""

        if self.outputDataset is not None:
            self.outputDataset.to_csv(outputPath, index=False)

    def FailTask(self, errorMessage: str):
        """Marca a task como falha"""

        self.status = TaskStatus.ERROR
        self.finishedAt = datetime.now()
        self.errorMessage = errorMessage
        self.thirdStep = True

    # =============================================================================
    # Fifth Step: Visualization Generation
    # =============================================================================

    def GenerateVisualization(self):
        """Gera a visualização da task"""

        if self.outputDataset is not None:
            # Lógica para gerar visualização a partir do dataset
            pass
    # =============================================================================
    # Fifth Step: Visualization Generation
    # =============================================================================

    def GenerateVisualization(self):
        """Gera a visualização da task"""

        if self.outputDataset is not None:
            # Lógica para gerar visualização a partir do dataset
            pass


