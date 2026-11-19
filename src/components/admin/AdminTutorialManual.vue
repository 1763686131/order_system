<template>
  <Teleport to="body">
    <dialog
      id="admin-tutorial-manual"
      ref="dialogRef"
      class="tutorial-manual"
      aria-labelledby="tutorial-manual-title"
      @click.self="closeManual"
      @close="restoreEntryFocus"
    >
      <div class="manual-content">
        <header class="manual-header">
          <h2 id="tutorial-manual-title">教程手册</h2>
          <button class="manual-close" type="button" aria-label="关闭教程手册" @click="closeManual">
            <X :size="18" aria-hidden="true" />
          </button>
        </header>

        <template v-if="availableTopics.length">
          <ol v-if="primaryTopics.length" class="manual-primary-topics" role="list" aria-label="主要教程">
            <li
              v-for="entry in primaryTopics"
              :key="entry.number"
              :value="entry.number"
              :class="{ 'manual-topic-group': entry.title }"
            >
              <h3 v-if="entry.title" class="manual-group-title">{{ entry.number }}、{{ entry.title }}</h3>
              <div :class="{ 'manual-topics': entry.title }">
                <button
                  v-for="topic in entry.topics"
                  :key="topic.id"
                  class="manual-topic"
                  type="button"
                  :disabled="Boolean(startingTopic)"
                  @click="startTour(topic)"
                >
                  <span class="topic-copy">
                    <strong>{{ entry.title ? topic.shortTitle : `${entry.number}、${topic.title}` }}</strong>
                    <small>{{ topic.location }}</small>
                  </span>
                  <span class="topic-action">{{ startingTopic === topic.id ? '打开中…' : '开始' }}</span>
                </button>
              </div>
            </li>
          </ol>

          <section v-if="otherTopics.length" aria-labelledby="tutorial-manual-other-title">
            <h3 id="tutorial-manual-other-title" class="manual-section-title">其它</h3>
            <div class="manual-topics">
              <button
                v-for="topic in otherTopics"
                :key="topic.id"
                class="manual-topic"
                type="button"
                :disabled="Boolean(startingTopic)"
                @click="startTour(topic)"
              >
                <span class="topic-copy">
                  <strong>{{ topic.title }}</strong>
                  <small>{{ topic.location }}</small>
                </span>
                <span class="topic-action">{{ startingTopic === topic.id ? '打开中…' : '开始' }}</span>
              </button>
            </div>
          </section>
        </template>
        <p v-else class="manual-note">当前账号暂无可用教程。</p>
        <p v-if="errorMessage" class="manual-error" role="alert">{{ errorMessage }}</p>
      </div>
    </dialog>
  </Teleport>

  <TutorialSpotlight
    v-if="activeStep"
    :step="activeStep"
    :number="stepIndex + 1"
    :total="tour.steps.length"
    :next-target="nextTarget"
    :can-go-back="canGoBack"
    @next="advanceTour"
    @back="stepIndex -= 1"
    @close="endTour"
    @target-missing="handleMissingTarget"
  />
</template>

<script setup>
import { computed, nextTick, ref, shallowRef, watch } from 'vue'
import { X } from '@lucide/vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import TutorialSpotlight from './TutorialSpotlight.vue'
import { tutorialTopics } from './tutorialTopics'

const primaryTopicGroups = [
  { ids: ['store'] },
  { ids: ['warehouse'] },
  { title: '新建物品', ids: ['product', 'material'] },
  { ids: ['customer'] },
  { ids: ['sale'] },
]
const primaryTopicIds = new Set(primaryTopicGroups.flatMap(group => group.ids))

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const canOpenTopic = topic => topic.permissions.every(permission => userStore.hasPerm(permission))
const availableTopics = computed(() => tutorialTopics.filter(canOpenTopic))
const primaryTopics = computed(() => {
  const topicsById = new Map(availableTopics.value.map(topic => [topic.id, topic]))
  return primaryTopicGroups.map((group, index) => ({
    number: index + 1,
    title: group.title,
    topics: group.ids.map(id => topicsById.get(id)).filter(Boolean),
  })).filter(entry => entry.topics.length)
})
const otherTopics = computed(() => availableTopics.value.filter(topic => !primaryTopicIds.has(topic.id)))
const dialogRef = ref(null)
const errorMessage = ref('')
const startingTopic = ref('')
const tour = shallowRef(null)
const stepIndex = ref(0)
const activeStep = computed(() => tour.value?.steps[stepIndex.value])
const nextStep = computed(() => tour.value?.steps[stepIndex.value + 1])
const stepRoute = step => step?.routeName ?? tour.value?.routeName
const nextTarget = computed(() => nextStep.value && stepRoute(nextStep.value) === route.name
  ? activeStep.value.advanceTarget || nextStep.value.target
  : '')
const canGoBack = computed(() => {
  const previous = tour.value?.steps[stepIndex.value - 1]
  return Boolean(previous && !previous.actionTarget && stepRoute(previous) === route.name)
})
let entryButton = null

