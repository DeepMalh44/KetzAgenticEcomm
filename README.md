# 🏠 KetzAgenticEcomm - AI-Powered Home Improvement Voice Assistant

> **Enterprise-grade voice commerce platform** powered by GPT-4o Realtime API, Azure AI Search, and multi-agent orchestration. Features **350+ home improvement products** with visual search capabilities.

![Architecture](docs/assets/architecture.png)

## ✨ Features

### 🎤 Voice-First Experience
- **GPT-4o Realtime API** - Native voice-to-voice with ultra-low latency
- **Built-in Barge-in** - Natural interruption handling
- **ACS Integration** - Phone (PSTN) and web voice support
- **Multi-language** - English primary, extensible

### 🖼️ Visual Search
- **Image Upload** - Find products by uploading photos
- **Azure AI Vision** - Florence model for image embeddings
- **Similarity Search** - "Find products like this image"
- **Combined Search** - Voice + image for precise results

### 🤖 Multi-Agent System
| Agent | Responsibility |
|-------|----------------|
| **Shopping Concierge** | Product discovery, recommendations, comparisons |
| **Order Processing** | New orders, tracking, modifications |
| **Returns & Support** | Returns, exchanges, complaints |
| **Product Expert** | Technical specs, compatibility, installation help |

### 🔍 Intelligent Search
- **Azure AI Search** - Full-text + vector search
- **Semantic Ranking** - Understanding intent, not just keywords
- **Image Vectors** - Find visually similar products
- **Faceted Filtering** - Category, price, brand, ratings

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CUSTOMER (Phone or Web Browser)                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
        ┌───────────────────┐           ┌───────────────────┐
        │  Azure Comm Svc   │           │   Web Frontend    │
        │  (Phone/PSTN)     │           │   (React + WS)    │
        └───────────────────┘           └───────────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                                   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    GPT-4o Realtime API                           │   │
│  │  • Native voice-to-voice                                         │   │
│  │  • Built-in barge-in                                             │   │
│  │  • Function calling for tools                                    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│  ┌─────────────────────────────────┴─────────────────────────────┐     │
│  │                    Multi-Agent Orchestration                    │     │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │     │
│  │  │  Shopping    │ │   Orders     │ │   Returns    │           │     │
│  │  │  Concierge   │ │   Agent      │ │   Agent      │           │     │
│  │  └──────────────┘ └──────────────┘ └──────────────┘           │     │
│  └───────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│  Azure AI     │         │   Cosmos DB   │         │ Blob Storage  │
│  Search       │         │  (MongoDB)    │         │  (Images)     │
│  • Text       │         │  • Products   │         │  • Product    │
│  • Vectors    │         │  • Orders     │         │    photos     │
│  • Images     │         │  • Sessions   │         │  • Uploads    │
└───────────────┘         └───────────────┘         └───────────────┘
        ▲
        │
┌───────────────┐
│ Azure AI      │
│ Vision        │
│ (Florence)    │
│ • Image       │
│   embeddings  │
└───────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Azure subscription
- Azure Developer CLI (`azd`)
- Python 3.11+
- Node.js 18+
- Docker (for local development)

### Deploy to Azure

```bash
# Clone and navigate
cd KetzAgenticEcomm

# Login to Azure
azd auth login

# Deploy everything (~20 minutes)
azd up

# Seed products with images
python scripts/seed_products.py
```

### Deploy with Terraform

```bash
# Navigate to Terraform directory
cd infra/terraform

# Initialize Terraform
terraform init

# Review the deployment plan
terraform plan

# Deploy infrastructure (~15-20 minutes)
terraform apply

# Note: After deployment, you need to:
# 1. Create GPT-4o-realtime deployment manually in Azure OpenAI Studio
# 2. Build and push container images to ACR
# 3. Seed product data
```

**Infrastructure Created by Terraform:**
- Virtual Network with Container Apps and Private Endpoint subnets
- Cosmos DB (MongoDB API) with private endpoint
- Azure AI Search
- Azure OpenAI (GPT-4o + text-embedding-3-large)
- Azure AI Vision (Florence model)
- Container Apps Environment with VNet integration
- Backend & Frontend Container Apps
- Blob Storage for product images
- Key Vault for secrets
- Application Insights for monitoring

### Local Development

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## 📁 Project Structure

