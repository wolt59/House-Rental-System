<template>
  <div class="page-container">
    <div class="page-header"><h2>我的数据面板</h2></div>

    <!-- 核心指标 -->
    <div class="stat-cards" v-if="dashboard">
      <div class="stat-card primary">
        <div class="stat-icon"></div>
        <div class="stat-value">{{ dashboard.properties?.total || 0 }}</div>
        <div class="stat-label">房源总数</div>
      </div>
      <div class="stat-card success">
        <div class="stat-icon">✅</div>
        <div class="stat-value">{{ dashboard.properties?.rented || 0 }}</div>
        <div class="stat-label">已出租</div>
      </div>
      <div class="stat-card warning">
        <div class="stat-icon">📊</div>
        <div class="stat-value">{{ dashboard.properties?.occupancy_rate || 0 }}%</div>
        <div class="stat-label">出租率</div>
      </div>
      <div class="stat-card danger">
        <div class="stat-icon">💰</div>
        <div class="stat-value">¥{{ formatMoney(dashboard.income?.total || 0) }}</div>
        <div class="stat-label">总收入</div>
      </div>
    </div>

    <!-- 图表区域 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <!-- 收入趋势 -->
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header><span>月度收入趋势</span></template>
          <div ref="incomeChart" style="height: 350px"></div>
        </el-card>
      </el-col>

      <!-- 房源状态 -->
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header><span>房源状态分布</span></template>
          <div ref="propertyChart" style="height: 350px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <!-- 待处理事项 -->
      <el-col :span="24">
        <el-card class="chart-card">
          <template #header><span>待处理事项</span></template>
          <el-row :gutter="20">
            <el-col :span="6">
              <div class="todo-item-large">
                <div class="todo-icon">📅</div>
                <div class="todo-info">
                  <div class="todo-label">待确认预约</div>
                  <div class="todo-value">{{ dashboard?.bookings?.pending || 0 }}</div>
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="todo-item-large">
                <div class="todo-icon">🔧</div>
                <div class="todo-info">
                  <div class="todo-label">待处理维修</div>
                  <div class="todo-value">{{ dashboard?.maintenance?.open || 0 }}</div>
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="todo-item-large">
                <div class="todo-icon">⚠️</div>
                <div class="todo-info">
                  <div class="todo-label">待处理投诉</div>
                  <div class="todo-value">{{ dashboard?.complaints?.open || 0 }}</div>
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="todo-item-large">
                <div class="todo-icon">📋</div>
                <div class="todo-info">
                  <div class="todo-label">活跃合同</div>
                  <div class="todo-value">{{ dashboard?.contracts?.active || 0 }}</div>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getLandlordDashboard, getLandlordMonthlyIncome } from '../../api/stats'
import * as echarts from 'echarts'

const dashboard = ref(null)
const incomeChart = ref(null)
const propertyChart = ref(null)

let incomeChartInstance = null
let propertyChartInstance = null

function formatMoney(value) {
  return value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
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
            { offset: 0, color: 'rgba(103, 194, 58, 0.5)' },
            { offset: 1, color: 'rgba(103, 194, 58, 0.05)' }
          ])
        },
        itemStyle: {
          color: '#67c23a'
        },
        lineStyle: {
          width: 3
        }
      }
    ]
  }

  incomeChartInstance.setOption(option)
}

function initPropertyChart(data) {
  if (!propertyChartInstance) {
    propertyChartInstance = echarts.init(propertyChart.value)
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
          formatter: '{b}: {c}套'
        },
        data: [
          { value: data.vacant, name: '空置', itemStyle: { color: '#909399' } },
          { value: data.rented, name: '已出租', itemStyle: { color: '#67c23a' } }
        ]
      }
    ]
  }

  propertyChartInstance.setOption(option)
}

async function loadData() {
  try {
    const [dashData, incomeData] = await Promise.all([
      getLandlordDashboard(),
      getLandlordMonthlyIncome()
    ])

    dashboard.value = dashData

    setTimeout(() => {
      initIncomeChart(incomeData)
      initPropertyChart(dashData.properties)
    }, 100)
  } catch (e) {
    console.error('加载数据失败:', e)
  }
}

onMounted(() => {
  loadData()

  window.addEventListener('resize', () => {
    incomeChartInstance?.resize()
    propertyChartInstance?.resize()
  })
})

onUnmounted(() => {
  incomeChartInstance?.dispose()
  propertyChartInstance?.dispose()
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

.todo-item-large {
  display: flex;
  align-items: center;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 12px;
  transition: all 0.3s;
}

.todo-item-large:hover {
  background: #e4e7ed;
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.todo-icon {
  font-size: 36px;
  margin-right: 15px;
}

.todo-info {
  flex: 1;
}

.todo-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 5px;
}

.todo-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}
</style>
