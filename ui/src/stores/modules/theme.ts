import { defineStore } from 'pinia'
import { cloneDeep } from 'lodash'
import { useElementPlusTheme } from 'use-element-plus-theme'
import ThemeApi from '@/api/system-settings/theme'
import type {Ref} from "vue";
export interface themeStateTypes {
  themeInfo: any
}
const defalueColor = '#3370FF'

const updateFavicon = (icon?: string) => {
  if (typeof document === 'undefined') {
    return
  }
  let link = document.querySelector("link[rel~='icon']") as HTMLLinkElement | null
  if (!link) {
    link = document.createElement('link')
    link.rel = 'icon'
    document.head.appendChild(link)
  }
  if (icon) {
    link.href = icon
  }
}

const useThemeStore = defineStore('theme', {
  state: (): themeStateTypes => ({
    themeInfo: null,
  }),
  actions: {
    isDefaultTheme() {
      return !this.themeInfo?.theme || this.themeInfo?.theme === defalueColor
    },

    setTheme(data?: any) {
      const { changeTheme } = useElementPlusTheme(this.themeInfo?.theme || defalueColor)
      changeTheme(data?.['theme'] || defalueColor)
      this.themeInfo = cloneDeep(data)
      updateFavicon(this.themeInfo?.icon)
    },

    async theme(loading?: Ref<boolean>) {
      return await ThemeApi.getThemeInfo(loading).then((ok) => {
        this.setTheme(ok.data)
      })
    },
  },
})

export default useThemeStore
