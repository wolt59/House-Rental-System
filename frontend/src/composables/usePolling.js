import { onUnmounted } from 'vue'

export function usePolling(callback, interval = 10000) {
  let timer = null

  function start() {
    stop()
    timer = setInterval(callback, interval)
  }

  function stop() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  onUnmounted(stop)

  return { start, stop }
}
