<script setup lang="ts">
import { useSellersStore } from '../../stores/sellers'
import { useAI } from '../../composables/useAI'
import SellerCard from './SellerCard.vue'

const sellersStore = useSellersStore()
const { analyze } = useAI()

function handleAnalyze(sellerId: string) {
  const seller = sellersStore.getSeller(sellerId)
  if (seller) {
    analyze('seller', sellerId, { ...seller })
  }
}
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <SellerCard
      v-for="(seller, index) in sellersStore.rankedSellers"
      :key="seller.id"
      :seller="seller"
      :rank="index + 1"
      @analyze="handleAnalyze"
    />
  </div>
</template>
