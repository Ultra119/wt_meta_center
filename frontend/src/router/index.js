import { createRouter, createWebHashHistory } from 'vue-router'

const MetaTab        = () => import('../views/MetaTab.vue')
const RedbookTab     = () => import('../views/RedbookTab.vue')
const BracketsTab    = () => import('../views/BracketsTab.vue')
const FarmTab        = () => import('../views/FarmTab.vue')
const ProgressionTab = () => import('../views/ProgressionTab.vue')
const CostTreeTab    = () => import('../views/CostTreeTab.vue')

const routes = [
  { path: '/',            redirect: '/meta' },
  { path: '/meta',        component: MetaTab,         name: 'meta'        },
  { path: '/redbook',     component: RedbookTab,      name: 'redbook'     },
  { path: '/brackets',    component: BracketsTab,     name: 'brackets'    },
  { path: '/farm',        component: FarmTab,         name: 'farm'        },
  { path: '/progression', component: ProgressionTab,  name: 'progression' },
  { path: '/cost',        component: CostTreeTab,     name: 'cost' },
]

export default createRouter({
  history: createWebHashHistory(),
  routes,
})
