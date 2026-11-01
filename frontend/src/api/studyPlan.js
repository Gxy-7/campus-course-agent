import request from '@/utils/request'

/**
 * 查询我的学习计划
 */
export function getStudyPlanList() {
  return request({
    url: '/api/study-plan/list',
    method: 'get'
  })
}

/**
 * 新建学习计划
 */
export function createStudyPlanApi(data) {
  return request({
    url: '/api/study-plan',
    method: 'post',
    data
  })
}

/**
 * 编辑学习计划
 */
export function updateStudyPlanApi(planId, data) {
  return request({
    url: `/api/study-plan/${planId}`,
    method: 'put',
    data
  })
}

/**
 * 删除学习计划
 */
export function deleteStudyPlanApi(planId) {
  return request({
    url: `/api/study-plan/${planId}`,
    method: 'delete'
  })
}
