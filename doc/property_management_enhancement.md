# 房源管理优化方案

## 📋 优化概述

本次优化对房源管理模块进行了全面升级，引入了更完善的审核流程和发布控制机制。

## 🎯 核心改进

### 1. 新增审核流程状态

**原有流程：**
```
创建 → pending → approved/rejected
```

**优化后流程：**
```
draft(草稿) → pending(待审核) → reviewing(审核中) → approved(已通过) → published(已发布)
                    ↑                                    ↓              ↓
                    └──── 重新申请 ◄─────────────── unpublished(未发布)
                                                            ↓
                                                    rented(已出租)
                                                            ↓
                                                    maintenance(维修中)
```

### 2. 状态说明

#### 审核状态 (review_status)
- **draft**: 草稿 - 房东创建后的初始状态，可自由编辑
- **pending**: 待审核 - 房东提交审核申请后，等待管理员处理
- **reviewing**: 审核中 - 管理员开始审核
- **approved**: 已通过 - 审核通过，自动发布
- **rejected**: 已拒绝 - 审核未通过，可修改后重新提交

#### 发布状态 (status)
- **published**: 已发布 - 租客可见，可被搜索和预订
- **unpublished**: 未发布 - 房东主动取消发布或管理员下架，租客不可见
- **vacant**: 空置 - 已发布且未出租（与published等价，保留兼容）
- **rented**: 已出租 - 已有生效合同
- **maintenance**: 维修中 - 正在进行维护

### 3. 新增时间戳字段

- `submitted_at`: 提交审核时间
- `approved_at`: 审核通过时间
- `published_at`: 发布时间
- `unpublished_at`: 暂停发布时间

## 🔐 权限与限制

### 房源修改权限矩阵

| 房源状态 | 可修改字段 | 是否需要重新审核 | 说明 |
|---------|-----------|----------------|------|
| **draft** | 全部字段 | ❌ 否 | 草稿阶段自由编辑 |
| **pending/reviewing** | 仅描述/图片/视频/设施/周边 | ❌ 否 | 审核中锁定核心信息 |
| **approved + published/unpublished/vacant** | 非核心字段 | ❌ 否 | 可改标题、描述、图片等 |
| **approved + published/unpublished/vacant** | 核心字段 | ✅ 是 | 改租金、面积等会自动转为待审核 |
| **approved + rented/maintenance** | 仅描述 | ❌ 否 | 已出租锁定大部分字段 |
| **rejected** | 全部字段 | ❌ 否 | 可自由修改后重新提交 |
| **draft + unpublished** | 全部字段 | ❌ 否 | 管理员下架后的状态，房东可修改后重新提交 |

### 核心字段定义

以下字段修改需要重新提交审核：
- 地址 (address)
- 户型 (floor_plan)
- 面积 (area)
- 租金 (rent)
- 押金 (deposit)
- 楼层 (floor_number, total_floors)

### 非核心字段

以下字段可直接修改，无需重新审核：
- 标题 (title)
- 装修 (decoration)
- 朝向 (orientation)
- 设施 (facilities)
- 周边配套 (surrounding)
- 描述 (description)
- 视频 (video_url)
- 图片 (images)

## 🛠️ API 接口变更

### 新增接口

#### 1. 提交审核
```http
POST /api/v1/properties/{property_id}/submit-review
```
**功能：** 房东将草稿或被拒绝的房源提交审核  
**权限：** 房东（房源所有者）  
**前置条件：** review_status 为 draft 或 rejected

#### 2. 取消发布
```http
POST /api/v1/properties/{property_id}/unpublish
```
**功能：** 房东主动将已发布的房源设为未发布  
**权限：** 房东（房源所有者）  
**前置条件：** review_status 为 approved，status 不为 rented/maintenance  
**效果：** status 变为 unpublished，审核状态保持 approved

#### 3. 发布房源
```http
POST /api/v1/properties/{property_id}/republish
```
**功能：** 房东将未发布的房源重新发布  
**权限：** 房东（房源所有者）  
**前置条件：** review_status 为 approved，status 为 unpublished  
**效果：** status 变为 published

#### 4. 管理员强制下架
```http
POST /api/v1/properties/{property_id}/unpublish
```
**功能：** 管理员强制下架房源  
**权限：** 管理员  
**前置条件：** status 不为 rented/maintenance  
**效果：** 
- status 变为 unpublished（未发布）
- review_status 变为 draft（草稿）
- 房东可以修改房源信息后重新提交审核

### 修改接口

#### 1. 创建房源
```http
POST /api/v1/properties/
```
**变更：** 创建后状态为 `draft`（原来是 `pending`）

#### 2. 更新房源
```http
PUT /api/v1/properties/{property_id}
```
**变更：**
- 增加了基于状态的字段修改限制
- 修改核心字段时自动将审核状态转为 pending，等待重新审核
- 已出租/维修中状态下只能修改描述

#### 3. 审核房源
```http
PUT /api/v1/properties/{property_id}/review
```
**变更：**
- 支持自动从 pending 转为 reviewing
- 审核通过后自动设置为 published 状态
- 拒绝时必须提供原因

