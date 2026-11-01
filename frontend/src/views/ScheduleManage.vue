<template>
  <div>
    <el-card>
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <div style="font-size: 16px; font-weight: bold">课表管理</div>
          <el-button
            type="success"
            :icon="Plus"
            :disabled="!selectedCourseId"
            @click="handleCreate"
          >
            新增时间段
          </el-button>
        </div>
      </template>

      <div style="margin-bottom: 12px; display: flex; align-items: center">
        <span style="margin-right: 8px">选择课程：</span>
        <el-select
          v-model="selectedCourseId"
          filterable
          placeholder="请选择课程"
          style="width: 300px"
          @change="loadSchedules"
        >
          <el-option
            v-for="course in courseOptions"
            :key="course.id"
            :label="`${course.code} - ${course.name}`"
            :value="course.id"
          />
        </el-select>
        <el-tag v-if="selectedCourse" type="info" style="margin-left: 10px">
          {{ selectedCourse.teacher || '老师待定' }}
        </el-tag>
      </div>

      <el-table
        :data="scheduleList"
        v-loading="loading"
        :header-cell-style="{ backgroundColor: '#f5f7fa', color: '#333' }"
      >
        <el-table-column label="星期" width="100">
          <template #default="{ row }">{{ weekdayLabel(row.weekday) }}</template>
        </el-table-column>
        <el-table-column label="节次" width="140">
          <template #default="{ row }">
            第 {{ row.start_section }}-{{ row.end_section }} 节
          </template>
        </el-table-column>
        <el-table-column label="周次" width="200">
          <template #default="{ row }">{{ weeksLabel(row) }}</template>
        </el-table-column>
        <el-table-column prop="classroom" label="上课地点" />
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button type="primary" text bg @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" text bg @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="!loading && !scheduleList.length"
        description="这门课还没有课表，点击右上角新增"
      />
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="form.id ? '编辑时间段' : '新增时间段'"
      width="520"
    >
      <el-form
        ref="formRef"
        :rules="rules"
        :model="form"
        label-width="90px"
        style="padding-right: 20px"
      >
        <el-form-item label="课程">
          <el-input
            :model-value="selectedCourse ? `${selectedCourse.code} - ${selectedCourse.name}` : ''"
            disabled
          />
        </el-form-item>
        <el-form-item label="星期" prop="weekday">
          <el-select v-model="form.weekday" style="width: 100%">
            <el-option v-for="day in 7" :key="day" :label="weekdayLabel(day)" :value="day" />
          </el-select>
        </el-form-item>
        <el-form-item label="节次" required>
          <div style="display: flex; align-items: center; gap: 8px">
            <el-select v-model="form.startSection" style="width: 130px">
              <el-option
                v-for="section in 12"
                :key="section"
                :label="`第 ${section} 节`"
                :value="section"
              />
            </el-select>
            <span>至</span>
            <el-select v-model="form.endSection" style="width: 130px">
              <el-option
                v-for="section in 12"
                :key="section"
                :label="`第 ${section} 节`"
                :value="section"
              />
            </el-select>
          </div>
        </el-form-item>
        <el-form-item label="周次" required>
          <div style="display: flex; align-items: center; gap: 8px">
            <el-input-number v-model="form.startWeek" :min="1" :max="20" />
            <span>至</span>
            <el-input-number v-model="form.endWeek" :min="1" :max="20" />
            <span>周</span>
          </div>
        </el-form-item>
        <el-form-item label="周类型" prop="weekType">
          <el-select v-model="form.weekType" style="width: 100%">
            <el-option label="每周" :value="0" />
            <el-option label="单周" :value="1" />
            <el-option label="双周" :value="2" />
          </el-select>
        </el-form-item>
        <el-form-item label="上课地点" prop="classroom">
          <el-input v-model="form.classroom" placeholder="例如：A101" maxlength="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="formLoading" @click="handleSave">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
defineOptions({ name: 'ScheduleManage' })

