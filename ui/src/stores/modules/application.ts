import { defineStore } from 'pinia'
import { getChatBaseUrl } from '@/utils/common'
const useApplicationStore = defineStore('application', {
  state: () => ({
    location: `${getChatBaseUrl()}/`,
  }),
  actions: {},
})

export default useApplicationStore