### 查询接口变更

#### 房源列表
```http
GET /api/v1/properties/
```
**变更：**
- 普通用户（租客）只能看到 `review_status=approved` 且 `status=published` 的房源
- 管理员可以看到所有状态的房源
- 房东通过 `/my` 接口查看自己的所有房源

## 📊 业务流程示例

### 场景1：房东首次发布房源

1. 房东创建房源 → 状态：`draft`
2. 房东确认信息无误，点击"提交审核" → 状态：`pending`
3. 管理员开始审核 → 状态：`reviewing`
4. 管理员审核通过 → 状态：`approved` + `published`（自动发布）
5. 房源对租客可见

### 场景2：房东临时取消发布

1. 房源状态：`approved` + `published`
2. 房东点击"取消发布" → 状态：`approved` + `unpublished`
3. 房源对租客不可见
4. 房东可随时点击"发布" → 状态：`approved` + `published`

### 场景3：修改核心信息

1. 房源状态：`approved` + `published`
2. 房东修改租金 → 系统允许修改，但自动将审核状态转为 `pending`
3. 房源对租客不可见（因为审核状态不是 approved）
4. 房东点击"提交审核" → 状态：`pending`（如果还未提交）
5. 管理员重新审核 → 状态：`approved` + `published`

### 场景4：审核被拒后重新申请

1. 房源状态：`rejected`
2. 房东根据审核意见修改房源信息
3. 房东点击"提交审核" → 状态：`pending`
4. 管理员重新审核

### 场景5：管理员下架房源

1. 房源状态：`approved` + `published`
2. 管理员执行下架操作（提供原因）→ 状态：`draft` + `unpublished`
3. 房源对租客不可见
4. 房东收到下架通知，查看原因
5. 房东修改房源信息
6. 房东点击"提交审核" → 状态：`pending` + `unpublished`
7. 管理员重新审核 → 状态：`approved` + `published`

## 🗄️ 数据库迁移

执行以下SQL脚本进行数据库升级：

```bash
mysql -u root -p house_rental < doc/migration_property_enhancement.sql
```

**注意：** 
- 迁移前请备份数据库
- 现有数据的处理策略需要根据实际情况调整（见SQL文件中的注释部分）

## ✅ 测试清单

### 功能测试
- [ ] 房东创建房源后状态为 draft
- [ ] 房东可以提交草稿房源审核
- [ ] 被拒绝的房源可以重新提交审核
- [ ] 审核通过后房源自动发布
- [ ] 房东可以取消发布房源
- [ ] 房东可以重新发布已取消的房源
- [ ] 管理员可以强制下架房源
- [ ] 租客只能看到已发布且审核通过的房源
- [ ] 修改核心字段时提示需要重新审核
- [ ] 已出租房源只能修改描述

### 边界测试
- [ ] 已出租房源不能取消发布
- [ ] 维修中房源不能暂停发布
- [ ] 审核中的房源只能修改非核心字段
- [ ] 拒绝审核时必须提供原因
- [ ] 重复提交审核的请求被正确处理

## 🚀 部署步骤

1. **备份数据库**
   ```bash
   mysqldump -u root -p house_rental > backup_before_migration.sql
   ```

2. **执行数据库迁移**
   ```bash
   mysql -u root -p house_rental < doc/migration_property_enhancement.sql
   ```

3. **重启后端服务**
   ```bash
   # 停止现有服务
   # 重新启动
   uvicorn app.main:app --host 0.0.0.0 --port 8018 --reload
   ```

4. **验证功能**
   - 登录管理员账号，检查房源列表
   - 登录房东账号，测试创建和提交流程
   - 登录租客账号，确认可见的房源正确

## 📝 后续优化建议

1. **前端适配**
   - 在房源详情页显示当前状态
   - 添加"提交审核"、"取消发布"、"发布"按钮
   - 根据状态动态显示可操作项
   - 修改核心字段时说明会自动转为待审核状态
   - 管理员下架后显示"修改后重新提交"提示

2. **消息通知**
   - 审核状态变更时发送站内消息
   - 房源即将到期时提醒房东
   - 管理员下架时通知房东原因

3. **数据统计**
   - 统计平均审核时长
   - 统计房源发布/下架频率
   - 分析审核通过率

4. **自动化**
   - 审核超时自动提醒管理员
   - 长期未发布的草稿自动清理
   - 合同到期后自动恢复房源状态

## ⚠️ 注意事项

1. **数据兼容性**：现有房源数据需要手动调整状态，建议执行迁移脚本后检查数据一致性
2. **API 变更**：前端需要同步更新以适配新的接口和状态逻辑（特别是 unpublish 接口从 PUT 改为 POST）
3. **权限控制**：确保所有新接口都有正确的权限验证
4. **审计日志**：所有状态变更都已记录审计日志，便于追溯
5. **核心字段修改**：房东修改核心字段后会自动转为待审核状态，无需手动提交

---

**版本：** v2.0  
**更新日期：** 2026-05-26  
**作者：** AI Assistant
