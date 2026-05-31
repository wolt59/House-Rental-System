<template>
  <div class="signature-pad-container">
    <div class="signature-header">
      <h3>{{ title }}</h3>
      <el-button size="small" @click="clearSignature" :disabled="!canDraw">
        清除
      </el-button>
    </div>
    
    <canvas
      ref="canvasRef"
      class="signature-canvas"
      :class="{ 'disabled': !canDraw }"
      @mousedown="startDrawing"
      @mousemove="draw"
      @mouseup="stopDrawing"
      @mouseleave="stopDrawing"
      @touchstart="handleTouchStart"
      @touchmove="handleTouchMove"
      @touchend="stopDrawing"
    ></canvas>
    
    <div class="signature-actions">
      <el-button type="primary" @click="confirmSignature" :disabled="isEmpty">
        确认签名
      </el-button>
      <el-button @click="$emit('cancel')">
        取消
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: '手写签名'
  },
  canDraw: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['confirm', 'cancel'])

const canvasRef = ref(null)
const isDrawing = ref(false)
const lastX = ref(0)
const lastY = ref(0)
const isEmpty = ref(true)

let ctx = null

onMounted(() => {
  initCanvas()
})

function initCanvas() {
  const canvas = canvasRef.value
  if (!canvas) return
  
  // 设置canvas尺寸
  canvas.width = canvas.offsetWidth
  canvas.height = canvas.offsetHeight
  
  ctx = canvas.getContext('2d')
  ctx.strokeStyle = '#000'
  ctx.lineWidth = 2
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
}

function getPos(e) {
  const canvas = canvasRef.value
  const rect = canvas.getBoundingClientRect()
  return {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top
  }
}

function getTouchPos(e) {
  const canvas = canvasRef.value
  const rect = canvas.getBoundingClientRect()
  const touch = e.touches[0]
  return {
    x: touch.clientX - rect.left,
    y: touch.clientY - rect.top
  }
}

function startDrawing(e) {
  if (!props.canDraw) return
  isDrawing.value = true
  const pos = getPos(e)
  lastX.value = pos.x
  lastY.value = pos.y
}

function draw(e) {
  if (!isDrawing.value || !props.canDraw) return
  
  const pos = getPos(e)
  ctx.beginPath()
  ctx.moveTo(lastX.value, lastY.value)
  ctx.lineTo(pos.x, pos.y)
  ctx.stroke()
  
  lastX.value = pos.x
  lastY.value = pos.y
  isEmpty.value = false
}

function stopDrawing() {
  isDrawing.value = false
}

function handleTouchStart(e) {
  e.preventDefault()
  if (!props.canDraw) return
  isDrawing.value = true
  const pos = getTouchPos(e)
  lastX.value = pos.x
  lastY.value = pos.y
}

function handleTouchMove(e) {
  e.preventDefault()
  if (!isDrawing.value || !props.canDraw) return
  
  const pos = getTouchPos(e)
  ctx.beginPath()
  ctx.moveTo(lastX.value, lastY.value)
  ctx.lineTo(pos.x, pos.y)
  ctx.stroke()
  
  lastX.value = pos.x
  lastY.value = pos.y
  isEmpty.value = false
}

function clearSignature() {
  const canvas = canvasRef.value
  if (!canvas) return
  
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  isEmpty.value = true
}

function confirmSignature() {
  if (isEmpty.value) return
  
  const canvas = canvasRef.value
  const dataUrl = canvas.toDataURL('image/png')
  emit('confirm', dataUrl)
}

defineExpose({
  clearSignature,
  initCanvas
})
</script>

<style scoped>
.signature-pad-container {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.signature-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.signature-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.signature-canvas {
  width: 100%;
  height: 200px;
  border: 2px solid #ddd;
  border-radius: 4px;
  cursor: crosshair;
  background: #fafafa;
  touch-action: none;
}

.signature-canvas.disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.signature-actions {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 15px;
}
</style>
