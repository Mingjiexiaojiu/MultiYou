<template>
  <div class="cropper-container">
    <vue-cropper
      ref="cropperRef"
      :src="src"
      :aspect-ratio="1"
      :view-mode="1"
      :auto-crop-area="0.8"
      :background="false"
      style="max-height: 320px"
    />
    <button type="button" class="btn-crop" @click="crop">裁剪</button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import VueCropper from 'vue-cropper'
import 'vue-cropper/dist/index.css'

const props = defineProps({ src: String })
const emit = defineEmits(['cropped'])

const cropperRef = ref(null)

function crop() {
  cropperRef.value.getCropBlob((blob) => {
    emit('cropped', blob)
  })
}
</script>

<style scoped>
.cropper-container { margin-bottom: 12px; }
.btn-crop {
  margin-top: 10px;
  padding: 8px 20px;
  background: #7c6fff;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  width: 100%;
}
</style>
