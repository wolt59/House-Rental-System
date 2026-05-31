# 电子合同系统 API 完整指南

## 📋 API 端点总览

### 1. 合约申请 API (`/api/v1/contract-applications`)

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/` | 创建合约申请 | 租客 |
| GET | `/` | 获取申请列表 | 所有角色（自动过滤） |
| GET | `/{id}` | 获取申请详情 | 相关用户 |
| POST | `/{id}/approve` | 同意申请 | 房东 |
| POST | `/{id}/reject` | 拒绝申请 | 房东 |
| POST | `/{id}/cancel` | 取消申请 | 租客 |

---

### 2. 合同管理 API (`/api/v1/contracts`)

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/` | 创建合同 | 房东 |
| POST | `/auto-create` | 自动创建合同 | 租客 |
| GET | `/` | 获取合同列表 | 所有角色 |
| GET | `/{id}` | 获取合同详情 | 相关用户 |
| PUT | `/{id}` | 更新合同 | 房东（DRAFT状态） |
| PUT | `/{id}/sign/landlord` | 房东签署 | 房东 |
| PUT | `/{id}/sign/tenant` | 租客签署 | 租客 |
| PUT | `/{id}/withdraw/landlord` | 房东撤回签署 | 房东 |
| PUT | `/{id}/withdraw/tenant` | 租客撤回签署 | 租客 |
| PUT | `/{id}/reject` | 拒绝合同 | 租客 |
| PUT | `/{id}/terminate` | 终止合同 | 相关用户 |

---

### 3. 合同变更 API (`/api/v1/contract-changes`)

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/` | 发起变更申请 | 合同双方 |
| GET | `/` | 获取变更列表 | 合同双方 |
| GET | `/{id}` | 获取变更详情 | 合同双方 |
| POST | `/{id}/approve` | 同意变更 | 合同另一方 |
| POST | `/{id}/reject` | 拒绝变更 | 合同另一方 |

---

### 4. 提前解约 API (`/api/v1/contract-terminations`)

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/` | 发起解约申请 | 合同双方 |
| GET | `/` | 获取解约列表 | 合同双方 |
| GET | `/{id}` | 获取解约详情 | 合同双方 |
| POST | `/{id}/approve` | 同意解约 | 合同另一方 |
| POST | `/{id}/reject` | 拒绝解约 | 合同另一方 |

---

## 🔧 API 使用示例

### 1. 创建合约申请

**请求**:
```bash
POST /api/v1/contract-applications/
Authorization: Bearer {tenant_token}
Content-Type: application/json

{
  "booking_id": 1,
  "start_date": "2026-06-01T00:00:00",
  "end_date": "2027-06-01T00:00:00",
  "payment_method": "押一付三",
  "additional_notes": "希望能尽快入住，房屋状况良好"
}
```

**响应** (201 Created):
```json
{
  "id": 1,
  "booking_id": 1,
  "property_id": 5,
  "tenant_id": 3,
  "landlord_id": 2,
  "start_date": "2026-06-01T00:00:00",
  "end_date": "2027-06-01T00:00:00",
  "payment_method": "押一付三",
  "additional_notes": "希望能尽快入住，房屋状况良好",
  "status": "apply_pending",
  "landlord_response": null,
  "responded_at": null,
  "contract_id": null,
  "cancelled_at": null,
  "created_at": "2026-05-30T10:30:00",
  "updated_at": "2026-05-30T10:30:00"
}
```

---

### 2. 房东同意合约申请

**请求**:
```bash
POST /api/v1/contract-applications/1/approve
Authorization: Bearer {landlord_token}
Content-Type: application/json

{
  "approved": true,
  "response": "同意您的申请，请联系我签署合同"
}
```

**响应**:
```json
{
  "id": 1,
  "status": "apply_approved",
  "contract_id": 10,
  "landlord_response": "同意您的申请，请联系我签署合同",
  "responded_at": "2026-05-30T14:20:00",
  ...
}
```

---

### 3. 房东签署合同

**请求**:
```bash
PUT /api/v1/contracts/10/sign/landlord
Authorization: Bearer {landlord_token}
Content-Type: application/json

{
  "signature_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "password": "landlord_password"
}
```

**响应**:
```json
{
  "id": 10,
  "status": "part_signed",
  "signed_by_landlord": true,
  "landlord_signed_at": "2026-05-30T15:00:00",
  "landlord_sign_ip": "127.0.0.1",
  "landlord_signature_image": "/uploads/signatures/xxx.png",
  ...
}
```

---

