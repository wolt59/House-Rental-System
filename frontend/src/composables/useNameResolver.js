import { reactive } from 'vue'
import { getProperty } from '../api/property'
import { useUserStore } from '../store/user'
import request from '../utils/request'

const userNames = reactive({})
const propertyNames = reactive({})

export function useNameResolver() {
  const userStore = useUserStore()

  function _currentUserId() {
    return userStore.user?.id
  }

  async function resolveUser(userId) {
    if (!userId) return '-'
    const key = String(userId)
    if (userNames[key]) return userNames[key]
    // If this is the current user, use store data directly.
    if (userStore.user && Number(key) === _currentUserId()) {
      userNames[key] = userStore.user.full_name || userStore.user.username || `用户#${key}`
      return userNames[key]
    }
    // Try API call - backend allows lookup if related by contract/application
    try {
      const res = await request.get(`/api/v1/users/${key}`)
      const u = res.data || res
      userNames[key] = u.full_name || u.username || `用户#${key}`
      return userNames[key]
    } catch {
      userNames[key] = `用户#${key}`
      return userNames[key]
    }
  }

  async function resolveProperty(propertyId) {
    if (!propertyId) return '-'
    const key = String(propertyId)
    if (propertyNames[key]) return propertyNames[key]
    try {
      const prop = await getProperty(Number(key))
      propertyNames[key] = prop.title || `房源#${key}`
      return propertyNames[key]
    } catch {
      propertyNames[key] = `房源#${key}`
      return propertyNames[key]
    }
  }

  async function resolveItems(items, fields) {
    const userFields = new Set(['tenant_id', 'landlord_id', 'user_id', 'from_user_id', 'to_user_id', 'handled_by', 'owner_id'])
    const propertyFields = new Set(['property_id'])

    const userKeys = new Set()
    const propertyKeys = new Set()

    items.forEach(item => {
      fields.forEach(f => {
        const val = item[f]
        if (val != null && val !== '') {
          if (propertyFields.has(f)) {
            propertyKeys.add(val)
          } else if (userFields.has(f)) {
            userKeys.add(val)
          }
        }
      })
    })

    await Promise.all([
      ...[...userKeys].map(key => resolveUser(key).catch(() => {})),
      ...[...propertyKeys].map(key => resolveProperty(key).catch(() => {})),
    ])
  }

  return { resolveUser, resolveProperty, resolveItems, userNames, propertyNames }
}
