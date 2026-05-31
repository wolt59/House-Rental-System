# 电子合同系统增强实施指南

## 概述
本文档描述了电子合同系统的完整增强功能，包括合约申请、合同签署、合同变更和提前解约功能。

## 已完成的后端工作

### 1. 数据库模型 (Models)
已创建/更新以下模型文件：

- **app/models/contract_application.py** - 合约申请表
- **app/models/contract.py** - 扩展合同表（新增字段）
- **app/models/contract_change_request.py** - 合同变更申请表
- **app/models/contract_termination_request.py** - 提前解约申请表
- **app/models/user.py** - 添加合约申请关系
- **app/models/booking.py** - 添加合约申请关系
- **app/models/property.py** - 添加合约申请关系

### 2. 枚举定义 (Enums)
已更新 **app/core/enums.py**：
- `ContractApplicationStatus` - 合约申请状态
- `ContractStatus` - 合同状态（新增PART_SIGNED、CHANGE_NEGOTIATING、TERMINATE_NEGOTIATING等）

### 3. Schema定义
已创建以下schema文件：
- **app/schemas/contract_application.py** - 合约申请Schema
- **app/schemas/contract_change_request.py** - 合同变更Schema
- **app/schemas/contract_termination_request.py** - 提前解约Schema

### 4. CRUD操作
已创建以下CRUD文件：
- **app/crud/crud_contract_application.py** - 合约申请CRUD
- **app/crud/crud_contract_change.py** - 合同变更和提前解约CRUD

### 5. 数据库迁移
已创建迁移脚本：
- **doc/migration_contract_system_enhancement.sql**

## 待完成的工作

### 后端部分

#### 1. 扩展合同CRUD操作 (task_8)
需要在 **app/crud/crud_contract.py** 中添加：
- 合同签署功能（房东/租客）
- 合同内容锁定机制
- 合同快照生成（HTML/PDF）
- 合同编辑权限控制
- 合同状态自动过期检查

关键函数示例：
```python
def sign_contract(db: Session, contract: Contract, user_id: int, user_role: str, 
                  signature_image: str = None, ip_address: str = None, device_info: str = None) -> Contract:
    """签署合同"""
    # 验证签署权限
    # 记录签署信息
    # 更新合同状态
    # 如果双方都签署，生成快照并更新房源状态
    
def lock_contract_content(db: Session, contract: Contract) -> Contract:
    """锁定合同内容（任一方签署后调用）"""
    
def generate_contract_snapshot(db: Session, contract: Contract) -> str:
    """生成合同HTML/PDF快照"""
    
def update_contract_editable_fields(db: Session, contract: Contract, update_data: dict) -> Contract:
    """更新合同可编辑字段（仅DRAFT状态）"""
```

#### 2. API端点实现

需要创建/更新以下API端点：

**A. 合约申请API (app/api/api_v1/endpoints/contract_applications.py)**
```python
POST   /contract-applications/          # 创建合约申请
GET    /contract-applications/          # 列表（支持tenant/landlord过滤）
GET    /contract-applications/{id}      # 详情
POST   /contract-applications/{id}/approve   # 房东同意
POST   /contract-applications/{id}/reject    # 房东拒绝
POST   /contract-applications/{id}/cancel    # 租客取消
```

**B. 合同API扩展 (app/api/api_v1/endpoints/contracts.py)**
```python
POST   /contracts/{id}/sign           # 签署合同
POST   /contracts/{id}/edit           # 编辑合同（仅DRAFT状态）
GET    /contracts/{id}/snapshot       # 获取合同快照
POST   /contracts/{id}/cancel         # 取消合同
GET    /contracts/{id}/check-expired  # 检查是否过期
```

**C. 合同变更API (app/api/api_v1/endpoints/contract_changes.py)**
```python
POST   /contract-changes/             # 创建变更申请
GET    /contract-changes/             # 列表
GET    /contract-changes/{id}         # 详情
POST   /contract-changes/{id}/approve # 同意变更
POST   /contract-changes/{id}/reject  # 拒绝变更
```

