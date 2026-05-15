<script setup lang="ts">
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useActivitiesStore } from '../../stores/activities'
import ActivityTimeline from '../activities/ActivityTimeline.vue'

const { t } = useI18n()
const router = useRouter()
const activitiesStore = useActivitiesStore()

onMounted(() => {
  void activitiesStore.fetchList({ limit: 12, days: 30 })
})

function openAll() {
  router.push('/activities')
}
</script>

<template>
  <div class="card">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-gray-800">{{ t('activity.title') }}</h3>
      <button type="button" class="text-xs text-indigo-600 hover:underline" @click="openAll">
        {{ t('activities.viewAll') }}
      </button>
    </div>
    <div class="max-h-80 overflow-y-auto">
      <ActivityTimeline
        v-if="!activitiesStore.loading"
        :items="activitiesStore.items"
        compact
        show-entity
      />
      <p v-else class="text-sm text-gray-500 py-4 text-center">{{ t('common.loading') }}</p>
    </div>
  </div>
</template>
