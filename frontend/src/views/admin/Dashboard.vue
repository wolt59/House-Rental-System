<template>
  <div class="page-container">
    <div class="page-header"><h2>数据统计面板</h2></div>

    <div class="stat-cards" v-if="dashboard">
      <div class="stat-card">
        <div class="stat-value">{{ dashboard.users?.total || 0 }}</div>
        <div class="stat-label">用户总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ dashboard.properties?.total || 0 }}</div>
        <div class="stat-label">房源总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ dashboard.properties?.approved || 0 }}</div>
        <div class="stat-label">已审核房源</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ dashboard.properties?.occupancy_rate || 0 }}%</div>
        <div class="stat-label">出租率</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ dashboard.contracts?.active || 0 }}</div>
        <div class="stat-label">活跃合同</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">¥{{ dashboard.payments?.total_rent_income || 0 }}</div>
        <div class="stat-label">租金总收入</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ dashboard.payments?.pending || 0 }}</div>
        <div class="stat-label">待支付</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ dashboard.bookings?.pending || 0 }}</div>
        <div class="stat-label">待处理预约</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ dashboard.maintenance?.open || 0 }}</div>
        <div class="stat-label">待处理维修</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ dashboard.complaints?.open || 0 }}</div>
        <div class="stat-label">待处理投诉</div>
      </div>
    </div>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header><span>房源状态分布</span></template>
          <div v-if="dashboard">
            <p>空置：{{ dashboard.properties?.vacant || 0 }} 套</p>
            <p>已出租：{{ dashboard.properties?.rented || 0 }} 套</p>
            <p>出租率：{{ dashboard.properties?.occupancy_rate || 0 }}%</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span>支付概况</span></template>
          <div v-if="dashboard">
            <p>总支付笔数：{{ dashboard.payments?.total || 0 }}</p>
            <p>已支付：{{ dashboard.payments?.paid || 0 }} 笔</p>
            <p>待支付：{{ dashboard.payments?.pending || 0 }} 笔</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getDashboard } from '../../api/stats'

const dashboard = ref(null)

onMounted(async () => {
  try {
    dashboard.value = await getDashboard()
  } catch (e) {}
})
</script>
