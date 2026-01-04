# Business Merchandising Portal - Implementation Plan

## Project Overview
Build a lightweight, business-user-friendly merchandising portal on top of existing Azure AI Search infrastructure. Deploy as a new Azure Container App alongside the existing e-commerce application.

## Core Requirements
- ✅ Use existing Cosmos DB (`cosmos_db` service in `backend/services/cosmos_db.py`)
- ✅ Use existing Azure AI Search (don't create new index)
- ✅ Deploy as NEW container app: `merchandising-portal`
- ✅ Keep lightweight (minimal dependencies)
- ✅ Business-user friendly (no Azure expertise required)
- ✅ Incremental deployment: Build → Deploy → Test → Next Feature

## Architecture

```
New Container Apps:
├─ merchandising-portal-frontend (React - Business UI)
└─ merchandising-portal-backend (FastAPI - Rules Engine)

Existing Resources (Reuse):
├─ Cosmos DB (add new containers: rules, synonyms, experiments)
├─ Azure AI Search (existing index)
├─ Azure Container Registry (existing)
└─ Container Apps Environment (existing: cae-ketzagentic-vnet)
```

---

## Implementation Sequence

### FEATURE 1: Merchandising Rules Engine
**Goal**: Business users can pin/boost products for specific categories/queries without developer help.

#### Tasks:
1. **Backend Implementation**
   - Create new FastAPI app: `merchandising-backend/`
   - Implement Rules Engine:
     - `models/merchandising_rule.py` - Pydantic models for rules
     - `services/rules_engine.py` - Apply rules to search results
     - `api/rules.py` - CRUD endpoints for rules
   - Create Cosmos DB container: `merchandising_rules`
   - Rule schema:
     ```json
     {
       "id": "rule-uuid",
       "name": "Winter Kitchen Faucets Promo",
       "category": "faucets",
       "conditions": {
         "query_contains": ["kitchen"],
         "date_range": {"start": "2026-01-01", "end": "2026-03-31"}
       },
       "actions": [
         {"type": "pin", "productId": "PROD-123", "position": 1},
         {"type": "boost", "productId": "PROD-456", "multiplier": 2.0}
       ],
       "enabled": true,
       "priority": 10,
       "createdBy": "user@company.com",
       "createdAt": "2026-01-04T10:00:00Z"
     }
     ```
   - Integrate with existing search endpoint: Modify `backend/api/v1/endpoints/` to apply rules

2. **Frontend Implementation**
   - Create new React app: `merchandising-frontend/`
   - Pages:
     - `/rules` - List all rules
     - `/rules/new` - Create rule form
     - `/rules/:id/edit` - Edit rule
   - Components:
     - `RuleBuilder` - Visual rule creation (drag-and-drop UI)
     - `ProductPicker` - Search and select products to pin/boost
     - `RulePreview` - Preview search results with rule applied
   - Use lightweight UI library: Ant Design or Shadcn

3. **Deployment**
   ```bash
   # Build and push images
   docker build -t crketzagentickh7xm2.azurecr.io/merchandising-backend:v1 merchandising-backend/
   docker build -t crketzagentickh7xm2.azurecr.io/merchandising-frontend:v1 merchandising-frontend/
   docker push ...
   
   # Create new container apps
   az containerapp create \
     --name merchandising-backend \
     --resource-group rg-ketzagentic-kh7xm2 \
     --environment cae-ketzagentic-vnet \
     --image crketzagentickh7xm2.azurecr.io/merchandising-backend:v1 \
     --target-port 8001 \
     --ingress external \
     --env-vars COSMOS_CONNECTION_STRING=... SEARCH_ENDPOINT=...
   
   az containerapp create \
     --name merchandising-frontend \
     --resource-group rg-ketzagentic-kh7xm2 \
     --environment cae-ketzagentic-vnet \
     --image crketzagentickh7xm2.azurecr.io/merchandising-frontend:v1 \
     --target-port 80 \
     --ingress external \
     --env-vars VITE_BACKEND_URL=https://merchandising-backend...
   ```

4. **Testing**
   - Access portal: `https://merchandising-frontend-....azurecontainerapps.io`
   - Create test rule: Pin product for "faucet" searches
   - Verify rule appears in main e-commerce app search
   - Test rule enable/disable
   - Test rule priority (multiple rules on same query)
   - **GATE**: All tests pass before proceeding to Feature 2

---

### FEATURE 2: Synonym Management Portal
**Goal**: Business users can add/edit synonyms without emailing developers.

#### Tasks:
1. **Backend Implementation**
   - Add to `merchandising-backend/`:
     - `models/synonym.py` - Synonym models
     - `services/synonym_manager.py` - Sync with Azure AI Search
     - `api/synonyms.py` - CRUD endpoints
   - Create Cosmos DB container: `synonyms`
   - Implement Azure AI Search sync:
     ```python
     async def update_synonym_map(synonyms: List[Synonym]):
         # Convert to Solr format
         solr_format = to_solr_format(synonyms)
         # Update AI Search synonym map via SDK
         await search_client.create_or_update_synonym_map(...)
     ```

2. **Frontend Implementation**
   - Add pages to `merchandising-frontend/`:
     - `/synonyms` - List synonym groups
     - `/synonyms/new` - Add synonym group
   - Components:
     - `SynonymEditor` - Add base term + variants
     - `SynonymTester` - Test search with/without synonym
     - `BulkImporter` - CSV upload for bulk synonyms

3. **Deployment**
   - Build new versions with `v2` tag
   - Update container apps with new images
   - Test deployment

4. **Testing**
   - Add synonym: "faucet" ↔ "tap" ↔ "spigot"
   - Click "Save" and verify it updates Azure AI Search
   - Test search for "tap" returns faucet products
   - Verify synonym appears in main e-commerce app
   - **GATE**: All tests pass before proceeding to Feature 3

---

### FEATURE 3: Search Analytics Dashboard
**Goal**: Business users can see search performance metrics and understand scoring.

#### Tasks:
1. **Backend Implementation**
   - Modify existing `backend/` to log search telemetry:
     - Add Application Insights logging in search endpoints
     - Log: query, results, clicks, scores, timestamp
   - Add to `merchandising-backend/`:
     - `services/analytics.py` - Query Application Insights
     - `api/analytics.py` - Analytics endpoints
     - Endpoints:
       - `GET /analytics/top-queries` - Most searched terms
       - `GET /analytics/no-results` - Queries with zero results
       - `GET /analytics/query-detail/{query}` - Detailed scoring breakdown

2. **Frontend Implementation**
   - Add pages to `merchandising-frontend/`:
     - `/analytics` - Overview dashboard
     - `/analytics/query/{query}` - Query detail view
   - Charts:
     - Search volume trends (line chart)
     - Top queries (bar chart)
     - No-results queries (table)
     - CTR by query (table)
   - Scoring detail view:
     ```
     Query: "kitchen faucet"
     Top Result: Delta Essa Faucet
       Keyword Score: 0.45
       Vector Score: 0.78
       Semantic Score: 0.92
       Rules Applied: Winter Promo (2x boost)
       Final Score: 1.84
     ```

3. **Deployment**
   - Build and deploy v3
   - Ensure Application Insights connection

4. **Testing**
   - Perform searches in main app
   - Check analytics dashboard shows data
   - Verify scoring breakdown displays correctly
   - Test date range filters
   - **GATE**: All tests pass before proceeding to Feature 4

---

### FEATURE 4: AI-Powered Synonym Suggestions
**Goal**: System learns from user behavior and suggests synonyms automatically.

#### Tasks:
1. **Backend Implementation**
   - Add to `merchandising-backend/`:
     - `services/ai_synonym_generator.py`
     - Analyze search/click patterns from Application Insights
     - Use GPT-4 to generate synonym suggestions
     - Store suggestions in Cosmos DB container: `synonym_suggestions`
   - Add scheduled job (Azure Functions or background task):
     ```python
     async def generate_weekly_suggestions():
         # Query search logs
         patterns = analyze_click_patterns(days=30)
         # Generate suggestions with GPT-4
         suggestions = await generate_suggestions(patterns)
         # Store for review
         await save_suggestions(suggestions)
     ```
   - Add endpoints:
     - `GET /synonyms/suggestions` - Pending suggestions
     - `POST /synonyms/suggestions/{id}/approve` - Approve & apply
     - `POST /synonyms/suggestions/{id}/reject` - Reject

2. **Frontend Implementation**
   - Add page: `/synonyms/suggestions`
   - Components:
     - `SuggestionCard` - Shows AI reasoning + preview
     - `ApproveRejectButtons` - One-click approval
     - `SuggestionImpact` - Estimated impact on searches

3. **Deployment**
   - Build and deploy v4
   - Set up scheduled task for weekly suggestions

4. **Testing**
   - Manually trigger suggestion generation
   - Verify suggestions appear in portal
   - Approve a suggestion
   - Verify it updates synonym map
   - Test search with new synonym
   - **GATE**: All tests pass before proceeding to Feature 5

---

### FEATURE 5: A/B Testing Framework
**Goal**: Business users can run experiments comparing search algorithms.

#### Tasks:
1. **Backend Implementation**
   - Modify existing `backend/api/v1/endpoints/` search:
     - Add experiment assignment logic
     - Route traffic based on user_id % 100
   - Add to `merchandising-backend/`:
     - `models/experiment.py` - Experiment config
     - `services/experiment_engine.py` - Traffic splitting
     - `api/experiments.py` - CRUD endpoints
   - Create Cosmos DB container: `experiments`
   - Log experiment results to Application Insights

2. **Frontend Implementation**
   - Add pages:
     - `/experiments` - List experiments
     - `/experiments/new` - Create experiment
     - `/experiments/:id` - View results
   - Components:
     - `ExperimentBuilder` - Define variants (A/B/C)
     - `TrafficSplitter` - Set % allocation
     - `ResultsDashboard` - Compare metrics (CTR, conversion, etc.)
     - `StatisticalSignificance` - Show confidence level

3. **Deployment**
   - Build and deploy v5
   - Ensure experiment logic in main app

4. **Testing**
   - Create experiment: Hybrid vs Semantic search
   - Set 50/50 traffic split
   - Perform searches from different user sessions
   - Verify traffic splits correctly
   - View results dashboard
   - **GATE**: All tests pass before proceeding to Feature 6

---

### FEATURE 6: Enhanced Visual Search
**Goal**: Business users can manage visual search training data and test image search.

#### Tasks:
1. **Backend Implementation**
   - Enhance existing `backend/agents/image_search_agent.py`
   - Add to `merchandising-backend/`:
     - `api/visual_search.py` - Upload training images
     - Store image metadata in Cosmos DB
   - Add endpoints:
     - `POST /visual-search/upload` - Upload reference image
     - `POST /visual-search/tag-product` - Map image to product
     - `POST /visual-search/test` - Test image search

2. **Frontend Implementation**
   - Add pages:
     - `/visual-search` - Manage training images
     - `/visual-search/test` - Test upload
   - Components:
     - `ImageUploader` - Drag-and-drop upload
     - `ImageGallery` - View training images
     - `ProductMatcher` - Link image to products
     - `SearchPreview` - Test image search

3. **Deployment**
   - Build and deploy v6

4. **Testing**
   - Upload test image of a faucet
   - Tag it with product
   - Test search with similar image
   - Verify results in main app
   - **GATE**: All tests pass

---

## File Structure

```
KetzAgenticEcomm/
├── backend/                           # Existing e-commerce backend
│   ├── api/v1/endpoints/
│   │   └── [MODIFY] Add rules_engine integration
│   └── services/
│       ├── cosmos_db.py              # [REUSE] Existing
│       └── ai_search.py              # [REUSE] Existing
│
├── merchandising-backend/            # NEW - Rules engine backend
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── models/
│   │   ├── merchandising_rule.py
│   │   ├── synonym.py
│   │   └── experiment.py
│   ├── services/
│   │   ├── rules_engine.py
│   │   ├── synonym_manager.py
│   │   ├── analytics.py
│   │   ├── ai_synonym_generator.py
│   │   └── experiment_engine.py
│   └── api/
│       ├── rules.py
│       ├── synonyms.py
│       ├── analytics.py
│       ├── experiments.py
│       └── visual_search.py
│
├── merchandising-frontend/           # NEW - Business portal UI
│   ├── package.json
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── pages/
│   │   │   ├── Rules/
│   │   │   │   ├── RulesList.tsx
│   │   │   │   ├── RuleEditor.tsx
│   │   │   │   └── RulePreview.tsx
│   │   │   ├── Synonyms/
│   │   │   │   ├── SynonymsList.tsx
│   │   │   │   ├── SynonymEditor.tsx
│   │   │   │   └── Suggestions.tsx
│   │   │   ├── Analytics/
│   │   │   │   ├── Dashboard.tsx
│   │   │   │   └── QueryDetail.tsx
│   │   │   ├── Experiments/
│   │   │   │   ├── ExperimentsList.tsx
│   │   │   │   ├── ExperimentBuilder.tsx
│   │   │   │   └── Results.tsx
│   │   │   └── VisualSearch/
│   │   │       ├── ImageManager.tsx
│   │   │       └── TestSearch.tsx
│   │   └── components/
│   │       ├── RuleBuilder.tsx
│   │       ├── ProductPicker.tsx
│   │       ├── SynonymEditor.tsx
│   │       └── ExperimentDashboard.tsx
│
└── infra/
    └── [UPDATE] Add merchandising container apps
```

---

## Deployment Script Template

```powershell
# deploy-merchandising.ps1

param(
    [string]$Feature = "all",  # rules, synonyms, analytics, ai-synonyms, experiments, visual
    [string]$Version = "v1"
)

$ACR = "crketzagentickh7xm2"
$RG = "rg-ketzagentic-kh7xm2"
$ENV = "cae-ketzagentic-vnet"

# Build backend
Write-Host "Building merchandising backend..."
docker build -t "$ACR.azurecr.io/merchandising-backend:$Version" merchandising-backend/
docker push "$ACR.azurecr.io/merchandising-backend:$Version"

# Build frontend
Write-Host "Building merchandising frontend..."
docker build -t "$ACR.azurecr.io/merchandising-frontend:$Version" merchandising-frontend/
docker push "$ACR.azurecr.io/merchandising-frontend:$Version"

# Deploy/Update backend
Write-Host "Deploying merchandising backend..."
az containerapp update `
  --name merchandising-backend `
  --resource-group $RG `
  --image "$ACR.azurecr.io/merchandising-backend:$Version" `
  --revision-suffix $Version

# Deploy/Update frontend
Write-Host "Deploying merchandising frontend..."
az containerapp update `
  --name merchandising-frontend `
  --resource-group $RG `
  --image "$ACR.azurecr.io/merchandising-frontend:$Version" `
  --revision-suffix $Version

Write-Host "✅ Deployment complete!"
Write-Host "Frontend: https://merchandising-frontend.happyisland-58d32b38.eastus2.azurecontainerapps.io"
Write-Host "Backend: https://merchandising-backend.happyisland-58d32b38.eastus2.azurecontainerapps.io"
```

---

## Testing Checklist (After Each Feature)

### General Tests:
- [ ] Container apps are healthy
- [ ] Frontend loads without errors
- [ ] Backend API responds to health check
- [ ] Authentication works (if implemented)
- [ ] Cosmos DB connection successful
- [ ] Azure AI Search connection successful

### Feature-Specific Tests:
#### Feature 1 - Rules:
- [ ] Create rule via UI
- [ ] Rule saved to Cosmos DB
- [ ] Rule appears in rules list
- [ ] Enable/disable rule works
- [ ] Preview shows expected results
- [ ] Rule applies to main app search
- [ ] Multiple rules respect priority

#### Feature 2 - Synonyms:
- [ ] Add synonym via UI
- [ ] Synonym saved to Cosmos DB
- [ ] Azure AI Search synonym map updated
- [ ] Search with synonym returns expected results
- [ ] Bulk import works
- [ ] Test mode shows before/after comparison

#### Feature 3 - Analytics:
- [ ] Dashboard loads with data
- [ ] Charts render correctly
- [ ] Top queries list accurate
- [ ] No-results queries identified
- [ ] Query detail shows scoring breakdown
- [ ] Date range filter works

#### Feature 4 - AI Synonyms:
- [ ] Suggestions generated from search logs
- [ ] Suggestions appear in UI with reasoning
- [ ] Approve suggestion updates synonym map
- [ ] Reject removes suggestion
- [ ] Search validates approved synonym

#### Feature 5 - Experiments:
- [ ] Create experiment via UI
- [ ] Traffic splits correctly
- [ ] Different users see different variants
- [ ] Results dashboard shows metrics
- [ ] Statistical significance calculated
- [ ] Declare winner applies changes

#### Feature 6 - Visual Search:
- [ ] Upload image succeeds
- [ ] Image tagged to product
- [ ] Test search returns similar products
- [ ] Integration with main app works
- [ ] Image gallery displays correctly

---

## Cosmos DB Containers to Create

```python
# Add to backend/services/cosmos_db.py or merchandising-backend setup

containers = [
    "merchandising_rules",      # Feature 1
    "synonyms",                 # Feature 2
    "synonym_suggestions",      # Feature 4
    "experiments",              # Feature 5
    "experiment_results",       # Feature 5
    "visual_search_images"      # Feature 6
]

# Create containers if not exists
for container_name in containers:
    try:
        database.create_container(
            id=container_name,
            partition_key=PartitionKey(path="/id")
        )
    except exceptions.CosmosResourceExistsError:
        pass
```

---

## Environment Variables

### merchandising-backend:
```bash
COSMOS_CONNECTION_STRING=<from existing backend>
COSMOS_DATABASE_NAME=<from existing backend>
SEARCH_ENDPOINT=<from existing backend>
SEARCH_KEY=<from existing backend>
AZURE_OPENAI_ENDPOINT=<from existing backend>
AZURE_OPENAI_API_KEY=<from existing backend>
APPLICATION_INSIGHTS_CONNECTION_STRING=<existing>
MAIN_BACKEND_URL=https://backend-vnet.happyisland-58d32b38.eastus2.azurecontainerapps.io
```

### merchandising-frontend:
```bash
VITE_BACKEND_URL=https://merchandising-backend.happyisland-58d32b38.eastus2.azurecontainerapps.io
```

---

## Success Criteria

**Feature Complete When:**
- ✅ Code implemented and reviewed
- ✅ Docker images built successfully
- ✅ Deployed to Azure Container Apps
- ✅ Health checks passing
- ✅ All tests in checklist pass
- ✅ Smoke test by business user successful
- ✅ Git committed with tag: `feature-X-complete`

**Overall Project Complete When:**
- ✅ All 6 features deployed
- ✅ End-to-end workflow tested
- ✅ Documentation updated
- ✅ Business user training completed
- ✅ Performance benchmarks met
- ✅ Kent approves for production use

---

## Next Steps to Begin

1. **Create base structure**: Initialize `merchandising-backend/` and `merchandising-frontend/` folders
2. **Set up Cosmos containers**: Run script to create required containers
3. **Start Feature 1**: Begin with rules engine implementation
4. **Iterate**: After each feature completion, deploy, test, then move to next

---

## Implementation Prompt for AI Agent

**"Implement the Business Merchandising Portal following this plan:**

**Start with Feature 1 (Merchandising Rules Engine).**

**Steps:**
1. Create `merchandising-backend/` folder with FastAPI app structure
2. Create `merchandising-frontend/` folder with React + TypeScript + Vite
3. Implement rules engine backend (models, services, API endpoints)
4. Implement rules UI frontend (list, create, edit, preview)
5. Create Dockerfiles for both
6. Deploy to new Azure Container Apps in existing environment `cae-ketzagentic-vnet`
7. Run all Feature 1 tests from checklist
8. Commit with message: "Feature 1: Merchandising Rules Engine - Complete"

**Once Feature 1 tests pass, ask me to proceed to Feature 2.**

**Keep it lightweight - use minimal dependencies, reuse existing Cosmos DB and AI Search, follow existing code patterns from backend/ and frontend/.**

**After each deployment, provide:**
- URLs to access the portal
- Test results summary
- Any issues encountered
- Ready to proceed confirmation**"
