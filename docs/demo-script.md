# KetzAgenticEcomm Demo Script

> **Comprehensive demonstration guide for showcasing the AI-Powered Home Improvement Voice Commerce Platform to business users and customers**

---

## 📋 Pre-Demo Checklist

### Environment Setup
- [ ] Ensure the application is deployed and accessible
  - **Customer Portal**: `https://[your-frontend-url]`
  - **Merchandising Portal**: `https://[merchandising-frontend-url]`
- [ ] Verify microphone permissions are enabled in browser
- [ ] Have sample product images ready for image search demo
- [ ] Prepare test order ID for order tracking demo
- [ ] Ensure stable internet connection for real-time voice features

### Audience Preparation
- [ ] Have audience members use Chrome or Edge browsers (best WebRTC support)
- [ ] Recommend headphones for voice demo to prevent feedback

---

## 🎬 Demo Flow Overview

| Section | Duration | Key Features |
|---------|----------|--------------|
| [1. Introduction](#1-introduction) | 3 min | Platform overview, value proposition |
| [2. Voice-First Shopping](#2-voice-first-shopping-experience) | 8 min | GPT-4o Realtime, natural conversation |
| [3. Visual Search](#3-visual-search-with-ai) | 5 min | Image upload, GPT-4o Vision |
| [4. Intelligent Search](#4-intelligent-product-search) | 5 min | Semantic search, agentic search |
| [5. Cross-Sell Recommendations](#5-ai-powered-cross-sell-recommendations) | 4 min | Real-time suggestions |
| [6. Order Management](#6-order-management) | 5 min | Cart, checkout, order tracking |
| [7. Returns & Support](#7-returns--customer-support) | 4 min | Voice-initiated returns |
| [8. DIY Video Integration](#8-diy-video-recommendations) | 3 min | YouTube tutorial suggestions |
| [9. Merchandising Portal](#9-merchandising-portal-business-tools) | 8 min | Business rules, synonyms |
| [10. Wrap-Up](#10-wrap-up--qa) | 5 min | Summary, Q&A |

**Total Demo Time: ~50 minutes**

---

## 1. Introduction
**Duration: 3 minutes**

### Talking Points

> "Welcome to KetzAgenticEcomm – our AI-powered home improvement voice commerce platform. Today I'll show you how we're revolutionizing the home improvement shopping experience using cutting-edge Azure AI technologies."

**Key Value Propositions to Highlight:**
- 🎤 **Voice-First Experience**: Shop naturally using conversation, not clicks
- 🖼️ **Visual Search**: Find products by simply uploading a photo
- 🤖 **Multi-Agent AI**: Specialized AI agents for shopping, orders, and returns
- 📈 **Business Impact**: 15-25% higher conversions, 10-15% higher order values

### Screen: Main Application Interface
- Show the clean, modern interface
- Point out the voice assistant button
- Highlight the chat panel and product grid

---

## 2. Voice-First Shopping Experience
**Duration: 8 minutes**

### Demo: Natural Language Product Discovery

**Step 1: Connect to Voice Assistant**
1. Click the microphone button in the voice assistant panel
2. Wait for the green "Connected" indicator
3. Observe the real-time audio visualization

**Step 2: Product Search via Voice**

> **Say**: "Hi Ketz, I'm looking for something to help me change my HVAC filter"

*Expected Response*: Ketz will acknowledge and search for HVAC filters, air filters, and related products.

**Step 3: Follow-up Questions**

> **Say**: "What sizes do you have available?"

*Expected Response*: Ketz provides available filter sizes.

> **Say**: "Do you have any MERV 13 filters? I want better air quality."

*Expected Response*: Ketz searches specifically for MERV 13 rated filters.

**Step 4: Project Assistance**

> **Say**: "I'm planning a bathroom renovation. What do I need?"

*Expected Response*: Ketz provides comprehensive project recommendations including:
- Plumbing fixtures (toilet, faucet, showerhead)
- Flooring materials
- Paint and primer
- Electrical items (exhaust fan, GFCI outlets)
- Budget estimates for different tiers

### Talking Points

- **"Notice how Ketz understands natural language** – I didn't need to type 'air filter' exactly"
- **"Built-in barge-in support** – You can interrupt anytime, just like a real conversation"
- **"GPT-4o Realtime API** provides native voice-to-voice with ultra-low latency"

### Technical Highlights for Business Users
- WebSocket streaming for real-time responses
- Function calling enables dynamic product searches
- Multi-language support capability

---

## 3. Visual Search with AI
**Duration: 5 minutes**

### Demo: Find Products by Image

**Step 1: Open Image Search**
1. Click the camera/image icon in the interface
2. Show the drag-and-drop upload zone

**Step 2: Upload a Product Image**
1. Drag and drop an image of a home improvement product (e.g., a faucet, drill, or filter)
2. Alternatively, click to browse and select an image

**Step 3: Observe AI Analysis**
- Point out the loading indicator while GPT-4o Vision analyzes the image
- Show the search results that match the uploaded image

> "Our AI analyzed this image and identified it as a [product type]. Here are the matching products in our catalog."

**Step 4: Review Results**
- Show how the AI found visually similar products
- Demonstrate clicking on a product for details

### Talking Points

- **"Perfect for 'I saw this at a friend's house' scenarios"** – customers don't need to know product names
- **"GPT-4o Vision analyzes** color, style, brand logos, and product type"
- **"Converts image → text description → semantic search** for accurate matching"

### Sample Images to Have Ready
1. A water filter or HVAC filter
2. A power drill or hand tool
3. A bathroom faucet
4. Flooring sample (hardwood, tile, vinyl)

---

## 4. Intelligent Product Search
**Duration: 5 minutes**

### Demo: Semantic vs. Keyword Search

**Step 1: Natural Language Search via Voice**

> **Say**: "I need something to cut wood"

*Expected Result*: Shows saws, circular saws, jigsaws – understands intent, not just keywords

**Step 2: Typo Handling**

> **Say**: "Show me Dewalt cordless drils" (intentionally mispronounced)

*Expected Result*: Agentic search corrects the typo and shows DeWalt cordless drills

**Step 3: Category Filtering**

> **Say**: "Show me plumbing products under $50"

*Expected Result*: Filtered product results by category and price

### Talking Points

- **"Azure AI Search with semantic ranking** understands intent"
- **"Agentic search uses GPT-4o** to understand and correct queries"
- **"Vector embeddings (text-embedding-3-large)** enable semantic similarity"

### Search Types Comparison
| Search Type | How It Works | Best For |
|-------------|--------------|----------|
| **Semantic** | Query → Vector → Similarity | Natural language queries |
| **Agentic** | Query → GPT interprets → Vector | Typos, complex requests |
| **Image** | Image → GPT Vision → Text → Vector | Visual similarity |

---

## 5. AI-Powered Cross-Sell Recommendations
**Duration: 4 minutes**

### Demo: Contextual Product Recommendations

**Step 1: Search for a Product**

> **Say**: "I'm looking for a power drill"

**Step 2: Observe Cross-Sell Panel**
- Point out the "You May Also Like" section that appears
- Show recommendations like drill bits, safety glasses, batteries

**Step 3: Add to Cart and See Updated Recommendations**
1. Add the drill to cart
2. Observe how "Complete Your Project" recommendations appear
3. Show relevant accessories based on cart contents

### Talking Points

- **"60% acceptance rate via voice** vs. 20% for traditional banner ads"
- **"Real-time recommendations** based on search context and cart"
- **"GPT-4o generates intelligent suggestions** based on category relationships"

### Business Impact
- Increases average order value by 10-15%
- Natural, conversational upselling feels helpful, not pushy

---

## 6. Order Management
**Duration: 5 minutes**

### Demo: Full Purchase Flow

**Step 1: Add Products to Cart**

> **Say**: "Add the Honeywell air filter to my cart"

*Alternative*: Click "Add to Cart" on a product card

**Step 2: Review Cart**
1. Click the cart icon
2. Show cart contents, quantities, and pricing
3. Demonstrate quantity adjustment

**Step 3: Checkout Process**
1. Click "Checkout" button
2. Show order confirmation with order ID
3. Note the 4-digit order ID for easy reference

**Step 4: Order Tracking via Voice**

> **Say**: "What's the status of my order?"

*or if you have an order ID*:

> **Say**: "Track order 1234"

*Expected Result*: Ketz retrieves order details, items, and delivery status

### Demo: View Orders Panel
1. Click the Orders icon
2. Show the orders list with status indicators
3. Demonstrate order detail view

### Talking Points

- **"Voice-enabled ordering reduces friction"** – like Amazon's 1-Click but even simpler
- **"Cosmos DB (MongoDB API)** stores orders for quick retrieval"
- **"Order status tracking works via voice or UI"**

---

## 7. Returns & Customer Support
**Duration: 4 minutes**

### Demo: Voice-Initiated Returns

**Step 1: Initiate a Return via Voice**

> **Say**: "I need to return the air filter from order 1234"

*Expected Response*: Ketz asks for return reason and initiates the process

**Step 2: Get Return Policy Information**

> **Say**: "What's your return policy?"

*Expected Response*: Ketz explains:
- 90-day return window
- Free return shipping with prepaid label
- Conditions and exceptions

### Demo: Support Queries

> **Say**: "The drill I bought isn't working properly"

*Expected Response*: Ketz offers troubleshooting help or initiates a return/exchange

### Talking Points

- **"30-40% support ticket deflection"** – AI handles routine queries 24/7
- **"No wait times"** – immediate response improves customer satisfaction
- **"Human agents focus on complex issues"** – better resource allocation

---

## 8. DIY Video Recommendations
**Duration: 3 minutes**

### Demo: YouTube Tutorial Integration

**Step 1: Search for an Installable Product**

> **Say**: "I need help installing a garbage disposal"

**Step 2: Observe DIY Video Panel**
- Show the red/orange highlighted video recommendation panel
- Point out video thumbnails and view counts

**Step 3: Interact with Videos**
- Show how users can watch tutorials directly
- Demonstrate the dismiss feature

### Products That Trigger DIY Videos
- HVAC filters (filter replacement tutorials)
- Flooring (installation guides)
- Plumbing fixtures (faucet installation)
- Electrical items (outlet installation)
- Paint (painting techniques)

### Talking Points

- **"YouTube Data API v3 integration"** for real-time video search
- **"Prioritizes high-view, popular content"** for quality
- **"Reduces returns"** – customers install products correctly
- **"Increases purchase confidence"** – customers know they can DIY

---

## 9. Merchandising Portal (Business Tools)
**Duration: 8 minutes**

### Demo: Business Merchandising Controls

**Access the Merchandising Portal**: Navigate to the merchandising frontend URL

### Feature 1: Search Rules

**Step 1: View Rules Dashboard**
- Show existing merchandising rules
- Explain rule components: conditions and actions

**Step 2: Create a New Rule**
1. Click "Create New Rule"
2. **Set Conditions**: Query contains "water filter"
3. **Set Actions**: 
   - Action Type: "Boost Products"
   - Boost Factor: 2.0
   - Select specific products to boost
4. Save the rule

**Step 3: Test the Rule**
- Go back to customer portal
- Search for "water filter"
- Show how boosted products appear higher in results

### Feature 2: Synonym Management

**Step 1: View Synonyms Dashboard**
- Show existing synonym groups
- Examples: "faucet" ↔ "tap" ↔ "spigot"

**Step 2: Create New Synonym Group**
1. Click "Add Synonym Group"
2. Enter terms: "AC filter", "air conditioning filter", "HVAC filter"
3. Save the synonym group

**Step 3: Test Synonyms**
1. Use the Synonym Tester
2. Enter: "AC filter"
3. Show expanded terms and search results

### Feature 3: Product Selection
- Demonstrate the ProductPicker component
- Show how merchandisers can select specific products for rules

### Talking Points

- **"Non-technical merchandisers"** can control search behavior
- **"No code changes required"** – business rules applied in real-time
- **"A/B testing ready"** – test different rules and measure impact
- **"Bulk import capability"** for large catalog updates

---

## 10. Wrap-Up & Q&A
**Duration: 5 minutes**

### Summary Slide / Talking Points

**Technology Stack**
| Component | Azure Service |
|-----------|---------------|
| Voice AI | GPT-4o Realtime API |
| Vision AI | GPT-4o |
| Embeddings | text-embedding-3-large |
| Search | Azure AI Search |
| Database | Cosmos DB (MongoDB API) |
| Storage | Azure Blob Storage |
| Hosting | Azure Container Apps |
| Monitoring | Application Insights |

**Business Impact Summary**
- 📈 **15-25% conversion rate increase**
- 💰 **10-15% higher average order value**
- 📞 **30-40% support cost reduction**
- ⚡ **40% faster time-to-market** vs. competitors
- 🎯 **240x first-year ROI** for mid-market businesses

**Multi-Agent Architecture**
| Agent | Capabilities |
|-------|--------------|
| Shopping Concierge | Product discovery, recommendations, project planning |
| Orders Agent | Order creation, tracking, modifications |
| Returns Agent | Return initiation, refund processing, policy info |
| Image Search Agent | Visual similarity search using GPT-4o Vision |
| Cross-Sell Agent | Real-time complementary product suggestions |

### Common Q&A Topics

**Q: How accurate is the voice recognition?**
> "GPT-4o Realtime has industry-leading accuracy and handles accents, background noise, and natural speech patterns extremely well."

**Q: What about privacy and data security?**
> "All data is processed securely within Azure's compliance framework. Voice data is not stored after processing. Customer data in Cosmos DB is encrypted at rest."

**Q: How does pricing work?**
> "Azure's consumption-based pricing means you pay only for what you use. GPT-4o Realtime charges per token, making it cost-effective for varying workloads."

**Q: Can this integrate with existing e-commerce platforms?**
> "Yes, the backend APIs are RESTful and can integrate with Shopify, Magento, SAP, or custom platforms. We have especially strong integration capabilities with **Microsoft Dynamics 365** through native Azure connectivity, Dataverse APIs, and Power Platform connectors – making it an ideal choice for organizations already in the Microsoft ecosystem."

**Q: How long does implementation take?**
> "Typical deployment is 4-6 weeks for a basic implementation, 8-12 weeks for full customization."

---

## 📝 Demo Tips

### Do's ✅
- Speak clearly and at a natural pace for voice demos
- Pause briefly after voice commands to let the AI respond
- Have backup text commands ready in case of audio issues
- Show real product results, not pre-staged demos
- Engage the audience – let them suggest products to search

### Don'ts ❌
- Don't rush through features – let the AI demonstrate its capabilities
- Don't apologize for small latency – it's remarkably fast
- Don't skip the business impact metrics – executives care about ROI
- Don't forget to show error handling gracefully

### Handling Demo Issues

**If voice doesn't connect:**
- Check microphone permissions
- Refresh the page and try again
- Fall back to text input: "Let me show you the same feature via text..."

**If search returns no results:**
- Try a more common product category
- Demonstrate how the AI acknowledges and suggests alternatives

**If an API is slow:**
- Use the time to explain what's happening technically
- "The AI is analyzing your query and searching across 350+ products..."

---

## 🎁 Leave-Behind Materials

After the demo, provide attendees with:
1. **This demo script** (for self-guided exploration)
2. **Business case document** ([business-case.md](business-case.md))
3. **Architecture overview** ([architecture-diagram.drawio](architecture-diagram.drawio))
4. **Azure differentiation** ([azure-differentiation.md](azure-differentiation.md))
5. **Access to sandbox environment** (if available)

---

## 📞 Contact & Next Steps

For follow-up questions or to schedule a technical deep-dive:
- **Technical Contact**: [Your Name]
- **Sales Contact**: [Sales Rep Name]
- **Documentation**: [Link to docs]

**Suggested Next Steps:**
1. Schedule a technical architecture review
2. Discuss integration with existing systems
3. Define pilot scope and success metrics
4. Plan proof-of-concept timeline

---

*Document Version: 1.0*
*Last Updated: January 11, 2026*
