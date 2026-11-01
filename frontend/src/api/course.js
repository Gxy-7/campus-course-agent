import request from '@/utils/request'

/**
 * 分页查询课程列表
 * 管理员会看到全部课程，学生只会看到正常状态的课程
 */
export function getCoursePageList(params) {
  return request({
    url: '/api/course/list',
    method: 'get',
    params
  })
}

/**
 * 新增课程
 */
export function createCourseApi(data) {
  return request({
    url: '/api/course',
    method: 'post',
    data
  })
}

/**
 * 编辑课程
 */
export function updateCourseApi(courseId, data) {
  return request({
    url: `/api/course/${courseId}`,
    method: 'put',
    data
  })
}

/**
 * 删除课程
 */
export function deleteCourseApi(courseId) {
  return request({
    url: `/api/course/${courseId}`,
    method: 'delete'
  })
}