```
KetzAgenticEcomm/
├── backend/                    # FastAPI + Python
│   ├── api/                    # API endpoints
│   │   ├── v1/
│   │   │   ├── realtime.py     # GPT-4o Realtime WebSocket
│   │   │   ├── search.py       # Product search endpoints
│   │   │   ├── images.py       # Image upload & search
│   │   │   └── orders.py       # Order management
│   │   └── dependencies.py
│   ├── agents/                 # Multi-agent system
│   │   ├── shopping_concierge/
│   │   ├── orders_agent/
│   │   ├── returns_agent/
│   │   └── product_expert/
│   ├── services/               # Azure integrations
│   │   ├── realtime_client.py  # GPT-4o Realtime
│   │   ├── ai_search.py        # Azure AI Search
│   │   ├── vision.py           # Azure AI Vision
│   │   ├── cosmos.py           # Cosmos DB
│   │   └── blob.py             # Blob Storage
│   ├── config/
│   │   └── settings.py
│   ├── main.py
│   └── requirements.txt
├── frontend/                   # React + Vite
│   ├── src/
│   │   ├── components/
│   │   │   ├── VoiceChat.jsx
│   │   │   ├── ImageUpload.jsx
│   │   │   ├── ProductGrid.jsx
│   │   │   └── ProductCard.jsx
│   │   ├── hooks/
│   │   │   ├── useRealtime.js
│   │   │   └── useImageSearch.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
├── infra/                      # Infrastructure as Code
│   └── terraform/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── modules/
├── scripts/                    # Utility scripts
│   ├── seed_products.py        # Seed 300+ products
│   ├── index_images.py         # Generate image embeddings
│   └── setup_search.py         # Create AI Search index
├── azure.yaml                  # Azure Developer CLI
├── docker-compose.yml
└── README.md
```

## 🛠️ Technology Stack

| Layer | Technology |
|-------|------------|
| **Voice AI** | GPT-4o Realtime API |
| **Telephony** | Azure Communication Services |
| **Image AI** | Azure AI Vision (Florence) |
| **Search** | Azure AI Search (vector + text) |
| **Database** | Azure Cosmos DB (MongoDB API) |
| **Storage** | Azure Blob Storage |
| **Backend** | FastAPI (Python 3.11) |
| **Frontend** | React 18 + Vite |
| **Hosting** | Azure Container Apps |
| **IaC** | Terraform |

## 📞 How It Works

### Voice Conversation Flow

```mermaid
sequenceDiagram
    participant C as Customer
    participant R as GPT-4o Realtime
    participant A as Agent System
    participant S as AI Search
    
    C->>R: "I need a new bathroom faucet"
    R->>A: Function call: search_products
    A->>S: Vector search: "bathroom faucet"
    S-->>A: Top 5 products
    A-->>R: Product results
    R-->>C: "I found 5 great options..."
    C->>R: [Interrupts] "Something in chrome"
    R->>A: Barge-in → Filter: chrome
    A->>S: Filtered search
    S-->>A: Chrome faucets
    R-->>C: "Here are chrome options..."
```

### Image Search Flow

```mermaid
sequenceDiagram
    participant C as Customer
    participant W as Web Frontend
    participant B as Backend
    participant V as AI Vision
    participant S as AI Search
    
    C->>W: Upload image of faucet
    W->>B: POST /api/v1/images/search
    B->>V: Generate embedding
    V-->>B: 1024-dim vector
    B->>S: Vector similarity search
    S-->>B: Similar products
    B-->>W: Product results
    W-->>C: "Found similar products..."
```

## 🔧 Configuration

### Environment Variables

```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://xxx.openai.azure.com/
AZURE_OPENAI_API_KEY=xxx
AZURE_OPENAI_REALTIME_DEPLOYMENT=gpt-4o-realtime-preview

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://xxx.search.windows.net
AZURE_SEARCH_KEY=xxx
AZURE_SEARCH_INDEX=products

# Azure AI Vision
AZURE_VISION_ENDPOINT=https://xxx.cognitiveservices.azure.com/
AZURE_VISION_KEY=xxx

# Azure Cosmos DB
AZURE_COSMOS_CONNECTION_STRING=mongodb+srv://xxx
AZURE_COSMOS_DATABASE=ketzagenticecomm

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=xxx
AZURE_STORAGE_CONTAINER=product-images

# Azure Communication Services
ACS_CONNECTION_STRING=xxx
ACS_PHONE_NUMBER=+1xxxxxxxxxx
```

## 📊 Product Categories

| Category | Subcategories | ~Products |
|----------|---------------|-----------|
| **Power Tools** | Drills, Saws, Sanders, Routers, Grinders | 50+ |
| **Hand Tools** | Hammers, Screwdrivers, Wrenches, Pliers | 40+ |
| **Building Materials** | Lumber, Drywall, Concrete, Insulation | 30+ |
| **Paint** | Interior, Exterior, Primers, Stains | 35+ |
| **Flooring** | Hardwood, Laminate, Tile, Vinyl, Carpet | 40+ |
| **Plumbing** | Faucets, Toilets, Sinks, Water Heaters | 40+ |
| **Electrical** | Lighting, Outlets, Switches, Smart Home | 35+ |
| **Kitchen & Bath** | Countertops, Cabinets, Vanities | 30+ |
| **Outdoor/Garden** | Grills, Lawn Mowers, Patio Furniture | 35+ |
| **Storage** | Shelving, Garage Storage, Tool Chests | 25+ |
| **Hardware** | Fasteners, Locks, Door Hardware | 25+ |
| **Appliances** | Refrigerators, Washers, Dryers, Ranges | 35+ |

**Total: 350+ Products** with images, ratings, and descriptions

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

Built with ❤️ using Azure AI Services
