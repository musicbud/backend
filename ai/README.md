# AI Module for MusicBud

This folder contains the AI and recommendation system components for the MusicBud project.

## Contents
- Model training scripts (e.g., `ai_fine_tune_neo4j.py`, `ai_model_engine.py`)
- Pre-trained model and user data (pickled files)
- Validation and legacy scripts

## How to Use

1. **Pre-trained Models:**
   - The folder contains several `.pkl` files (pickled models and data) that are used for recommendations and user mapping.
   - These files are loaded automatically by the AI scripts and the main application.

2. **Running AI Scripts:**
   - You can run scripts like `ai_fine_tune_neo4j.py` or `ai_model_engine.py` to retrain or fine-tune the recommendation models.
   - Example:
     ```bash
     python ai_fine_tune_neo4j.py
     ```
   - Make sure your Python environment has all dependencies installed (see the main `requirements.txt`).

3. **Pickled Data:**
   - Files like `model.pkl`, `user_id_to_index.pkl`, etc., are generated after training and are required for the AI to function.
   - Do not delete these files unless you intend to retrain the models from scratch.

## Training Your Own Data

- **Spotify Dataset Required:**
  - To train or retrain the AI models, you need a Spotify dataset (user listening history, tracks, artists, etc.).
  - Due to its large size, the dataset is **not included** in this repository.
  - You must download the dataset yourself and place it in this `ai/` folder.
  - The Spotify dataset is available on [Kaggle](https://www.kaggle.com/) and other data platforms. Search for "Spotify Million dataset".

- **Training Steps:**
  1. Download the Spotify dataset and place it in the `ai/` folder.
  2. Run the training script (e.g., `ai_fine_tune_neo4j.py`).
  3. The script will generate new pickled model and data files.

## Notes
- Make sure to update the dataset path in the scripts if your dataset file has a different name or location.
- Some scripts may require environment variables or configuration (see `.env` or script comments).
- For best results, use a machine with sufficient RAM and CPU for model training.

---

For questions or issues, please refer to the main project README or open an issue in the repository.