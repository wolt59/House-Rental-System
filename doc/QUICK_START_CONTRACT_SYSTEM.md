# 电子合同系统 - 快速开始指南

## 🚀 立即测试合约申请功能

### 步骤1: 执行数据库迁移

打开 PowerShell，执行以下命令：

```powershell
cd D:\CODE\House-Rental-System
mysql -u root -p house_rental_system < doc\migration_contract_system_enhancement.sql
```

**注意**: 
- 系统会提示输入MySQL密码
- 如果看到 "Query OK" 等成功信息，说明迁移成功
- 如果有错误，请将错误信息复制给我

---

### 步骤2: 启动后端服务

在 PowerShell 中执行：

```powershell
uvicorn app.main:app --reload --port 8000
```

**预期输出**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxx] using WatchFiles
INFO:     Started server process [xxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**验证**: 访问 http://localhost:8000/docs，应该能看到Swagger API文档页面

---

### 步骤3: 安装前端依赖（如果需要）

```powershell
cd frontend
npm install dayjs
```

---

### 步骤4: 启动前端开发服务器

```powershell
cd frontend
npm run dev
```

**预期输出**:
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

---

### 步骤5: 测试完整流程

#### 5.1 以租客身份登录
1. 浏览器访问 http://localhost:5173
2. 使用租客账号登录（如果没有，先注册一个）
3. 默认测试账号（如果有的话）

#### 5.2 预约看房
1. 浏览房源列表
2. 选择一个房源，进入详情页
3. 点击"预约看房"按钮
4. 选择预约时间，提交预约

#### 5.3 房东同意预约
1. 退出租客账号，以房东身份登录
2. 进入"我的预约"管理页面
3. 找到刚才的预约，点击"同意"

#### 5.4 租客标记看房完成
1. 切换回租客账号
2. 进入"我的预约"页面
3. 找到状态为"已同意"的预约
4. 点击"标记完成"按钮

#### 5.5 发起合约申请 ⭐ 新功能
1. 在"我的预约"页面，找到状态为"已完成"的预约
2. 应该会看到 **"发起合约申请"** 按钮
3. 点击该按钮，进入申请表单页面
4. 填写以下信息：
   - 租赁开始日期
   - 租赁结束日期
   - 付款方式（押一付三、押一付一等）
   - 补充说明（选填）
5. 点击"提交申请"

#### 5.6 查看申请状态
1. 提交成功后，会自动返回预约列表
2. 可以再次进入申请页面查看状态
3. 等待房东处理

---

## 📋 API 测试（可选）

如果您想直接测试API，可以使用Swagger界面或curl命令：

### 创建合约申请

```bash
curl -X POST "http://localhost:8000/api/v1/contract-applications/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "booking_id": 1,
    "start_date": "2026-06-01T00:00:00",
    "end_date": "2027-06-01T00:00:00",
    "payment_method": "押一付三",
    "additional_notes": "希望能尽快入住"
  }'
```

### 获取申请列表

```bash
curl -X GET "http://localhost:8000/api/v1/contract-applications/?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## ✅ 功能检查清单

完成上述步骤后，您应该能够：

- [ ] 在看房完成后看到"发起合约申请"按钮
- [ ] 成功提交合约申请表单
- [ ] 在数据库中看到新创建的申请记录
- [ ] 申请状态初始为"apply_pending"
- [ ] 表单验证正常工作（日期选择、必填项等）
- [ ] 租期时长自动计算显示

---

## ❌ 常见问题排查

### 问题1: 数据库连接失败
**错误信息**: `Can't connect to MySQL server`

**解决方案**:
1. 确认MySQL服务已启动
2. 检查 `.env` 文件中的数据库配置
3. 确认数据库 `house_rental_system` 已创建

### 问题2: 表不存在
**错误信息**: `Table 'contract_applications' doesn't exist`

**解决方案**:
重新执行数据库迁移脚本

### 问题3: 后端启动失败 - 导入错误
**错误信息**: `ImportError: cannot import name 'xxx'`

**解决方案**:
1. 检查是否有语法错误
2. 确认所有导入的模块都存在
3. 重启后端服务

### 问题4: 前端看不到"发起合约申请"按钮
**可能原因**:
1. 看房状态不是"completed"
2. 前端代码未更新

**解决方案**:
1. 确认预约状态是"已完成"
2. 刷新浏览器页面（Ctrl+F5）
3. 检查浏览器控制台是否有错误

### 问题5: 提交申请时400错误
**可能原因**:
1. booking_id不正确
2. 看房记录不属于当前用户
3. 看房状态不是completed

**解决方案**:
检查请求参数和业务逻辑

---

## 🎯 下一步开发建议

完成测试后，您可以继续开发以下功能：

### 优先级1 - 房东处理申请
1. 创建房东查看申请的页面
2. 实现同意/拒绝操作
3. 同意后自动生成合同草稿

### 优先级2 - 合同编辑
1. 创建合同编辑页面
2. 使用 ContractDocument.vue 组件展示合同正文
3. 实现可编辑字段内联输入

### 优先级3 - 合同签署
1. 创建签名画板组件
2. 实现签署流程
3. 记录签署信息（IP、设备）

---

## 📞 需要帮助？

如果在测试过程中遇到任何问题，请提供：

1. **完整的错误信息**（包括堆栈跟踪）
2. **执行的命令**
3. **浏览器控制台的错误**（如果是前端问题）
4. **后端日志输出**

我会立即帮您解决！

---

## 📚 相关文档

- [实施进度报告](./CONTRACT_SYSTEM_PROGRESS.md) - 详细的实施状态
- [数据库迁移脚本](./migration_contract_system_enhancement.sql) - SQL脚本
- [原始需求规格](../todo.md) - 完整的需求描述
