---
title: "Event 1 - FCAJ Meetup #1"
date: "2026-06-06"
weight: 1
chapter: false
pre: "<b> 4.1. </b>"
---

#### Event 1 – FCAJ Meetup #1 (June 6, 2026)

{{% notice info %}}
📅 **Date:** June 6, 2026 | 📍 **Format:** In-person | 🏢 **Organizer:** First Cloud AI Journey (FCAJ)
{{% /notice %}}

---

#### Summary Report: "FCAJ Meetup #1 – Kickoff & Community Talks"

##### Event Objectives
- Open the First Cloud AI Journey program with community introductions and orientation.
- Share practical knowledge on AWS Cloud, Docker containerization, and GraphRAG.
- Foster connection between community members, mentors, and program participants.

##### Speakers & Topics

| Speaker | Topic |
|:---|:---|
| **Bảo Huỳnh** | Docker – A Containerization Technology |
| **Lê Hoàng Gia Đại** | Combining AWS WAF with Machine Learning for Cyber Attack Detection on AWS |
| **Nguyễn Quốc Bảo** | Multiplayer in the Cloud: Connecting Godot Clients with AWS WebSockets |
| **Trương Phước** | Cách làm việc nhóm hiệu quả (Effective Teamwork) |
| **Vinh Trần** | Từ IT Helpdesk lên Senior Sysadmin – Hành trình tự học và Lộ trình dịch chuyển sang Cloud/DevOps |
| **Việt Phát** | AWS Neptune for Building a Graph Knowledge Base for GraphRAG |

---

#### Key Highlights

**1. Docker – A Containerization Technology (Bảo Huỳnh)**
- Introduction to container concepts: how Docker isolates applications from the underlying host OS.
- Core components: Dockerfile, Image, Container, Docker Compose.
- Practical benefits: consistent dev/prod environments, fast deployment, and portability across machines.
- Comparison between virtual machines (VMs) and containers in terms of resource overhead and startup speed.

**2. AWS WAF & Machine Learning for Cyber Attack Detection (Lê Hoàng Gia Đại)**
- Overview of common web attack vectors: SQL injection, XSS, DDoS, bot traffic.
- How AWS WAF (Web Application Firewall) works with rule groups and IP sets.
- Integrating Machine Learning models (Network Intrusion Detection System – NIDS) with AWS WAF for intelligent threat detection.
- Architecture: traffic logs → S3 → Lambda → ML inference → WAF rule updates.

**3. Multiplayer Gaming with AWS WebSockets (Nguyễn Quốc Bảo)**
- Building real-time multiplayer features in Godot game engine using AWS API Gateway WebSocket API.
- Serverless architecture: WebSocket connections managed via Lambda and DynamoDB connection store.
- Broadcasting game events to all connected clients without a dedicated game server.

**4. Effective Teamwork (Trương Phước)**
- Principles of high-performing teams: clear communication, role definition, and accountability.
- Tools and methods for remote collaboration and task tracking.
- Real-world lessons learned from working in Cloud and Software projects.

**5. From IT Helpdesk to Senior Sysadmin & Cloud/DevOps (Vinh Trần)**
- Personal learning roadmap: starting from entry-level IT support to becoming a Senior Sysadmin.
- Key milestones: Linux administration, networking, then transitioning into Cloud and DevOps tooling.
- Recommended learning resources and certifications (e.g., AWS Cloud Practitioner, Solutions Architect).
- Advice for students and early-career professionals on how to navigate a self-taught journey.

**6. AWS Neptune for GraphRAG (Việt Phát)**
- Introduction to Knowledge Graphs and why they enhance Retrieval-Augmented Generation (RAG) for LLMs.
- AWS Neptune as a managed graph database service (supporting Gremlin and SPARQL).
- Architecture: data ingestion → Neptune graph store → vector embedding → RAG pipeline → LLM response.
- Use cases: enterprise knowledge bases, semantic search, and context-aware AI assistants.

---

#### Key Takeaways

- **Containerization is foundational:** Docker is a must-have skill in any modern cloud deployment workflow.
- **Security as code:** Combining AWS WAF with ML models enables adaptive, automated threat defense rather than static rule-based blocking.
- **Serverless unlocks real-time capabilities:** WebSocket APIs on API Gateway can power real-time multiplayer, chat, and notification features without managing servers.
- **Career paths are non-linear:** Vinh Trần's journey demonstrates that consistent self-learning and hands-on practice can lead to a successful Cloud/DevOps career even without a traditional computer science background.
- **GraphRAG enhances AI accuracy:** Connecting LLMs to graph-structured knowledge bases in Neptune significantly improves answer quality and context-awareness compared to flat vector search alone.

---

#### Applying to Work
- Apply Docker containerization in our Lambda deployment pipeline (already implemented via ECR).
- Explore AWS WAF integration to protect our API Gateway endpoint from abuse.
- Consider Neptune-based knowledge graph as a future enhancement to our stock prediction system (linking related companies, sectors, and market events).

---

#### Event Photos
*Add your event photos here.*

---

Overall, the first FCAJ Meetup set a strong foundation for the program — covering a diverse range of topics from infrastructure (Docker, AWS WAF) to application development (WebSockets, GraphRAG) and career development. It was an excellent opportunity to meet fellow participants and learn from experienced practitioners in the Vietnamese AWS community.
