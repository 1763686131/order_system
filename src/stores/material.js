import { defineStore } from 'pinia'
import request from '@/api/request'

export const useMaterialStore = defineStore('material', {
  state: () => ({
    materials: [],
    remarkTags: []
  }),

  getters: {
    allMaterials: (state) => state.materials,
    allRemarkTags: (state) => state.remarkTags
  },

  actions: {
    setMaterials(materials) {
      this.materials = materials
    },

    setRemarkTags(tags) {
      this.remarkTags = tags
    },

    // API 请求方法
    async fetchMaterials() {
      try {
        const response = await request({ url: '/materials', method: 'GET' })
        this.setMaterials(Array.isArray(response) ? response : [])
        return response
      } catch (error) {
        console.error('Failed to fetch materials:', error)
        return []
      }
    },

    async uploadMaterial(materialData) {
      try {
        const response = await request({
          url: '/materials',
          method: 'POST',
          data: materialData
        })
        if (response.success) {
          await this.fetchMaterials()
        }
        return response
      } catch (error) {
        console.error('Failed to upload material:', error)
        throw error
      }
    },

    async fetchRemarkTags() {
      try {
        const response = await request({ url: '/material_tags', method: 'GET' })
        this.setRemarkTags(Array.isArray(response) ? response : [])
        return response
      } catch (error) {
        console.error('Failed to fetch remark tags:', error)
        return []
      }
    },

    async saveRemarkTag(tag) {
      try {
        const response = await request({
          url: '/material_tags',
          method: 'POST',
          data: { tag }
        })
        return response
      } catch (error) {
        console.error('Failed to save remark tag:', error)
        throw error
      }
    }
  }
})
