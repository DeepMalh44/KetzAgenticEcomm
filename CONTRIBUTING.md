# Contributing to KetzAgenticEcomm

Thank you for your interest in contributing to KetzAgenticEcomm! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Azure subscription
- Docker (optional, for local development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/KetzAgenticEcomm.git
   cd KetzAgenticEcomm
   ```

2. **Set up backend**
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. **Set up frontend**
   ```bash
   cd frontend
   npm install
   ```

4. **Configure environment**
   ```bash
   cp .env.sample .env
   # Edit .env with your Azure credentials
   ```

## Development Workflow

### Running Locally

**Backend:**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

### Code Style

- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Follow ESLint rules, use strict mode
- **Commits**: Use conventional commits format

### Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests to ensure nothing is broken
5. Commit your changes (`git commit -m 'feat: add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### PR Guidelines

- Provide a clear description of changes
- Reference any related issues
- Include screenshots for UI changes
- Ensure all tests pass
- Update documentation if needed

## Architecture Overview

```
backend/
├── agents/      # Multi-agent system (Shopping, Orders, Returns)
├── api/         # FastAPI endpoints
├── services/    # Azure service integrations
├── tools/       # Agent tools for function calling
└── config/      # Settings and configuration

frontend/
├── src/
│   ├── components/  # React components
│   ├── store/       # Zustand state management
│   └── App.tsx      # Main application
```

## Key Technologies

- **GPT-4o Realtime API** - Voice-to-voice AI
- **Azure AI Search** - Vector and semantic search
- **Azure AI Vision** - Image embeddings (Florence model)
- **Azure Cosmos DB** - MongoDB API database
- **FastAPI** - Python backend framework
- **React + Vite** - Frontend framework

## Questions?

Feel free to open an issue for any questions or concerns.
