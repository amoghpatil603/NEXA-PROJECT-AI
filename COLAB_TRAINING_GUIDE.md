# Colab Training Guide

## Prerequisites
1. A Google Account with Google Drive access.
2. Ensure you have ample space in Drive for dataset shards and checkpoints.
3. Notebook: `notebooks/NEXA_Training_Colab.ipynb`

## Execution Steps
1. **Open Colab**: Navigate to [Google Colab](https://colab.research.google.com/) and upload `notebooks/NEXA_Training_Colab.ipynb`.
2. **Select Runtime**: Go to `Runtime > Change runtime type` and select `T4 GPU`, `L4 GPU`, or `A100 GPU` (if available).
3. **Run Setup**: Run the first cell to clone the repo and install dependencies.
4. **Mount Drive**: Run the second cell and accept the authorization prompt to link your Google Drive.
5. **Verify Data**: Ensure your dataset shards exist at `/content/drive/MyDrive/NEXA_FM/datasets/shards/`. (Run the dataset pipeline beforehand if they don't).
6. **Start Training**: Run the initialization and training cells. The trainer will automatically resume from the latest checkpoint if one exists.

## Interruption and Resuming
Google Colab may disconnect dynamically. The training loop catches `KeyboardInterrupt` and automatically saves a checkpoint. Next time you run the notebook, it automatically resumes.