### 4. 租客签署合同

**请求**:
```bash
PUT /api/v1/contracts/10/sign/tenant
Authorization: Bearer {tenant_token}
Content-Type: application/json

{
  "signature_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "password": "tenant_password"
}
```

**响应**:
```json
{
  "id": 10,
  "status": "active",
  "signed_by_tenant": true,
  "tenant_signed_at": "2026-05-30T16:00:00",
  "tenant_sign_ip": "127.0.0.1",
  "tenant_signature_image": "/uploads/signatures/yyy.png",
  ...
}
```

**注意**: 双方都签署后，合同状态自动变为 `active`，房源状态变为 `RENTED`。

---

### 5. 发起合同变更申请

**请求**:
```bash
POST /api/v1/contract-changes/
Authorization: Bearer {tenant_or_landlord_token}
Content-Type: application/json

{
  "contract_id": 10,
  "change_reason": "希望调整租金支付方式",
  "change_fields": {
    "payment_method": {
      "old_value": "押一付三",
      "new_value": "押一付一"
    },
    "monthly_rent": {
      "old_value": 3000,
      "new_value": 3200
    }
  }
}
```

**响应** (201 Created):
```json
{
  "id": 1,
  "contract_id": 10,
  "initiator_id": 3,
  "change_reason": "希望调整租金支付方式",
  "change_fields": {
    "payment_method": {"old_value": "押一付三", "new_value": "押一付一"},
    "monthly_rent": {"old_value": 3000, "new_value": 3200}
  },
  "status": "pending",
  "responder_id": null,
  "response_opinion": null,
  "responded_at": null,
  "created_at": "2026-06-15T10:00:00",
  "updated_at": "2026-06-15T10:00:00"
}
```

---

### 6. 同意合同变更

**请求**:
```bash
POST /api/v1/contract-changes/1/approve
Authorization: Bearer {other_party_token}
Content-Type: application/json

{
  "opinion": "同意变更，已协商好新的支付方式"
}
```

**响应**:
```json
{
  "id": 1,
  "status": "approved",
  "responder_id": 2,
  "response_opinion": "同意变更，已协商好新的支付方式",
  "responded_at": "2026-06-15T14:30:00",
  ...
}
```

**注意**: 同意后，合同会自动更新相应字段，状态从 `CHANGE_NEGOTIATING` 恢复为 `ACTIVE`。

---

### 7. 发起提前解约申请

**请求**:
```bash
POST /api/v1/contract-terminations/
Authorization: Bearer {tenant_or_landlord_token}
Content-Type: application/json

{
  "contract_id": 10,
  "termination_reason": "工作调动需要离开本市",
  "expected_termination_date": "2026-08-31T00:00:00",
  "penalty_amount": 3000,
  "deposit_handling": "押金作为违约金，不再退还",
  "additional_notes": "希望能协商一个双方都能接受的方案"
}
```

**响应** (201 Created):
```json
{
  "id": 1,
  "contract_id": 10,
  "initiator_id": 3,
  "termination_reason": "工作调动需要离开本市",
  "expected_termination_date": "2026-08-31T00:00:00",
  "penalty_amount": 3000,
  "deposit_handling": "押金作为违约金，不再退还",
  "additional_notes": "希望能协商一个双方都能接受的方案",
  "status": "pending",
  "created_at": "2026-07-15T10:00:00",
  "updated_at": "2026-07-15T10:00:00"
}
```

---

### 8. 同意提前解约

**请求**:
```bash
POST /api/v1/contract-terminations/1/approve
Authorization: Bearer {other_party_token}
Content-Type: application/json

{
  "opinion": "同意解约，请按约定处理押金"
}
```

**响应**:
```json
{
  "id": 1,
  "status": "approved",
  "responder_id": 2,
  "response_opinion": "同意解约，请按约定处理押金",
  "responded_at": "2026-07-15T14:00:00",
  ...
}
```

**注意**: 同意后，合同状态变为 `TERMINATED`，房源状态恢复为 `VACANT`。

---

## 📊 状态流转图

### 合约申请状态流转
```
APPLY_PENDING (待处理)
  ├─→ APPLY_APPROVED (已同意) → 生成DRAFT合同
  ├─→ APPLY_REJECTED (已拒绝)
  └─→ APPLY_CANCELLED (已取消)
```

