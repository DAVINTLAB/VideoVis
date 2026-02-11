# VideoVis
## ⚙️ Installation
##### Clone the repository
```bash
git clone https://github.com/DAVINTLAB/VideoVis.git
cd VideoVis
```

##### Setup venv (recommended):
```bash
python3 -m venv ambiente_youtube
```
If using windows:
```bash
.\ambiente_youtube\Scripts\activate
```

If using linux:
```bash
source ambiente_youtube/bin/activate
```

##### Install dependencies
```bash
pip install -r requirements.txt
```

##### (Option 1) To collect comments the main.py file and insert your API key and Video ID
```bash
7 - API_KEY = ''
8 - VIDEO_ID = ''
```

#### 🚀Run Option 1
```bash
python3 v1/main.py
```

#### (Option 2) To show the dashboard run the following
```bash
streamlit run app.py
```

#### Tips:
1. Ensure you are using the venv when trying to run, or else it will fail
2. Remember to install the requirements in the venv
3. If the commands are not working try using only **python** as prefix instead of **python3** 