**D. 提前解约API (app/api/api_v1/endpoints/contract_terminations.py)**
```python
POST   /contract-terminations/        # 创建解约申请
GET    /contract-terminations/        # 列表
GET    /contract-terminations/{id}    # 详情
POST   /contract-terminations/{id}/approve  # 同意解约
POST   /contract-terminations/{id}/reject   # 拒绝解约
```

#### 3. 注册API路由
在 **app/api/api_v1/api.py** 中注册新端点

### 前端部分

#### 1. API封装 (frontend/src/api/)
创建以下API文件：
- **contractApplication.js** - 合约申请API
- **contractChange.js** - 合同变更API
- **contractTermination.js** - 提前解约API

#### 2. 组件开发

**A. 合约申请表单组件**
位置：`frontend/src/views/tenant/ContractApplication.vue` 或在PropertyDetail中集成
功能：
- 在看房完成后显示"发起合约申请"按钮
- 表单字段：租赁开始/结束日期、付款方式、补充说明
- 提交后显示申请状态

**B. 合同正文展示组件（核心）**
位置：`frontend/src/components/contract/ContractDocument.vue`
要求：
- **不要做成普通表单**，要像Word/PDF合同一样展示
- 按章节排版（第一条、第二条...）
- 可编辑字段使用内联输入控件嵌入正文
- 不可编辑字段显示为普通文本
- 签署后所有字段变为只读

示例样式：
```vue
<template>
  <div class="contract-document">
    <h1>房屋租赁合同</h1>
    <p>合同编号：{{ contract.contract_no }}</p>
    
    <section>
      <h2>第一条 租赁双方信息</h2>
      <p>甲方（出租方）：{{ landlord.full_name }}</p>
      <p>身份证号码：{{ landlord.id_card_number }}</p>
      <p>乙方（承租方）：{{ tenant.full_name }}</p>
      <p>身份证号码：{{ tenant.id_card_number }}</p>
    </section>
    
    <section>
      <h2>第四条 租金及支付方式</h2>
      <p>
        该房屋月租金为人民币 
        <input v-if="canEdit" v-model="contract.monthly_rent" type="number" class="inline-input" />
        <span v-else>{{ contract.monthly_rent }}</span>
        元
      </p>
    </section>
    
    <!-- 签署区 -->
    <section class="signature-section">
      <div class="signature-box">
        <p>甲方（出租方）电子签名：</p>
        <button v-if="!contract.signed_by_landlord && isLandlord" @click="signContract">
          签署合同
        </button>
        <img v-else :src="contract.landlord_signature_image" alt="房东签名" />
      </div>
    </section>
  </div>
</template>
```

**C. 合同签署组件**
位置：`frontend/src/components/contract/SignaturePad.vue`
功能：
- 手写签名板（使用canvas）
- 或点击确认签署（简化版）
- 上传签名图片

**D. 合同变更申请组件**
位置：`frontend/src/views/common/ContractChangeRequest.vue`
功能：
- 选择要变更的字段
- 填写原值和新值
- 填写变更原因

**E. 提前解约申请组件**
位置：`frontend/src/views/common/ContractTerminationRequest.vue`
功能：
- 填写解约原因
- 期望解约日期
- 违约金金额
- 押金处理说明

#### 3. 页面集成

**A. 租客端**
- 在看房记录列表/详情页添加"发起合约申请"入口
- 在合同列表页显示合同状态和操作按钮
- 合同详情页集成合同正文展示组件

**B. 房东端**
- 在Dashboard显示待处理的合约申请
- 合约申请列表页（同意/拒绝操作）
- 合同管理页（查看、签署、发起变更/解约）

