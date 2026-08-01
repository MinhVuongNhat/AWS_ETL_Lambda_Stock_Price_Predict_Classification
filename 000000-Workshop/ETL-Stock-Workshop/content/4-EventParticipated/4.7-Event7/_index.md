---
title: "Event 7 - FCAJ x AABW Community Day"
date: "2026-07-25"
weight: 7
chapter: false
pre: "<b> 4.7. </b>"
---

#### Event 7 – FCAJ x AABW Community Day (July 25, 2026)

{{% notice info %}}
📅 **Date:** July 25, 2026 | 📍 **Format:** In-person | 🏢 **Organizer:** First Cloud AI Journey (FCAJ) x AWS Ambassadors & Builders in Vietnam (AABW)
{{% /notice %}}

---

#### Summary Report: "FCAJ x AABW Community Day – Hackathon, Cloud Solutions & Native App Development"

##### Event Objectives
- Showcase the journeys and results of FCAJ program teams through hackathon-style project presentations.
- Share advanced cloud architecture insights and native application development best practices.
- Celebrate the community collaboration between FCAJ and AABW (AWS Ambassadors & Builders in Vietnam).
- Foster networking between interns, AWS ambassadors, and experienced cloud practitioners.

##### Presentations

| # | Presentation | Description |
|:---|:---|:---|
| 1 | **Hackathon Journey – 3KA** | FCAJ team project showcase and hackathon experience |
| 2 | **SA Professional – Native App Development** | Solutions Architect insights on cloud-native application design |
| 3 | **SignalScout** | Cloud-powered signal intelligence application demo |
| 4 | **OneTeam Community Day** | Community highlights and program retrospective |

---

#### Key Highlights

**1. Hackathon Journey – 3KA**
- Team 3KA shared their complete end-to-end journey building a cloud-powered solution during the FCAJ hackathon phase.
- Architecture walkthrough: from requirements and design through implementation, testing, and deployment on AWS.
- Key technical decisions: service selection rationale, trade-offs made, and lessons learned from real AWS deployments.
- Challenges overcome: cold start optimization, data pipeline bottlenecks, and managing costs within Free Tier limits.
- Reflections on teamwork, time management under hackathon constraints, and the iterative development process.

**2. SA Professional – Native App Development on AWS**
- Solutions Architect-level guidance on designing modern cloud-native applications.
- **Twelve-Factor App methodology** applied to AWS: configuration via environment variables, disposable processes, and dev/prod parity.
- Comparing architecture patterns for native apps: monolith vs. microservices vs. serverless — choosing the right approach based on team size, workload, and scalability requirements.
- Deep dive into container orchestration: ECS vs. EKS vs. App Runner for different deployment scenarios.
- Best practices for API design, versioning, and backwards compatibility on API Gateway.
- Observability stack: implementing structured logging (CloudWatch Logs Insights), distributed tracing (X-Ray), and metrics dashboards.

**3. SignalScout – Cloud-powered Signal Intelligence**
- Live demo of SignalScout: a cloud application for aggregating, analyzing, and visualizing signal intelligence data.
- Architecture: real-time data ingestion → Lambda processing → DynamoDB storage → API Gateway → React frontend.
- Machine learning integration: anomaly detection models deployed as Lambda functions for real-time signal classification.
- Scalability design: handling burst traffic with SQS buffering and Lambda concurrency management.
- Practical lessons on building production-ready cloud applications as a student team within time and budget constraints.

**4. OneTeam Community Day – Retrospective & Closing**
- Program retrospective: highlights, achievements, and memorable moments from the FCAJ cohort.
- Community recognition: acknowledging standout contributions from participants, mentors, and admin team.
- Networking session: open floor for Q&A, knowledge exchange, and connections between FCAJ participants and AABW members.
- Looking ahead: future FCAJ phases, recommended learning paths, and continued community engagement.

---

#### Key Takeaways

- **End-to-end project experience is irreplaceable:** Hearing Team 3KA's complete hackathon journey reinforced that the most valuable learning comes from building and deploying real systems under pressure, not just studying theory.
- **Cloud-native principles are universal:** The Twelve-Factor App and microservices patterns discussed by the SA professional apply directly to our own Lambda + API Gateway + DynamoDB architecture.
- **Production readiness goes beyond functionality:** SignalScout demonstrated that observability (logging, tracing, dashboards), scalability design, and cost management are non-negotiable for any production AWS system.
- **Community multiplies learning:** The joint FCAJ x AABW format connected participants with AWS ambassadors and builders who have deep, battle-tested expertise — the kind of knowledge not found in documentation.
- **Reflection is part of the journey:** The OneTeam retrospective demonstrated that structured program reflection is as valuable as the technical work itself.

---

#### Applying to Work
- Apply Twelve-Factor App principles to refactor our project's Lambda function configuration management (currently using hardcoded env vars — move to AWS Systems Manager Parameter Store).
- Implement AWS X-Ray distributed tracing on our Lambda functions to gain end-to-end visibility into request latency and error paths.
- Use the SignalScout SQS buffering pattern as inspiration for handling burst traffic on our stock data ingestion pipeline.
- Document our own end-to-end project journey in the Workshop documentation (this site!) following the narrative format demonstrated by Team 3KA.

---

#### Event Photos

![FCAJ x AABW Community Day – Hackathon showcase and community gathering](/images/event/25-07.png)

---

The FCAJ x AABW Community Day was the perfect closing event for the FCAJ program — combining the showcase of intern project achievements with world-class technical talks from AWS ambassadors and builders. It left every participant energized about their cloud journey and motivated to continue building, learning, and contributing to the Vietnamese AWS community.
