# 🤖 Contract Intelligence System

**AI-Powered Multi-Agent Contract Analysis & Risk Assessment Platform**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![AWS](https://img.shields.io/badge/AWS-ECS-orange.svg)](https://aws.amazon.com/ecs/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 Overview

A production-ready multi-agent AI system that analyzes legal contracts, assesses risks, and provides executive-level recommendations. Built with **Crew.AI** for agent orchestration and **GPT-4** for intelligent analysis.

### ✨ Key Features

- 🤖 **4 Specialized AI Agents** working collaboratively
- ⚖️ **Legal Analysis** - Extract clauses, obligations, and terms
- 🎯 **Risk Assessment** - Score and categorize contract risks
- 📊 **Executive Reports** - Comprehensive analysis with recommendations
- 🚀 **REST API** - FastAPI with automatic documentation
- 🐳 **Docker Ready** - Containerized for easy deployment
- ☁️ **AWS Deployable** - Production-grade ECS setup
- 🔒 **Secure** - Secrets management, IAM roles

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     COORDINATOR AGENT                        │
│         (Orchestrates workflow & synthesizes reports)        │
└─────────────────────────────────────────────────────────────┘
                              │
      ┌──────────────┬────────┴────────┬───────────────┐
      │              │                 │               │
      ▼              ▼                 ▼               ▼
┌──────────┐  ┌────────────┐  ┌─────────────┐  ┌──────────┐
│  PARSER  │→ │   LEGAL    │→ │    RISK     │→ │  REPORT  │
│  AGENT   │  │   AGENT    │  │   AGENT     │  │  OUTPUT  │
└──────────┘  └────────────┘  └─────────────┘  └──────────┘
```

### Agent Responsibilities

| Agent | Role | Output |
|-------|------|--------|
| **Parser** | Extract and structure document text | Sections, metadata, confidence score |
| **Legal** | Analyze clauses, terms, obligations | Parties, key terms, legal assessment |
| **Risk** | Assess financial, legal, operational risks | Risk scores, critical issues, recommendations |
| **Coordinator** | Synthesize and generate executive reports | Final report with approval recommendation |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key
- Docker (optional, for containerization)
- AWS CLI (optional, for deployment)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/contract-intelligence-system.git
cd contract-intelligence-system

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Running Locally

```bash
# Start the API server
./start_api.sh

# Or run directly
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Visit: **http://localhost:8000**

---

## 📡 API Usage

### Upload and Analyze Contract

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@contract.pdf" \
  -F "user_instructions=Focus on liability clauses" \
  -F "priority_level=high"
```

### Get Analysis Results

```bash
curl http://localhost:8000/api/results/CONTRACT-ABC123
```

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📊 Example Output

```json
{
  "contract_id": "CONTRACT-C23CFBB1",
  "status": "completed",
  "final_report": {
    "risk_matrix": {
      "overall_risk": "Medium",
      "financial_risk": "Medium",
      "legal_risk": "Low",
      "operational_risk": "High"
    },
    "approval_recommendation": "Approve with Modifications",
    "action_items": [
      "Negotiate liability cap from $500K to $1M",
      "Clarify definition of 'Confidential Information'",
      "Add termination clause flexibility"
    ],
    "executive_summary": "This NDA presents moderate risk..."
  }
}
```

---

## 🐳 Docker Deployment

### Local Testing

```bash
# Build and test locally
./test-docker.sh

# Or use Docker Compose
docker-compose up -d
```

### Production Build

```bash
# Build production image
docker build -t contract-intelligence:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY="your-key" \
  contract-intelligence:latest
```

---

## ☁️ AWS Deployment

Complete AWS deployment with ECS, ALB, and auto-scaling.

### Quick Deploy

```bash
# 1. Create infrastructure
cd deployment/aws
chmod +x create-infrastructure.sh
./create-infrastructure.sh

# 2. Deploy application
chmod +x deploy.sh
./deploy.sh
```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

### AWS Architecture

- **ECS Fargate** - Container orchestration
- **Application Load Balancer** - Traffic distribution
- **ECR** - Container registry
- **Secrets Manager** - API key storage
- **CloudWatch** - Logging and monitoring

**Estimated Cost:** ~$76/month (can be reduced to ~$30/month)

---

## 🧪 Testing

```bash
# Test all agents
python tests/test_all_agents.py

# Test API endpoints
python tests/test_api.py

# Test coordinator only
python tests/test_coordinator.py
```

---

## 📁 Project Structure

```
contract-intelligence-system/
├── agents/                    # AI agent implementations
│   ├── coordinator_agent.py   # Orchestrates workflow
│   ├── parser_agent.py        # Document extraction
│   ├── legal_agent.py         # Legal analysis
│   └── risk_agent.py          # Risk assessment
├── api/                       # FastAPI application
│   ├── main.py                # API endpoints
│   └── models.py              # Pydantic models
├── core/                      # Core functionality
│   ├── state.py               # State management
│   ├── base_agent.py          # Base agent class
│   ├── orchestrator.py        # Workflow orchestration
│   └── config.py              # Configuration
├── deployment/                # Deployment configs
│   └── aws/                   # AWS-specific files
├── tests/                     # Test suite
├── Dockerfile                 # Container definition
├── docker-compose.yml         # Local orchestration
└── requirements.txt           # Python dependencies
```

---

## 🎯 Use Cases

### Business Applications

- **Legal Teams** - Accelerate contract review processes
- **Risk Management** - Identify potential liabilities
- **Procurement** - Assess vendor agreements
- **M&A Due Diligence** - Rapid contract analysis
- **Compliance** - Ensure regulatory adherence

### Document Types Supported

- ✅ Non-Disclosure Agreements (NDAs)
- ✅ Service Level Agreements (SLAs)
- ✅ Employment Contracts
- ✅ Vendor Agreements
- ✅ Partnership Agreements
- ✅ Lease Agreements
- ✅ Custom contracts

---

## 🔒 Security

- **API Keys** stored in AWS Secrets Manager
- **IAM Roles** for service authentication
- **Security Groups** restrict network access
- **HTTPS** support (via ALB)
- **Non-root** container user
- **Rate limiting** ready

---

## 📈 Performance

- **Analysis Time**: 40-60 seconds per contract
- **Concurrent Requests**: Scales with ECS tasks
- **Accuracy**: Based on GPT-4 capabilities
- **Throughput**: ~100 contracts/hour (2 tasks)

### Optimization Options

- Switch to GPT-3.5-turbo (faster, cheaper)
- Increase ECS task count
- Implement caching layer
- Use Fargate Spot instances

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.11 |
| **AI Framework** | Crew.AI |
| **LLM** | OpenAI GPT-4 |
| **API** | FastAPI |
| **Async** | asyncio, uvicorn |
| **Validation** | Pydantic |
| **Containerization** | Docker |
| **Orchestration** | AWS ECS Fargate |
| **Load Balancing** | AWS ALB |
| **Logging** | CloudWatch, Loguru |
| **Secrets** | AWS Secrets Manager |

---

## 📚 Documentation

- [Step 3: Agent Architecture](README_STEP3.md)
- [Step 4: API & Orchestration](README_STEP4.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**[Your Name]**

- Portfolio: [yourwebsite.com](https://yourwebsite.com)
- LinkedIn: [linkedin.com/in/yourprofile](https://linkedin.com/in/yourprofile)
- GitHub: [@yourusername](https://github.com/yourusername)

---

## 🙏 Acknowledgments

- **Crew.AI** - Multi-agent orchestration framework
- **OpenAI** - GPT-4 language model
- **FastAPI** - Modern Python web framework
- **AWS** - Cloud infrastructure

---

## 📊 Project Stats

- **Total Lines of Code**: ~3,500+
- **Python Files**: 15+
- **Test Coverage**: Comprehensive
- **Documentation**: Complete
- **Production Ready**: ✅

---

## 🎓 Skills Demonstrated

✅ Multi-Agent System Design  
✅ AI/ML Integration (LLMs)  
✅ API Development (FastAPI)  
✅ Containerization (Docker)  
✅ Cloud Deployment (AWS)  
✅ Infrastructure as Code  
✅ Async Python Programming  
✅ State Management  
✅ Error Handling & Logging  
✅ Security Best Practices  
✅ Testing & Documentation  

---

## 🌟 Show Your Support

Give a ⭐️ if this project helped you learn or build something amazing!

---

**Built with ❤️ for demonstrating real-world AI engineering skills**