function endTour() {
  tour.value = null
  stepIndex.value = 0
}

function advanceTour() {
  if (nextStep.value && stepRoute(nextStep.value) === route.name) stepIndex.value += 1
}

function open(trigger) {
  if (!dialogRef.value || dialogRef.value.open) return
  entryButton = trigger
  errorMessage.value = ''
  endTour()
  dialogRef.value.showModal()
}

function closeManual() {
  dialogRef.value?.close()
}

function restoreEntryFocus() {
  if (!activeStep.value && entryButton?.isConnected) {
    entryButton.focus({ preventScroll: true })
  }
}

async function startTour(topic) {
  if (startingTopic.value || !canOpenTopic(topic)) return
  startingTopic.value = topic.id
  errorMessage.value = ''
  const useMobileSteps = topic.mobileSteps && window.matchMedia('(max-width: 780px)').matches

  try {
    if (route.name !== topic.routeName) await router.push({ name: topic.routeName })
    await nextTick()
    if (!dialogRef.value?.open) return
    if (route.name !== topic.routeName || !canOpenTopic(topic)) {
      errorMessage.value = '暂时无法打开教程页面，请重试。'
      return
    }

    const steps = useMobileSteps ? topic.mobileSteps : topic.steps
    const existingMobileDraft = useMobileSteps && document.querySelector('[data-tutorial-target="mobile-order-contact"]')
    stepIndex.value = existingMobileDraft ? steps.findIndex(step => step.target === 'mobile-order-contact') : 0
    tour.value = { ...topic, steps }
    closeManual()
  } catch {
    errorMessage.value = '暂时无法打开教程页面，请重试。'
  } finally {
    startingTopic.value = ''
  }
}

function handleMissingTarget() {
  endTour()
  errorMessage.value = '暂时无法定位这一步，请重新开始引导。'
  dialogRef.value?.showModal()
}

watch([() => route.name, availableTopics], ([name, topics]) => {
  if (!tour.value) return
  if (!topics.some(topic => topic.id === tour.value.id)) {
    endTour()
    return
  }
  if (name === stepRoute(activeStep.value)) return
  if (activeStep.value.actionTarget && nextStep.value && name === stepRoute(nextStep.value)) advanceTour()
  else endTour()
})

defineExpose({ open })
</script>

<style scoped>
.tutorial-manual {
  box-sizing: border-box;
  width: min(680px, calc(100% - 28px));
  max-height: calc(100dvh - 28px);
  margin: auto;
  padding: 0;
  color: #172033;
  background: #fff;
  border: 1px solid #dce5ec;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(15, 23, 42, .22);
}

.tutorial-manual::backdrop {
  background: rgba(15, 23, 42, .43);
}

.manual-content {
  padding: 18px;
}

.manual-header {
  position: sticky;
  top: 0;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: -18px -18px 12px;
  padding: 14px 18px;
  background: #fff;
  border-bottom: 1px solid #edf1f4;
}

.manual-header h2 {
  margin: 0;
  font-size: 18px;
}

.manual-close {
  display: grid;
  width: 32px;
  height: 32px;
  place-items: center;
  color: #596579;
  background: transparent;
  border: 0;
  border-radius: 6px;
  cursor: pointer;
}

.manual-close:hover {
  background: #f1f5f9;
}

.manual-primary-topics {
  display: grid;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.manual-topic-group {
  padding: 10px;
  background: #f8fbfa;
  border: 1px solid #dce8e3;
  border-radius: 8px;
}

.manual-group-title {
  margin: 0 0 8px;
  font-size: 14px;
}

.manual-section-title {
  margin: 16px 0 8px;
  font-size: 14px;
}

.manual-topics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.manual-topic {
  display: flex;
  width: 100%;
  min-height: 64px;
  align-items: center;
  gap: 10px;
  padding: 10px;
  text-align: left;
  color: inherit;
  background: #f8fbfa;
  border: 1px solid #dce8e3;
  border-radius: 8px;
  cursor: pointer;
}

.manual-primary-topics .manual-topic {
  min-height: 54px;
  padding-block: 8px;
}

.manual-topic-group .manual-topic {
  background: #fff;
}

.manual-topic:hover:not(:disabled) {
  border-color: #87c9b4;
  background: #edf8f4;
}

.manual-topic:disabled {
  opacity: .65;
  cursor: wait;
}

.topic-copy {
  display: grid;
  flex: 1;
  gap: 4px;
  font-size: 14px;
}

.topic-copy small,
.manual-note {
  color: #596579;
  font-size: 13px;
}

.topic-action {
  flex: none;
  color: #08745a;
  font-size: 13px;
  font-weight: 600;
}

.manual-error {
  margin: 10px 0 0;
  color: #a52d33;
  font-size: 13px;
}

@media (max-width: 560px) {
  .manual-topics {
    grid-template-columns: 1fr;
  }
}
</style>
