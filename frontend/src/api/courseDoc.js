import request from '@/utils/request'

/**
 * 上传课程资料
 * 后端会自动抽取文本、切块并入库
 */
export function uploadCourseDocApi(file, courseId, title) {
  const formData = new FormData()
  formData.append('course_id', courseId)
  if (title) formData.append('title', title)
  formData.append('file', file)

  return request({
    url: '/api/course-doc/upload',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/**
 * 查询课程资料列表
 */
export function getCourseDocList(courseId) {
  return request({
    url: '/api/course-doc/list',
    method: 'get',
    params: { course_id: courseId }
  })
}

/**
 * 删除课程资料，同时删除文本块
 */
export function deleteCourseDocApi(documentId) {
  return request({
    url: `/api/course-doc/${documentId}`,
    method: 'delete'
  })
}

/**
 * 重新向量化全部课程资料
 */
export function reindexCourseDocsApi() {
  return request({
    url: '/api/course-doc/reindex',
    method: 'post'
  })
}
