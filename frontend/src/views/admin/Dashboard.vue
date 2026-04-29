<template>
  <div class="page-container">
    <div class="page-header"><h2>数据统计面板</h2></div>

    <!-- 核心指标卡片 -->
    <div class="stat-cards" v-if="dashboard">
      <div class="stat-card primary">
        <div class="stat-icon"></div>
        <div class="stat-value">{{ dashboard.users?.total || 0 }}</div>
        <div class="stat-label">用户总数</div>
      </div>
      <div class="stat-card success">
        <div class="stat-icon">🏠</div>
        <div class="stat-value">{{ dashboard.properties?.total || 0 }}</div>
        <div class="stat-label">房源总数</div>
      </div>
      <div class="stat-card warning">
        <div class="stat-icon">📊</div>
        <div class="stat-value">{{ dashboard.properties?.occupancy_rate || 0 }}%</div>
        <div class="stat-label">出租率</div>
      </div>
      <div class="stat-card danger">
        <div class="stat-icon">💰</div>
        <div class="stat-value">¥{{ formatMoney(dashboard.payments?.total_rent_income || 0) }}</div>
        <div class="stat-label">租金总收入</div>
      </div>
      <div class="stat-card info">
        <div class="stat-icon">📝</div>
        <div class="stat-value">{{ dashboard.contracts?.active || 0 }}</div>
        <div class="stat-label">活跃合同</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">⏳</div>
        <div class="stat-value">{{ dashboard.payments?.pending || 0 }}</div>
        <div class="stat-label">待支付</div>
      </div>
    </div>

        <el-row :gutter="20" style="margin-top: 20px">
      <!-- 房源状态分布饼图 -->
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header><span>房源状态分布</span></template>
          <div ref="propertyStatusChart" style="height: 300px"></div>
        </el-card>
      </el-col>

      <!-- 用户角色分布饼图 -->
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header><span>用户角色分布</span></template>
          <div ref="userRoleChart" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <!-- 月度收入趋势折线图 -->
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header><span>月度租金收入趋势</span></template>
          <div ref="incomeChart" style="height: 350px"></div>
        </el-card>
      </el-col>

      <!-- 待处理事项 -->
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header><span>待处理事项</span></template>
          <div class="todo-list">
            <div class="todo-item">
              <span class="todo-icon">📅</span>
              <span class="todo-label">待处理预约</span>
              <span class="todo-value">{{ dashboard?.bookings?.pending || 0 }}</span>
            </div>
            <div class="todo-item">
              <span class="todo-icon">🔧</span>
              <span class="todo-label">待处理维修</span>
              <span class="todo-value">{{ dashboard?.maintenance?.open || 0 }}</span>
            </div>
            <div class="todo-item">
              <span class="todo-icon">⚠️</span>
              <span class="todo-label">待处理投诉</span>
              <span class="todo-value">{{ dashboard?.complaints?.open || 0 }}</span>
            </div>
            <div class="todo-item">
              <span class="todo-icon">💳</span>
              <span class="todo-label">待支付订单</span>
              <span class="todo-value">{{ dashboard?.payments?.pending || 0 }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getDashboard, getMonthlyIncome, getUserActivity, getPropertyStatus } from '../../api/stats'
import * as echarts from 'echarts'

const dashboard = ref(null)
const propertyStatusChart = ref(null)
const userRoleChart = ref(null)
const occupancyChart = ref(null)
const incomeChart = ref(null)

let propertyChartInstance = null
let userChartInstance = null
let occupancyChartInstance = null
let incomeChartInstance = null

function formatMoney(value) {
  return value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function initPropertyStatusChart(data) {
  if (!propertyChartInstance) {
    propertyChartInstance = echarts.init(propertyStatusChart.value)
  }

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}: {c}'
        },
        data: [
          { value: data.vacant, name: '空置', itemStyle: { color: '#909399' } },
          { value: data.rented, name: '已出租', itemStyle: { color: '#67c23a' } },
          { value: data.maintenance, name: '维修中', itemStyle: { color: '#e6a23c' } },
          { value: data.pending_review, name: '待审核', itemStyle: { color: '#f56c6c' } }
        ]
      }
    ]
  }

  propertyChartInstance.setOption(option)
}

