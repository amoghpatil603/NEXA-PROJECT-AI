# First Training Guide - NEXA Foundation Model

## Introduction
This guide details the steps required to execute the first real training run of the NEXA Foundation Model using the `NEXA Tiny` configuration.

## Pre-requisites
1. A valid PyTorch environment with CUDA or MPS support (optional but recommended for speed).
2. Proper datasets downloaded via the Dataset Manager.

## Step 1: Download Datasets
Ensure your environment has the datasets prepared:
```bash
python -m backend.models.nexa_fm.dataset_manager.downloader
```

## Step 2: Validate the Pipeline (Dry-Run)
Run the validation script to ensure all integrations are functional without actually updating weights:
```bash
python run_dry_run_validation.py
```
*Expected Output: `🟢 READY FOR TRAINING`*

## Step 3: Initiate Training
Update the Google Colab Notebook (`notebooks/NEXA_Training_Colab.ipynb`) to instantiate `NexaFMConfig.tiny()` and begin the full training loop.

## Post-Training Verification
Check the `./test_checkpoints` and `./test_logs` directories to ensure artifacts are being successfully created.
