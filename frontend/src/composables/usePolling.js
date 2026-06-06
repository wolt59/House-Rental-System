import { ref, onUnmounted } from 'vue'

/**
 * 轮询 composable — 用于合同/列表页自动刷新
 * @param {Function} callback 每次轮询要执行的异步函数
 * @param {number} interval 轮询间隔（毫秒），默认 10000
 * @param {Object} options
 * @param {Function} options.shouldPoll 可选，返回 true 才继续轮询
 */
export function usePolling(callback, interval = 10000, options = {}) {
  const { shouldPoll } = options
  const isPolling = ref(false)
  let timer = null

  function start() {
    if (isPolling.value) return
    isPolling.value = true
    schedule()
  }

  function stop() {
    isPolling.value = false
    clearTimer()
  }

  function clearTimer() {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
  }

  async function schedule() {
    if (!isPolling.value) return
    clearTimer()

    // 检查是否应该继续轮询
    if (shouldPoll && !shouldPoll()) {
      stop()
      return
    }

    timer = setTimeout(async () => {
      if (!isPolling.value) return
      try {
        await callback()
      } catch (e) {
        console.error('轮询出错:', e)
      }
      if (isPolling.value) {
        schedule()
      }
    }, interval)
  }

  onUnmounted(stop)

  return { start, stop, isPolling }
}
