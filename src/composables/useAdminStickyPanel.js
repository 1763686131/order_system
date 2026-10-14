import {
  computed,
  inject,
  nextTick,
  onBeforeUnmount,
  onMounted,
  provide,
  ref,
  shallowRef
} from 'vue'

const adminStickyPanelKey = Symbol('adminStickyPanel')

export function provideAdminStickyPanel(mainContentRef, headerRef) {
  const activePanel = shallowRef(null)
  const pinned = ref(false)
  const expanded = ref(false)
  const placeholderHeight = ref(0)
  const geometry = ref({ left: 0, top: 0, width: 0, maxHeight: 0, scrollable: false })
  let resizeObserver = null

  const updatePosition = () => {
    const container = mainContentRef.value
    const header = headerRef.value
    const content = activePanel.value?.contentRef.value
    if (!container || !header || !content) return

    const rect = container.getBoundingClientRect()
    const padding = getComputedStyle(container)
    const leftPadding = parseFloat(padding.paddingLeft) || 0
    const rightPadding = parseFloat(padding.paddingRight) || 0
    const top = header.getBoundingClientRect().bottom
    const maxHeight = Math.max(0, window.innerHeight - top - 12)
    const nextGeometry = {
      left: rect.left + container.clientLeft + leftPadding,
      top,
      width: container.clientWidth - leftPadding - rightPadding,
      maxHeight,
      scrollable: content.scrollHeight > maxHeight
    }
    if (Object.keys(nextGeometry).some(key => geometry.value[key] !== nextGeometry[key])) {
      geometry.value = nextGeometry
    }
  }

  const restore = () => {
    if (pinned.value) activePanel.value?.onRestore?.()
    pinned.value = false
    expanded.value = false
  }

  const collapse = () => {
    if (!expanded.value) return
    expanded.value = false
    activePanel.value?.onCollapse?.()
  }

  const handleScroll = () => {
    const panel = activePanel.value
    const scrollTop = mainContentRef.value?.scrollTop || 0
    if (!panel) return

    if (scrollTop <= 0) {
      restore()
      return
    }

    collapse()
    if (!pinned.value && scrollTop > (panel.threshold ?? 24)) {
      // Preserve the list's layout while its filter panel is displayed below the header.
      placeholderHeight.value = panel.placeholderRef.value.getBoundingClientRect().height
      updatePosition()
      panel.onPin?.()
      pinned.value = true
      expanded.value = false
      panel.onCollapse?.()
    }
  }

  const handleWheel = event => {
    if (event.deltaX || event.deltaY) collapse()
  }

  const expand = () => {
    if (!activePanel.value || !pinned.value) return
    expanded.value = true
    activePanel.value.onExpand?.()
    nextTick(updatePosition)
  }

  const register = panel => {
    restore()
    resizeObserver?.disconnect()
    activePanel.value = panel
    resizeObserver = new ResizeObserver(updatePosition)
    for (const element of [
      mainContentRef.value,
      headerRef.value,
      panel.contentRef.value
    ]) {
      if (element) resizeObserver.observe(element)
    }
    nextTick(() => {
      if (activePanel.value !== panel) return
      updatePosition()
      handleScroll()
    })

    return () => {
      if (activePanel.value !== panel) return
      restore()
      resizeObserver?.disconnect()
      resizeObserver = null
      activePanel.value = null
    }
  }

  const placeholderStyle = computed(() =>
    pinned.value ? { height: `${placeholderHeight.value}px` } : {}
  )
  const contentStyle = computed(() => {
    if (!pinned.value) return {}
    if (!expanded.value) return { display: 'none' }
    return {
      position: 'fixed',
      top: `${geometry.value.top}px`,
      left: `${geometry.value.left}px`,
      width: `${geometry.value.width}px`,
      maxHeight: `${geometry.value.maxHeight}px`,
      overflowY: geometry.value.scrollable ? 'auto' : undefined,
      zIndex: 80
    }
  })

  provide(adminStickyPanelKey, {
    activePanel,
    pinned,
    placeholderStyle,
    contentStyle,
    register
  })
  onMounted(() => window.addEventListener('resize', updatePosition))
  onBeforeUnmount(() => {
    window.removeEventListener('resize', updatePosition)
    resizeObserver?.disconnect()
  })

  return {
    visible: computed(() => Boolean(activePanel.value) && pinned.value && !expanded.value),
    panelId: computed(() => activePanel.value?.id),
    buttonLabel: computed(() =>
      `展开${activePanel.value?.label || '筛选栏'}`
    ),
    handleScroll,
    handleWheel,
    expand
  }
}

export function useAdminStickyPanel(placeholderRef, contentRef, options = {}) {
  const controller = inject(adminStickyPanelKey, null)
  const panel = { ...options, placeholderRef, contentRef }
  const isActive = computed(() => controller?.activePanel.value === panel)
  let unregister = null

  onMounted(() => {
    if (placeholderRef.value && contentRef.value) {
      unregister = controller?.register(panel)
    }
  })
  onBeforeUnmount(() => unregister?.())

  return {
    pinned: computed(() => isActive.value && controller.pinned.value),
    placeholderStyle: computed(() => isActive.value ? controller.placeholderStyle.value : {}),
    contentStyle: computed(() => isActive.value ? controller.contentStyle.value : {})
  }
}
