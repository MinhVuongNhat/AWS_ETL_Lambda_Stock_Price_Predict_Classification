---
title: "Sự kiện 1 - FCAJ Meetup #1"
date: "2026-06-06"
weight: 1
chapter: false
pre: "<b> 4.1. </b>"
---

#### Sự kiện 1 – FCAJ Meetup #1 (06/06/2026)

{{% notice info %}}
📅 **Ngày:** 06/06/2026 | 📍 **Hình thức:** Tham gia trực tiếp | 🏢 **Đơn vị tổ chức:** First Cloud AI Journey (FCAJ)
{{% /notice %}}

---

#### Báo cáo tóm tắt: "FCAJ Meetup #1 – Buổi Khai mạc & Chia sẻ Cộng đồng"

##### Mục tiêu sự kiện
- Khai mạc chương trình First Cloud AI Journey, giới thiệu cộng đồng và định hướng cho các thành viên.
- Chia sẻ kiến thức thực tế về AWS Cloud, Docker containerization và GraphRAG.
- Kết nối các thành viên cộng đồng, mentor và học viên trong chương trình.

##### Diễn giả & Chủ đề

| Diễn giả | Chủ đề |
|:---|:---|
| **Bảo Huỳnh** | Docker – Công nghệ Containerization |
| **Lê Hoàng Gia Đại** | Kết hợp AWS WAF với Machine Learning để phát hiện tấn công mạng trên AWS |
| **Nguyễn Quốc Bảo** | Multiplayer trên Cloud: Kết nối Godot Clients với AWS WebSockets |
| **Trương Phước** | Cách làm việc nhóm hiệu quả |
| **Vinh Trần** | Từ IT Helpdesk lên Senior Sysadmin – Hành trình tự học và lộ trình chuyển sang Cloud/DevOps |
| **Việt Phát** | AWS Neptune để xây dựng Graph Knowledge Base cho GraphRAG |

---

#### Điểm nổi bật

**1. Docker – Công nghệ Containerization (Bảo Huỳnh)**
- Giới thiệu khái niệm container: cách Docker cô lập ứng dụng khỏi hệ điều hành máy chủ.
- Các thành phần cốt lõi: Dockerfile, Image, Container, Docker Compose.
- Lợi ích thực tế: môi trường dev/prod đồng nhất, triển khai nhanh, di chuyển giữa các máy dễ dàng.
- So sánh giữa máy ảo (VM) và container về tài nguyên và tốc độ khởi động.

**2. AWS WAF & Machine Learning để phát hiện tấn công mạng (Lê Hoàng Gia Đại)**
- Tổng quan các véc-tơ tấn công web phổ biến: SQL injection, XSS, DDoS, bot traffic.
- Cách AWS WAF hoạt động với rule groups và IP sets.
- Tích hợp mô hình Machine Learning (NIDS) với AWS WAF để phát hiện mối đe dọa thông minh.
- Kiến trúc: traffic logs → S3 → Lambda → ML inference → cập nhật WAF rule.

**3. Multiplayer Gaming với AWS WebSockets (Nguyễn Quốc Bảo)**
- Xây dựng tính năng multiplayer real-time trong game engine Godot sử dụng AWS API Gateway WebSocket API.
- Kiến trúc serverless: quản lý kết nối WebSocket qua Lambda và DynamoDB.
- Broadcast sự kiện game tới tất cả client đang kết nối mà không cần dedicated game server.

**4. Làm việc nhóm hiệu quả (Trương Phước)**
- Nguyên tắc của đội nhóm hiệu suất cao: giao tiếp rõ ràng, phân công vai trò và trách nhiệm.
- Công cụ và phương pháp cộng tác từ xa và theo dõi công việc.
- Bài học thực tế từ kinh nghiệm làm dự án Cloud và phần mềm.

**5. Từ IT Helpdesk lên Senior Sysadmin & Cloud/DevOps (Vinh Trần)**
- Lộ trình học tập cá nhân: từ IT support cơ bản đến Senior Sysadmin.
- Các mốc quan trọng: quản trị Linux, networking, rồi chuyển sang Cloud và DevOps tooling.
- Các tài nguyên học tập và chứng chỉ khuyến nghị (AWS Cloud Practitioner, Solutions Architect).
- Lời khuyên cho sinh viên và người đi làm trẻ về hành trình tự học.

**6. AWS Neptune cho GraphRAG (Việt Phát)**
- Giới thiệu Knowledge Graph và lý do chúng cải thiện Retrieval-Augmented Generation (RAG) cho LLM.
- AWS Neptune là managed graph database service (hỗ trợ Gremlin và SPARQL).
- Kiến trúc: nhập dữ liệu → lưu trên Neptune → vector embedding → RAG pipeline → phản hồi LLM.
- Ứng dụng: knowledge base doanh nghiệp, semantic search, và AI assistant nhận biết ngữ cảnh.

---

#### Bài học rút ra

- **Containerization là nền tảng:** Docker là kỹ năng bắt buộc trong quy trình triển khai Cloud hiện đại.
- **Bảo mật như code:** Kết hợp AWS WAF với ML cho phép phòng thủ thích ứng, tự động thay vì chỉ dựa vào rule tĩnh.
- **Serverless mở ra khả năng real-time:** WebSocket API Gateway có thể hỗ trợ multiplayer, chat và thông báo mà không cần quản lý server.
- **Con đường sự nghiệp không tuyến tính:** Hành trình của Vinh Trần chứng minh rằng tự học và thực hành liên tục có thể dẫn đến thành công trong Cloud/DevOps.
- **GraphRAG nâng cao độ chính xác AI:** Kết nối LLM với knowledge graph trên Neptune cải thiện đáng kể chất lượng câu trả lời so với vector search thuần túy.

---

#### Áp dụng vào dự án
- Áp dụng Docker containerization trong pipeline deploy Lambda (đã thực hiện qua ECR).
- Khám phá tích hợp AWS WAF để bảo vệ API Gateway endpoint.
- Xem xét Neptune-based knowledge graph như hướng mở rộng tương lai cho hệ thống dự đoán cổ phiếu.

---

#### Ảnh sự kiện
*Thêm ảnh sự kiện của bạn tại đây.*

---

Nhìn chung, FCAJ Meetup #1 đã tạo nền tảng vững chắc cho chương trình – bao gồm đa dạng chủ đề từ hạ tầng (Docker, AWS WAF) đến phát triển ứng dụng (WebSockets, GraphRAG) và phát triển sự nghiệp. Đây là cơ hội tuyệt vời để gặp gỡ các thành viên đồng hành và học hỏi từ những người thực chiến trong cộng đồng AWS Việt Nam.
