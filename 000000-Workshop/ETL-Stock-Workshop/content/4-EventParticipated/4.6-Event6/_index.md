---
title: "Event 6 - FCAJ Meetup #3 & Tranh Hùng Grand Final"
date: "2026-07-11"
weight: 6
chapter: false
pre: "<b> 4.6. </b>"
---

#### Event 6 – FCAJ Meetup #3 & "Tranh Hùng" Grand Final (July 11, 2026)

{{% notice info %}}
📅 **Date:** July 11, 2026 | 📍 **Format:** In-person | 🏢 **Organizer:** First Cloud AI Journey (FCAJ)
{{% /notice %}}

---

#### Summary Report: "FCAJ Meetup #3 – Tranh Hùng Grand Final & Technical Talks"

##### Event Objectives
- Crown the Tranh Hùng champion team from among the qualifying teams.
- Continue technical knowledge sharing with community talks on AWS security, cloud practitioner certification, and student risk monitoring.
- Celebrate achievements and strengthen community bonds within the FCAJ program.

---

#### Part 1: "Tranh Hùng" Grand Final

The grand final of the **Tranh Hùng** inter-team AWS knowledge competition concluded the tournament that began in the qualifying round on June 20, 2026.

**Final Format**
- Top qualifying teams from the June 20 round competed head-to-head in the final.
- The same scoring rules applied: +1 for correct answers, -1 for incorrect answers.
- Questions in the final were more advanced, covering architectural design decisions, AWS service trade-offs, and scenario-based problem solving.

**Notable Final Round Topics**
- Designing multi-region disaster recovery architectures (RPO/RTO targets).
- Choosing between Aurora Serverless vs. DynamoDB for different application workloads.
- AWS Step Functions for orchestrating complex serverless workflows.
- CloudFront distribution configuration and cache invalidation strategies.
- Security Hub vs. GuardDuty vs. Inspector: selecting the right security tooling.
- AWS Organizations and Service Control Policies for multi-account governance.

---

#### Part 2: Technical Talks

Following the grand final, the meetup continued with three technical presentations:

**Talk 1: Inside the Exam – AWS Cloud Practitioner**
- Comprehensive breakdown of the AWS Certified Cloud Practitioner (CLF-C02) exam structure and domain weights.
- Study strategies: recommended resources (AWS Skill Builder, Stephane Maarek, TutorialsDojo practice exams).
- Key topics tested: cloud concepts, AWS core services, security & compliance, billing & pricing.
- Exam tips: time management, eliminating obviously wrong answers, and leveraging process of elimination.
- Q&A covering common pitfalls and how to approach scenario-based questions on the exam.

**Talk 2: Securing Your Web Apps with AWS Security Agent**
- Introduction to building an intelligent security agent on AWS that monitors and responds to web application threats.
- Architecture: Application Load Balancer → WAF → Lambda security agent → CloudWatch logs → SNS alerting.
- Using Amazon Bedrock or Claude to power an AI-driven security analysis layer.
- Real-time threat detection and automated remediation: blocking IPs, updating WAF rules, and triggering incident response.
- Demo: detecting SQL injection patterns and automatically updating WAF IP block lists.

**Talk 3: AWS SLA Monitoring – Student Risk Assessment System**
- Practical demo of an AWS-powered student risk monitoring system built during the FCAJ program.
- Architecture: data ingestion (student metrics) → S3 → Lambda processing → DynamoDB → CloudWatch dashboard.
- Defining SLA thresholds for student performance KPIs and automated alerting for at-risk students.
- Lessons learned from building production-grade monitoring systems on AWS Free Tier constraints.

---

#### Key Takeaways

- **Competition drives depth:** The grand final pushed participants to study more advanced AWS topics (multi-region, Step Functions, Organizations) than they would have encountered in typical project work.
- **Certification provides structure:** The AWS Cloud Practitioner talk clarified that certification study, even for developers already using AWS in projects, helps systematize and fill knowledge gaps.
- **AI-powered security is the future:** The security agent talk demonstrated that the next generation of cloud security is not static rules — it is intelligent, adaptive systems that learn from new threats in real-time.
- **Monitoring = quality:** Building robust monitoring systems (as shown in the SLA talk) is just as important as building the application itself; it is often the difference between a toy project and a production system.

---

#### Applying to Work
- Study the AWS Cloud Practitioner certification materials to formalize understanding and fill gaps revealed during the Tranh Hùng competition.
- Apply the security agent architecture pattern to protect our API Gateway endpoint with more intelligent threat detection.
- Implement CloudWatch dashboards for the `NasdaqStockPredictions` API to monitor SLA compliance and error rates.

---

#### Event Photos

![FCAJ Meetup #3 – Tranh Hùng Grand Final and technical talks](/images/event/11-07.png)

---

The combined Tranh Hùng Grand Final and FCAJ Meetup #3 was arguably the most packed and energy-filled event of the entire program. The competitive climax of the tournament, combined with three high-quality technical talks, made it an outstanding capstone to the mid-program community building phase.
