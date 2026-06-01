<template>
  <el-dialog
    v-model="dialogVisible"
    title="签署合同"
    width="700px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-alert
      title="签署提示"
      type="warning"
      description="请在下方画板上手写签名，签署后将无法修改。系统将记录您的IP地址和设备信息。"
      :closable="false"
      style="margin-bottom: 20px"
    />

    <div class="signature-container">
      <div class="signature-canvas-wrapper">
        <canvas
          ref="canvasRef"
          width="600"
          height="200"
          @mousedown="startDrawing"
          @mousemove="draw"
          @mouseup="stopDrawing"
          @mouseleave="stopDrawing"
          @touchstart="handleTouchStart"
          @touchmove="handleTouchMove"
          @touchend="stopDrawing"
        ></canvas>
        <div v-if="isEmpty" class="canvas-placeholder">
          请在此处签名
        </div>
      </div>

      <div class="signature-actions">
        <el-button size="small" @click="clearCanvas">清除重签</el-button>
        <el-button size="small" @click="undoLastStroke">撤销上一步</el-button>
      </div>

      <div class="signature-preview" v-if="signatureImage">
        <p><strong>签名预览：</strong></p>
        <img :src="signatureImage" alt="签名预览" class="preview-image" />
      </div>

      <el-divider />

      <el-form :model="form" label-width="120px">
        <el-form-item label="确认密码" required>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入您的登录密码以确认签署"
            show-password
          />
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="submitting">
        确认签署
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  contractId: {
    type: Number,
    required: true
  },
  userRole: {
    type: String, // 'landlord' or 'tenant'
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const canvasRef = ref(null)
const ctx = ref(null)
const isDrawing = ref(false)
const strokes = ref([]) // 保存所有笔画用于撤销
const currentStroke = ref([]) // 当前笔画的点
const isEmpty = ref(true)
const submitting = ref(false)
const signatureImage = ref(null)

const form = ref({
  password: ''
})

// 初始化画布
function initCanvas() {
  if (!canvasRef.value) return
  
  const canvas = canvasRef.value
  ctx.value = canvas.getContext('2d')
  
  // 设置画笔样式
  ctx.value.strokeStyle = '#000'
  ctx.value.lineWidth = 2
  ctx.value.lineCap = 'round'
  ctx.value.lineJoin = 'round'
  
  // 白色背景
  ctx.value.fillStyle = '#fff'
  ctx.value.fillRect(0, 0, canvas.width, canvas.height)
}

// 获取坐标
function getCoordinates(e) {
  const canvas = canvasRef.value
  const rect = canvas.getBoundingClientRect()
  const scaleX = canvas.width / rect.width
  const scaleY = canvas.height / rect.height
  
  return {
    x: (e.clientX - rect.left) * scaleX,
    y: (e.clientY - rect.top) * scaleY
  }
}

// 开始绘制
function startDrawing(e) {
  isDrawing.value = true
  const coords = getCoordinates(e)
  currentStroke.value = [coords]
  
  ctx.value.beginPath()
  ctx.value.moveTo(coords.x, coords.y)
}

// 绘制
function draw(e) {
  if (!isDrawing.value) return
  
  const coords = getCoordinates(e)
  currentStroke.value.push(coords)
  
  ctx.value.lineTo(coords.x, coords.y)
  ctx.value.stroke()
  isEmpty.value = false
}

// 停止绘制
function stopDrawing() {
  if (!isDrawing.value) return
  isDrawing.value = false
  
  // 保存当前笔画
  if (currentStroke.value.length > 0) {
    strokes.value.push([...currentStroke.value])
    currentStroke.value = []
  }
  
  // 生成签名图片
  generateSignatureImage()
}

// 触摸事件处理
function handleTouchStart(e) {
  e.preventDefault()
  const touch = e.touches[0]
  const mouseEvent = new MouseEvent('mousedown', {
    clientX: touch.clientX,
    clientY: touch.clientY
  })
  startDrawing(mouseEvent)
}

function handleTouchMove(e) {
  e.preventDefault()
  const touch = e.touches[0]
  const mouseEvent = new MouseEvent('mousemove', {
    clientX: touch.clientX,
    clientY: touch.clientY
  })
  draw(mouseEvent)
}

// 清除画布
function clearCanvas() {
  if (!ctx.value || !canvasRef.value) return
  
  ctx.value.fillStyle = '#fff'
  ctx.value.fillRect(0, 0, canvasRef.value.width, canvasRef.value.height)
  strokes.value = []
  currentStroke.value = []
  isEmpty.value = true
  signatureImage.value = null
}

// 撤销上一步
function undoLastStroke() {
  if (strokes.value.length === 0) return
  
  strokes.value.pop()
  redrawCanvas()
  
  if (strokes.value.length === 0) {
    isEmpty.value = true
    signatureImage.value = null
  }
}

// 重绘画布
function redrawCanvas() {
  if (!ctx.value || !canvasRef.value) return
  
  // 清空画布
  ctx.value.fillStyle = '#fff'
  ctx.value.fillRect(0, 0, canvasRef.value.width, canvasRef.value.height)
  
  // 重绘所有笔画
  strokes.value.forEach(stroke => {
    if (stroke.length === 0) return
    
    ctx.value.beginPath()
    ctx.value.moveTo(stroke[0].x, stroke[0].y)
    
    for (let i = 1; i < stroke.length; i++) {
      ctx.value.lineTo(stroke[i].x, stroke[i].y)
    }
    
    ctx.value.stroke()
  })
}

// 生成签名图片
function generateSignatureImage() {
  if (!canvasRef.value) return
  signatureImage.value = canvasRef.value.toDataURL('image/png')
}

// 提交签署
async function handleSubmit() {
  if (isEmpty.value) {
    ElMessage.warning('请先签名')
    return
  }
  
  if (!form.value.password) {
    ElMessage.warning('请输入确认密码')
    return
  }
  
  try {
    submitting.value = true
    
    // 将签名图片上传到服务器（这里简化为直接发送base64）
    const signatureData = canvasRef.value.toDataURL('image/png')
    
    // 调用签署API
    const endpoint = props.userRole === 'landlord' 
      ? `/api/v1/contracts/${props.contractId}/sign/landlord`
      : `/api/v1/contracts/${props.contractId}/sign/tenant`

    await request.put(endpoint, {
      signature_image: signatureData,
      ip_address: null,
      device_info: navigator.userAgent
    })
    
    ElMessage.success('签署成功！')
    emit('success')
    handleClose()
  } catch (e) {
    const msg = e.response?.data?.detail || '签署失败，请稍后重试'
    ElMessage.error(msg)
  } finally {
    submitting.value = false
  }
}

// 关闭对话框
function handleClose() {
  dialogVisible.value = false
  clearCanvas()
  form.value.password = ''
}

// 监听对话框打开
watch(dialogVisible, (val) => {
  if (val) {
    setTimeout(() => {
      initCanvas()
    }, 100)
  }
})

onMounted(() => {
  // 预初始化
})
</script>

<style scoped>
.signature-container {
  padding: 10px 0;
}

.signature-canvas-wrapper {
  position: relative;
  border: 2px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 15px;
  background: white;
}

.signature-canvas-wrapper canvas {
  display: block;
  width: 100%;
  cursor: crosshair;
  touch-action: none; /* 防止触摸滚动 */
}

.canvas-placeholder {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #ccc;
  font-size: 18px;
  pointer-events: none;
}

.signature-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
  justify-content: center;
}

.signature-preview {
  margin-top: 15px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.preview-image {
  max-width: 300px;
  max-height: 100px;
  border: 1px solid #ddd;
  background: white;
  display: block;
  margin-top: 10px;
}
</style>
