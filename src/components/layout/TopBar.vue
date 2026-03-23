<script setup lang="ts">
</script>

<template>
  <header class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0">
    <div class="flex items-center gap-4">
      <h1 class="text-lg font-semibold text-gray-800">
        <router-link to="/" class="hover:text-indigo-600 transition-colors">CRM</router-link>
      </h1>
    </div>

    <div class="flex items-center gap-4">
      <!-- Avatar -->
      <div class="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
        <span class="text-indigo-600 text-sm font-medium">U</span>
      </div>
    </div>
  </header>
</template>
