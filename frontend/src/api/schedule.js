import request from '@/utils/request'

/**
 * 查询所有正常课程的课表
 */
export function getScheduleList() {
  return request({
    url: '/api/schedule/list',
    method: 'get'
  })
}

/**
 * 查询当前学生已选课程的全部课表
 */
export function getMyScheduleList() {
  return request({
    url: '/api/schedule/my',
    method: 'get'
  })
}

/**
 * 查询某门课程的课表
 */
export function getCourseScheduleList(courseId) {
  return request({
    url: `/api/schedule/course/${courseId}`,
    method: 'get'
  })
}

/**
 * 新增课表时间段
 */
export function createScheduleApi(data) {
  return request({
    url: '/api/schedule',
    method: 'post',
    data
  })
}

/**
 * 编辑课表时间段
 */
export function updateScheduleApi(scheduleId, data) {
  return request({
    url: `/api/schedule/${scheduleId}`,
    method: 'put',
    data
  })
}

/**
 * 删除课表时间段
 */
export function deleteScheduleApi(scheduleId) {
  return request({
    url: `/api/schedule/${scheduleId}`,
    method: 'delete'
  })
}