### 合同状态流转
```
DRAFT (草稿)
  ↓ 提交签署
PENDING_SIGN (待签署)
  ↓ 一方签署
PART_SIGNED (部分签署)
  ↓ 双方签署
ACTIVE (生效中)
  ├─→ CHANGE_NEGOTIATING (变更协商中) → ACTIVE
  ├─→ TERMINATE_NEGOTIATING (解约协商中) → TERMINATED
  ├─→ EXPIRED (已过期)
  └─→ CANCELLED (已取消)
```

---

## 🔐 权限控制规则

### 合约申请
- **创建**: 仅 TENANT 角色，且必须是看房记录的租客
- **查看**: 仅租客、房东、管理员
- **处理**: 仅房东（landlord_id 匹配）
- **取消**: 仅租客（tenant_id 匹配）

### 合同签署
- **房东签署**: 仅 landlord_id 匹配的用户
- **租客签署**: 仅 tenant_id 匹配的用户
- **撤回**: 仅签署方本人，且合同未生效

### 合同变更/解约
- **发起**: 合同任一方（tenant_id 或 landlord_id）
- **审批**: 仅合同另一方（发起人不能审批自己的申请）
- **查看**: 仅合同双方和管理员

---

## ⚠️ 业务校验规则

### 创建合约申请
1. ✓ 看房记录必须存在且属于该租客
2. ✓ 看房状态必须是 `completed`
3. ✓ 同一租客对同一房源不能有重复的未完成申请
4. ✓ 房源不能已有活跃合同

### 签署合同
1. ✓ 用户必须有签署权限
2. ✓ 合同状态不能是已结束的状态
3. ✓ 不能重复签署
4. ✓ 双方都签署后自动生效

### 合同变更
1. ✓ 合同状态必须是 `ACTIVE`
2. ✓ 不能有 pending 状态的变更申请
3. ✓ 变更字段必须在允许范围内

### 提前解约
1. ✓ 合同状态必须是 `ACTIVE`
2. ✓ 期望解约日期必须晚于当前日期
3. ✓ 不能有 pending 状态的解约申请

---

## 🧪 Postman 测试集合

您可以导入以下 JSON 到 Postman 进行测试：

```json
{
  "info": {
    "name": "Electronic Contract System API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Contract Applications",
      "item": [
        {
          "name": "Create Application",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{tenant_token}}"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"booking_id\": 1,\n  \"start_date\": \"2026-06-01T00:00:00\",\n  \"end_date\": \"2027-06-01T00:00:00\",\n  \"payment_method\": \"押一付三\"\n}"
            },
            "url": {
              "raw": "{{base_url}}/api/v1/contract-applications/",
              "host": ["{{base_url}}"],
              "path": ["api", "v1", "contract-applications", ""]
            }
          }
        }
      ]
    }
  ]
}
```

---

## 📝 前端集成建议

### 1. 合约申请流程
```javascript
// 1. 租客提交申请
const response = await request.post('/contract-applications/', {
  booking_id: bookingId,
  start_date: startDate,
  end_date: endDate,
  payment_method: paymentMethod
})

// 2. 房东查看申请列表
const applications = await request.get('/contract-applications/')

// 3. 房东同意申请
await request.post(`/contract-applications/${id}/approve`, {
  approved: true,
  response: '同意'
})

// 4. 跳转到合同编辑页面
router.push(`/landlord/contract-edit/${contractId}`)
```

### 2. 合同签署流程
```vue
<template>
  <ContractDocument 
    :contract="contract"
    :can-sign="canSign"
    @sign="showSignatureDialog"
  />
  
  <SignaturePad
    v-model="signatureVisible"
    :contract-id="contract.id"
    :user-role="userRole"
    @success="handleSignSuccess"
  />
</template>

<script setup>
import ContractDocument from '../views/common/ContractDocument.vue'
import SignaturePad from '../components/contract/SignaturePad.vue'

const signatureVisible = ref(false)

function showSignatureDialog() {
  signatureVisible.value = true
}

async function handleSignSuccess() {
  // 刷新合同数据
  await loadContract()
  ElMessage.success('签署成功！')
}
</script>
```

---

## 🎯 下一步开发建议

1. **房东处理申请页面** - 查看和审批合约申请
2. **合同编辑页面** - 使用 ContractDocument 组件编辑 DRAFT 合同
3. **合同详情页** - 展示合同正文和签署状态
4. **变更/解约前端组件** - 发起和处理变更、解约申请
5. **消息通知集成** - 申请、签署、变更等事件通知

---

## 📞 技术支持

如有问题，请检查：
1. Swagger 文档：http://localhost:8000/docs
2. 后端日志输出
3. 浏览器控制台错误
4. 数据库表结构是否正确迁移