function initUserRoleChart(data) {
  if (!userChartInstance) {
    userChartInstance = echarts.init(userRoleChart.value)
  }

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}人 ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}: {c}人'
        },
        data: [
          { value: data.role_distribution.tenant, name: '租客', itemStyle: { color: '#409eff' } },
          { value: data.role_distribution.landlord, name: '房东', itemStyle: { color: '#67c23a' } },
          { value: data.role_distribution.admin, name: '管理员', itemStyle: { color: '#e6a23c' } }
        ]
      }
    ]
  }

  userChartInstance.setOption(option)
}

function initOccupancyChart(rate) {
  if (!occupancyChartInstance) {
    occupancyChartInstance = echarts.init(occupancyChart.value)
  }

  const option = {
    series: [
      {
        type: 'gauge',
        startAngle: 200,
        endAngle: -20,
        min: 0,
        max: 100,
        splitNumber: 10,
        itemStyle: {
          color: '#58d9f9',
          shadowColor: 'rgba(0,138,255,0.45)',
          shadowBlur: 10,
          shadowOffsetX: 2,
          shadowOffsetY: 2
        },
        progress: {
          show: true,
          roundCap: true,
          width: 18
        },
        pointer: {
          icon: 'roundRect',
          length: '60%',
          width: 6,
          offsetCenter: [0, '-10%']
        },
        axisLine: {
          roundCap: true,
          lineStyle: {
            width: 18
          }
        },
        axisTick: {
          splitNumber: 2,
          lineStyle: {
            width: 2,
            color: '#999'
          }
        },
        splitLine: {
          length: 12,
          lineStyle: {
            width: 3,
            color: '#999'
          }
        },
        axisLabel: {
          distance: 25,
          color: '#999',
          fontSize: 12
        },
        title: {
          show: true,
          fontSize: 14,
          color: '#666',
          offsetCenter: [0, '30%']
        },
        detail: {
          valueAnimation: true,
          fontSize: 30,
          offsetCenter: [0, '0%'],
          formatter: '{value}%',
          color: 'inherit'
        },
        data: [
          {
            value: rate,
            name: '出租率'
          }
        ]
      }
    ]
  }

  occupancyChartInstance.setOption(option)
}

function initIncomeChart(data) {
  if (!incomeChartInstance) {
    incomeChartInstance = echarts.init(incomeChart.value)
  }

  const months = data.map(item => item.month)
  const amounts = data.map(item => item.amount)

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: '{b}<br/>收入：¥{c}'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: months
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '¥{value}'
      }
    },
    series: [
      {
        name: '租金收入',
        type: 'line',
        smooth: true,
        data: amounts,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.5)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
          ])
        },
        itemStyle: {
          color: '#409eff'
        },
        lineStyle: {
          width: 3
        }
      }
    ]
  }

  incomeChartInstance.setOption(option)
}

async function loadData() {
  try {
    const [dashData, incomeData, userData, propertyData] = await Promise.all([
      getDashboard(),
      getMonthlyIncome(),
      getUserActivity(),
      getPropertyStatus()
    ])

    dashboard.value = dashData

    setTimeout(() => {
      initPropertyStatusChart(propertyData)
      initUserRoleChart(userData)
      initOccupancyChart(dashData.properties?.occupancy_rate || 0)
      initIncomeChart(incomeData)
    }, 100)
  } catch (e) {
    console.error('加载数据失败:', e)
  }
}

onMounted(() => {
  loadData()

  window.addEventListener('resize', () => {
    propertyChartInstance?.resize()
    userChartInstance?.resize()
    occupancyChartInstance?.resize()
    incomeChartInstance?.resize()
  })
})

onUnmounted(() => {
  propertyChartInstance?.dispose()
  userChartInstance?.dispose()
  occupancyChartInstance?.dispose()
  incomeChartInstance?.dispose()
})
</script>

<style scoped>
.stat-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 20px;
  color: white;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-card.success {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.stat-card.warning {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-card.danger {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.stat-card.info {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon {
  font-size: 32px;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

.chart-card {
  margin-bottom: 20px;
}

.todo-list {
  padding: 10px;
}

.todo-item {
  display: flex;
  align-items: center;
  padding: 15px;
  margin-bottom: 10px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: all 0.3s;
}

.todo-item:hover {
  background: #e4e7ed;
  transform: translateX(5px);
}

.todo-icon {
  font-size: 24px;
  margin-right: 15px;
}

.todo-label {
  flex: 1;
  font-size: 16px;
  color: #606266;
}

.todo-value {
  font-size: 20px;
  font-weight: bold;
  color: #f56c6c;
}
</style>
