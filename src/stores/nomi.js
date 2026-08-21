import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useNomiStore = defineStore('nomi', () => {
  // AI 语音短语列表
  const aiPhrases = [
    "主人，我叫小圆，是你的智能小助手~",
    "主人，今天的订单都处理完了吗？",
    "今天又有什么新订单呀？",
    "需要我帮你查库存吗？",
    "闲着也是闲着，看看数据吧！",
    "随时准备接入 AI 大脑神经~",
    "累了就休息一下，喝口水吧~",
    "中固的产品最近卖得很火呢！",
    "发呆中... 随时可以戳我哦"
  ]

  // 状态
  const isMenuActive = ref(false)
  const speechBubbleContent = ref('')
  const showSpeechBubble = ref(false)
  const speechBubbleType = ref('text') // 'text' | 'filter'
  const filterType = ref('shipped') // 'shipped' | 'material'

  // 定时器
  let speechTimer = null
  let filterTimer = null

  // 切换菜单显示/隐藏
  const toggleMenu = () => {
    isMenuActive.value = !isMenuActive.value
  }

  // 关闭菜单
  const closeMenu = () => {
    isMenuActive.value = false
  }

  // 显示随机 AI 语音
  const showRandomSpeech = () => {
    if (showSpeechBubble.value) return

    const randomPhrase = aiPhrases[Math.floor(Math.random() * aiPhrases.length)]
    speechBubbleContent.value = randomPhrase
    speechBubbleType.value = 'text'
    showSpeechBubble.value = true

    if (speechTimer) clearTimeout(speechTimer)
    speechTimer = setTimeout(() => {
      hideSpeechBubble()
    }, 4000)
  }

  // 隐藏气泡
  const hideSpeechBubble = () => {
    showSpeechBubble.value = false
    speechBubbleContent.value = ''
    if (speechTimer) clearTimeout(speechTimer)
    if (filterTimer) clearTimeout(filterTimer)
  }

  // 显示日期筛选气泡
  const showDateFilterBubble = (type = 'shipped') => {
    filterType.value = type
    speechBubbleType.value = 'filter'
    showSpeechBubble.value = true
    startFilterTimer()
  }

  // 启动筛选气泡自动隐藏定时器
  const startFilterTimer = () => {
    if (filterTimer) clearTimeout(filterTimer)
    filterTimer = setTimeout(() => {
      hideSpeechBubble()
    }, 10000)
  }

  // 停止筛选气泡定时器
  const stopFilterTimer = () => {
    if (filterTimer) clearTimeout(filterTimer)
  }

  // 获取随机 AI 短语
  const getRandomPhrase = () => {
    return aiPhrases[Math.floor(Math.random() * aiPhrases.length)]
  }

  return {
    // 状态
    isMenuActive,
    speechBubbleContent,
    showSpeechBubble,
    speechBubbleType,
    filterType,
    aiPhrases,

    // 方法
    toggleMenu,
    closeMenu,
    showRandomSpeech,
    hideSpeechBubble,
    showDateFilterBubble,
    startFilterTimer,
    stopFilterTimer,
    getRandomPhrase
  }
})