import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getCoursePageList } from '@/api/course'
import {
  createScheduleApi,
  deleteScheduleApi,
  getCourseScheduleList,
  updateScheduleApi
} from '@/api/schedule'

const courseOptions = ref([])
const selectedCourseId = ref(null)
const selectedCourse = computed(() =>
  courseOptions.value.find((item) => item.id === selectedCourseId.value)
)

const scheduleList = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref()
const formLoading = ref(false)

// 表单使用驼峰命名，提交时再转换成后端的下划线字段
const form = reactive({
  id: null,
  weekday: 1,
  startSection: 1,
  endSection: 2,
  startWeek: 1,
  endWeek: 16,
  weekType: 0,
  classroom: ''
})

const rules = {
  weekday: [{ required: true, message: '请选择星期', trigger: 'change' }],
  classroom: [{ required: true, message: '请输入上课地点', trigger: 'blur' }]
}

const weekdayLabel = (day) =>
  ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日'][day] || ''
const weekTypeLabel = (type) => ['每周', '单周', '双周'][type] || ''
const weeksLabel = (row) => {
  const text =
    row.start_week === row.end_week
      ? `第 ${row.start_week} 周`
      : `${row.start_week}-${row.end_week} 周`
  return row.week_type === 0 ? text : `${text}（${weekTypeLabel(row.week_type)}）`
}

// 先加载课程下拉，再加载第一门课的课表
const loadCourses = async () => {
  const res = await getCoursePageList({ page: 1, page_size: 100 })
  if (res.code === 200) {
    courseOptions.value = res.data?.list || []
    if (courseOptions.value.length) {
      selectedCourseId.value = courseOptions.value[0].id
      await loadSchedules()
    }
  }
}

const loadSchedules = async () => {
  if (!selectedCourseId.value) {
    scheduleList.value = []
    return
  }
  loading.value = true
  try {
    const res = await getCourseScheduleList(selectedCourseId.value)
    if (res.code === 200) scheduleList.value = res.data || []
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  Object.assign(form, {
    id: null,
    weekday: 1,
    startSection: 1,
    endSection: 2,
    startWeek: 1,
    endWeek: 16,
    weekType: 0,
    classroom: ''
  })
  formRef.value?.clearValidate()
}

const handleCreate = () => {
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row) => {
  resetForm()
  Object.assign(form, {
    id: row.id,
    weekday: row.weekday,
    startSection: row.start_section,
    endSection: row.end_section,
    startWeek: row.start_week,
    endWeek: row.end_week,
    weekType: row.week_type,
    classroom: row.classroom
  })
  dialogVisible.value = true
}

const handleSave = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  if (form.endSection < form.startSection) {
    return ElMessage.warning('结束节次不能小于开始节次')
  }
  if (form.endWeek < form.startWeek) {
    return ElMessage.warning('结束周不能小于开始周')
  }
  if (!selectedCourseId.value) return ElMessage.warning('请先选择课程')

  formLoading.value = true
  try {
    const payload = {
      course_id: selectedCourseId.value,
      weekday: form.weekday,
      start_section: form.startSection,
      end_section: form.endSection,
      start_week: form.startWeek,
      end_week: form.endWeek,
      week_type: form.weekType,
      classroom: form.classroom
    }
    const res = form.id
      ? await updateScheduleApi(form.id, payload)
      : await createScheduleApi(payload)
    if (res.code === 200) {
      dialogVisible.value = false
      ElMessage.success(form.id ? '修改成功' : '新增成功')
      loadSchedules()
    }
  } finally {
    formLoading.value = false
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(
    `确认删除 ${weekdayLabel(row.weekday)} 第 ${row.start_section}-${row.end_section} 节的课表？`,
    '确认删除',
    { type: 'warning' }
  )
    .then(async () => {
      const res = await deleteScheduleApi(row.id)
      if (res.code === 200) {
        ElMessage.success('删除成功')
        loadSchedules()
      }
    })
    .catch(() => {})
}

onMounted(loadCourses)
</script>