**C. 合同详情页**
根据合同状态显示不同操作：
- DRAFT: 显示编辑按钮
- PENDING_SIGN: 显示签署按钮
- PART_SIGNED: 显示"等待对方签署"
- ACTIVE: 显示"发起变更"、"发起解约"按钮
- CHANGE_NEGOTIATING: 显示变更协商进度
- TERMINATE_NEGOTIATING: 显示解约协商进度

## 业务规则实现要点

### 1. 合约申请
- ✅ 只有看房状态为COMPLETED才能发起
- ✅ 同一租客对同一房源不能有重复的未完成申请
- ✅ 房东同意后自动生成DRAFT状态的合同

### 2. 合同签署
- ⏳ 任一方签署后，合同状态变为PART_SIGNED
- ⏳ 任一方签署后，合同内容锁定（不可编辑）
- ⏳ 双方签署后，状态变为ACTIVE，房源状态改为RENTED
- ⏳ 签署时记录IP、设备信息、签名图片

### 3. 合同编辑
- ⏳ 仅DRAFT状态可编辑
- ⏳ 只能编辑允许的字段（租金、日期、付款方式等）
- ⏳ 不能编辑：合同编号、房屋地址、双方身份信息

### 4. 合同变更
- ⏳ 仅ACTIVE状态可发起变更
- ⏳ 只能变更允许字段
- ⏳ 需要双方同意才生效
- ⏳ 保留原合同内容和变更记录

### 5. 提前解约
- ⏳ 仅ACTIVE状态可发起解约
- ⏳ 需要双方同意
- ⏳ 同意后合同状态变为TERMINATED
- ⏳ 房源状态恢复为VACANT

## 下一步行动

### 立即执行
1. **执行数据库迁移**
   ```bash
   mysql -u root -p your_database < doc/migration_contract_system_enhancement.sql
   ```

2. **实现合同签署CRUD功能** (task_8)
   - 在crud_contract.py中添加签署相关函数

3. **创建API端点** (task_11-14)
   - 合约申请API
   - 合同签署API
   - 合同变更API
   - 提前解约API

### 前端开发
4. **创建API封装** (frontend/src/api/)
5. **开发合同正文展示组件** (最关键)
6. **集成到现有页面**

## 技术注意事项

### 1. 合同快照生成
建议使用以下方案之一：
- **html2pdf.js** (前端生成PDF)
- **weasyprint** (Python后端生成PDF)
- **puppeteer** (Node.js生成PDF)

### 2. 电子签名
简化方案：
- 用户上传签名图片
- 或使用文字确认："本人确认签署此合同"

完整方案：
- 使用canvas实现手写签名
- 保存签名为PNG图片

### 3. 合同正文样式
CSS建议：
```css
.contract-document {
  max-width: 800px;
  margin: 0 auto;
  padding: 40px;
  font-family: "SimSun", "宋体", serif;
  line-height: 1.8;
  background: white;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

.inline-input {
  border: none;
  border-bottom: 1px solid #333;
  width: 150px;
  text-align: center;
  font-size: inherit;
  font-family: inherit;
}

.signature-section {
  margin-top: 60px;
  display: flex;
  justify-content: space-between;
}
```

## 测试清单

### 后端测试
- [ ] 合约申请创建（正常/异常场景）
- [ ] 房东同意/拒绝申请
- [ ] 合同签署流程
- [ ] 合同编辑权限控制
- [ ] 合同变更流程
- [ ] 提前解约流程
- [ ] 状态流转正确性

### 前端测试
- [ ] 合约申请表单提交
- [ ] 合同正文展示效果
- [ ] 内联编辑功能
- [ ] 签署功能
- [ ] 变更申请流程
- [ ] 解约申请流程

## 总结

目前已完成：
✅ 数据库模型设计
✅ 枚举定义
✅ Schema定义
✅ CRUD基础操作
✅ 数据库迁移脚本

待完成：
⏳ 合同签署CRUD扩展
⏳ API端点实现
⏳ 前端组件开发
⏳ 合同正文展示（重点）
⏳ 集成测试

预计剩余工作量：3-5天（取决于合同正文展示的复杂度）
