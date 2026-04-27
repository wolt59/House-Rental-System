# 🏠 智能房屋租赁系统

基于 **FastAPI + Vue3 + MySQL** 的智能房屋租赁系统，支持租客、房东、管理员三种角色。

## 项目结构

```
House-Rental-System/
├── app/                    # 后端应用
│   ├── api/                # API 路由
│   ├── core/               # 核心配置
│   ├── crud/               # 数据库操作
│   ├── db/                 # 数据库连接
│   ├── models/             # SQLAlchemy 模型
│   ├── schemas/            # Pydantic 模型
│   └── main.py             # 应用入口
├── frontend/               # 前端应用 (Vue3)
│   ├── src/
│   │   ├── api/            # API 封装
│   │   ├── store/          # Pinia 状态管理
│   │   ├── router/         # 路由配置
│   │   ├── views/          # 页面组件
│   │   └── layouts/        # 布局组件
│   └── package.json
├── doc/                    # 文档与数据库脚本
├── requirements.txt        # Python 依赖
└── .env.example            # 环境变量模板
```

---

## 后端配置

### 方式一：Conda 虚拟环境

```powershell
# 创建环境
conda create -n hrs python=3.11 -y

# 激活环境
conda activate hrs

# 安装依赖
pip install -r requirements.txt
```

### 方式二：Python venv

```powershell
# 创建虚拟环境
python -m venv .venv

# 激活环境 (Windows)
.\.venv\Scripts\activate

# 激活环境 (Linux/macOS)
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```


---

## 数据库配置

### 1. 创建 MySQL 数据库

```sql
CREATE DATABASE house_rental DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;
```

### 2. 配置环境变量

复制模板文件：

```powershell
copy .env.example .env
```

编辑 `.env` 文件：

```ini
SQLALCHEMY_DATABASE_URI=mysql+pymysql://root:你的密码@127.0.0.1:3306/house_rental
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=10080
BACKEND_CORS_ORIGINS=["*"]
```

### 3. 初始化数据库

```powershell
# 使用 MySQL 命令行导入
mysql -u root -p house_rental < doc/init_db.sql
```

---

## 启动项目

### 启动后端

```powershell
# 进入项目目录
cd House-Rental-System

# 激活虚拟环境后启动
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

后端 API 文档：http://127.0.0.1:8000/docs

### 启动前端

```powershell
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端页面：http://localhost:3000

---

## 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |

> 首次部署后请及时修改默认密码

---

## 技术栈

### 后端
- Python 3.11+
- FastAPI - Web 框架
- SQLAlchemy - ORM
- MySQL - 数据库
- PyJWT - 身份认证
- Passlib + bcrypt - 密码加密

### 前端
- Vue 3 - 前端框架
- Vite - 构建工具
- Element Plus - UI 组件库
- Pinia - 状态管理
- Vue Router - 路由
- Axios - HTTP 客户端

---

## 开发命令

```powershell
# 后端开发模式
uvicorn app.main:app --reload

# 前端开发模式
cd frontend && npm run dev

# 前端构建生产版本
cd frontend && npm run build

# 前端预览生产版本
cd frontend && npm run preview
```

---

## 环境要求

- Python >= 3.11
- Node.js >= 18
- MySQL >= 8.0
- npm 或 yarn
