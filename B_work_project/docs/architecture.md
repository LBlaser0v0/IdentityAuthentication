# 系统架构说明

本项目采用本地多服务模拟架构：

- Client App: `127.0.0.1:8001`
- Authorization Server: `127.0.0.1:8000`
- Resource Server: `127.0.0.1:8002`
- Shared SQLite DB: `data/app.db`

该架构便于课程作业演示、论文画图和后续成员协作扩展。
