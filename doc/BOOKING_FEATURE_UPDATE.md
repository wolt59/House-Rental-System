# 预约看房功能更新说明

## ✅ 已完成的修改

### 后端修改
1. **数据库模型** (`app/models/booking.py`)
   - 新增字段：reject_reason, reschedule_proposal, reschedule_response, completed_at, landlord_contact_shown

2. **枚举类型** (`app/core/enums.py`)
   - 新增状态：NEGOTIATING（待协商）, COMPLETED（已完成）, OVERDUE（已逾期）

3. **Schema定义** (`app/schemas/booking.py`)
   - 更新BookingInDBBase和BookingUpdate
   - 新增BookingReschedule和BookingRescheduleResponse

4. **CRUD操作** (`app/crud/crud_booking.py`)
   - 新增：approve_booking, reject_booking, propose_reschedule, complete_booking, mark_overdue

5. **API接口** (`app/api/api_v1/endpoints/bookings.py`)
   - POST /approve - 同意预约
   - POST /{id}/reject - 拒绝预约
   - POST /{id}/reschedule - 提出改期
   - POST /{id}/reschedule-response - 响应改期
   - POST /{id}/complete - 标记完成
   - POST /{id}/show-contact - 查看联系方式

### 前端修改
1. **API接口** (`frontend/src/api/booking.js`)
   - 新增所有预约相关的API调用函数

2. **房源详情页** (`frontend/src/views/common/PropertyDetail.vue`)
   - 优化预约表单，使用统一的600px宽度和两列布局

3. **租客端预约页** (`frontend/src/views/tenant/Bookings.vue`)
   - 新增状态分类筛选（全部/待确认/已同意/待协商/已完成/已拒绝/已取消）
   - 新增操作：标记完成、查看联系方式、同意/拒绝改期、查看详情

4. **房东端预约页** (`frontend/src/views/landlord/Bookings.vue`)
   - 新增状态分类筛选（全部/待处理/已处理）
   - 新增操作：同意、拒绝（需填写原因）、改期、标记完成、查看详情
   - 新增拒绝对话框和改期对话框

##  接下来的步骤

### 1. 执行数据库迁移

打开MySQL客户端，执行迁移脚本：

```sql
-- 方法1：使用命令行
mysql -u root -p your_database_name < doc/migration_booking_enhancement.sql

-- 方法2：在MySQL客户端中直接执行
source D:/CODE/House-Rental-System/doc/migration_booking_enhancement.sql;
```

或者手动执行以下SQL：

```sql
ALTER TABLE bookings 
ADD COLUMN reject_reason VARCHAR(500) NULL COMMENT '拒绝原因',
ADD COLUMN reschedule_proposal TEXT NULL COMMENT '改期建议',
ADD COLUMN reschedule_response VARCHAR(50) NULL COMMENT '租客对改期的响应',
ADD COLUMN completed_at DATETIME NULL COMMENT '看房完成时间',
ADD COLUMN landlord_contact_shown INT DEFAULT 0 COMMENT '是否已查看房东联系方式';

ALTER TABLE bookings 
ADD INDEX idx_tenant_status (tenant_id, status),
ADD INDEX idx_property_status (property_id, status),
ADD INDEX idx_status (status),
ADD INDEX idx_appointment_time (appointment_time);
```

### 2. 重启后端服务

```bash
# 停止当前运行的后端（如果正在运行）
# Ctrl+C

# 重新启动
cd D:\CODE\House-Rental-System
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 前端会自动热更新

前端开发服务器已经在运行的话，会自动检测到文件变化并重新编译。

如果没有运行，请启动：

```bash
cd D:\CODE\House-Rental-System\frontend
npm run dev
```

### 4. 清除浏览器缓存

为了确保看到最新的效果：
- 按 `Ctrl + Shift + R` 强制刷新
- 或者按 `Ctrl + F5`
- 或者打开浏览器开发者工具 → Network → 勾选 "Disable cache"

## 🎯 功能测试清单

### 租客端测试
- [ ] 在房源详情页点击"预约看房"，选择未来时间并提交
- [ ] 在"我的预约"页面查看预约列表
- [ ] 切换不同的状态标签筛选预约
- [ ] 对待确认的预约进行取消操作
- [ ] 对已同意的预约点击"标记完成"
- [ ] 对已同意的预约点击"联系方式"
- [ ] 对待协商的预约进行同意/拒绝/取消操作
- [ ] 点击"详情"查看完整预约信息

### 房东端测试
- [ ] 在"预约管理"页面查看预约列表
- [ ] 切换到"待处理"标签查看待审核预约
- [ ] 点击"同意"确认预约
- [ ] 点击"拒绝"并填写拒绝原因
- [ ] 点击"改期"选择新时间并填写说明
- [ ] 对已同意的预约点击"标记完成"
- [ ] 点击"详情"查看完整预约信息

## 🐛 可能遇到的问题

### 问题1：后端启动报错
**原因**：数据库字段未添加
**解决**：确保已执行数据库迁移SQL

### 问题2：前端页面不显示新按钮
**原因**：浏览器缓存
**解决**：强制刷新页面（Ctrl+Shift+R）

### 问题3：API调用404错误
**原因**：后端服务未重启
**解决**：重启后端服务

### 问题4：预约时间可以选择过去的时间
**原因**：前端时间选择器配置问题
**解决**：已配置 `:disabled-date` 属性，确保刷新页面

## 📝 状态流转说明

```
租客发起预约
    ↓
pending（待确认）
    ↓
房东操作：
├─ 同意 → approved（已同意）
│   ├─ 租客标记完成 → completed（已完成）
│   └─ 超时未处理 → overdue（已逾期）
├─ 拒绝 → rejected（已拒绝）
│   └─ 显示拒绝原因
└─ 改期 → negotiating（待协商）
    ├─ 租客同意 → approved（已同意）
    ├─ 租客拒绝 → pending（待确认）
    └─ 租客取消 → cancelled（已取消）
```

## ✨ 新增功能亮点

1. **状态管理完善**：7种状态覆盖所有业务场景
2. **改期协商机制**：房东和租客可以协商调整时间
3. **拒绝原因必填**：房东拒绝时必须填写原因
4. **标记完成功能**：双方都可以标记看房完成
5. **联系方式保护**：只有预约被同意后才会显示房东联系方式
6. **分类筛选**：按状态快速筛选预约记录
7. **详情查看**：完整的预约信息展示

##  技术改进

- 使用Element Plus的el-tabs实现状态分类
- 统一表单样式（600px宽度，90px标签宽度）
- 表格自适应宽度（min-width替代固定width）
- 操作列固定在右侧（fixed="right"）
- 完整的错误处理和用户提示
