import request from '@/utils/request'

/**
 * 获取当前学生已选课程 ID
 */
export function getMyEnrollmentIds() {
  return request({
    url: '/api/enrollment/my',
    method: 'get'
  })
}

/**
 * 选课
 */
export function enrollCourseApi(courseId) {
  return request({
    url: `/api/enrollment/${courseId}`,
    method: 'post'
  })
}

/**
 * 退课
 */
export function unenrollCourseApi(courseId) {
  return request({
    url: `/api/enrollment/${courseId}`,
    method: 'delete'
  })
}
