# NEXA Platform Installation Guide

## Desktop / Server Installation
The NEXA platform uses a unified Docker environment for simplicity and security.

### Prerequisites
- Docker Engine & Docker Compose
- Node.js (for manual builds)
- GPU support for Docker (optional, but highly recommended for heavy LLM workloads)

### Steps
1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd NEXA-PROJECT-AI
   ```
2. **Environment Configuration**:
   ```bash
   cp .env.example .env
   # Edit .env to add your specific keys if required (e.g., ElevenLabs API)
   ```
3. **Launch the Stack**:
   ```bash
   docker-compose up -d --build
   ```
4. **Access**:
   Open a browser to `http://localhost`. 

## Mobile Installation (Flutter)
1. **Prerequisites**: Flutter SDK (>=3.2.0), Android Studio / Xcode.
2. **Setup**:
   ```bash
   cd nexa_mobile
   flutter pub get
   ```
3. **Run**:
   ```bash
   flutter run
   ```
