
# LLM-Powered Chatbot for Managerial Sustainability Insights

## Overview

This project was published as a Short Paper at EnviroInfo 2024, Cairo, Egypt. 


The **LLM-Powered Chatbot for Managerial Sustainability Insights** provides answers to user questions based on information from the provided data sources. This README includes an overview of the application, setup instructions, usage guidelines, and technical details.

## Installation

### Prerequisites

- **Python 3.10:** The application was developed and tested with Python 3.10. Using other versions may lead to issues.
- **Ollama:** To run the Large Language Model (LLM) used in this application, Ollama is required.

### Steps to Install Ollama

- **Windows:** Download Ollama [here](https://ollama.com/download/windows).
- **Linux:** Install Ollama using the following command:

  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ```

### Running the LLM

To download and run the Llama 3 model (70B parameters), execute:

```bash
ollama run llama3:70b
```

While the application supports other LLMs, Llama 3 yielded the best results during testing.

### Setting Up the Application

1. Download or clone this repository.
2. Ensure that Python 3.10 is installed on your system.
3. Install the required dependencies by running:

   ```bash
   pip install -r requirements.txt
   ```

### Database Connection

The database connection is configured in the `config.py` file. To use SQLite (as tested), modify the following line:

```python
ENGINE = create_engine("sqlite:///chatDB.db")
```

Alternatively, you can create the database from CSV files. Adjust the `data_dir` path in `import.py` to point to the correct directory:

```python
data_dir = Path("./Data")
```

If a database already exists, new data will be added to the current database:

```python
engine = create_engine("sqlite:///chatDB.db")
```

## System Requirements

- **Python version:** 3.10
- **Tested on a Linux system** with the following specifications:
  - 96 GB RAM
  - 2x RTX 3090 Ti GPUs
  - AMD Ryzen Threadripper 3960X 24-Core Processor

Lower specifications may lead to performance issues.

## Troubleshooting

### First-Time Setup

If the application is starting for the first time and there are no pre-existing JSON files, ensure that the `CSR_Tableinfo` and `table_index-dir` directories are empty. Delete any existing data before starting the application. This step is only necessary for the initial setup or when switching the Large Language Model.

### Slow or No Responses

If the system takes too long to respond or fails to generate an answer, your system specifications may be insufficient. Consider using a smaller LLM or upgrading your hardware. Alternatively, the information requested might not be available in the dataset.

### Multiple Questions in One Request

When asking multiple questions in one query, issues may arise. To improve accuracy, ask one question at a time. Single questions provided better results during testing.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
