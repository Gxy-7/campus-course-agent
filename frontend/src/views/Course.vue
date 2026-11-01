<template>
  <div>
    <el-card>
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <!-- 管理员看到“课程管理”，学生看到“课程列表” -->
          <div style="font-size: 16px; font-weight: bold">
            <span>{{ isAdmin ? '课程管理' : '课程列表' }}</span>
          </div>
          <!-- 只有管理员才能新增课程 -->
          <el-button v-if="isAdmin" type="success" :icon="Plus" @click="handleCreate">
            新增课程
          </el-button>
        </div>
      </template>

      <div style="margin-bottom: 10px">
        <!-- 支持按课程名称、课程代码、授课老师模糊搜索 -->
        <el-input
          v-model="params.keywords"
          placeholder="请输入课程名称、代码或老师查询"
          style="width: 300px; margin-right: 8px"
          maxlength="50"
          clearable
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        />
        <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
      </div>

      <el-table
        :header-cell-style="{ backgroundColor: '#f5f7fa', color: '#333' }"
        :data="tableData"
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="code" label="课程代码" width="140" />
        <el-table-column prop="name" label="课程名称" width="180" />
        <el-table-column prop="teacher" label="授课老师" width="120" />
        <el-table-column
          prop="description"
          label="课程简介"
          min-width="260"
          show-overflow-tooltip
        />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'">
              {{ row.status === 1 ? '正常' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.create_time) }}
          </template>
        </el-table-column>
        <!-- 操作列只对管理员显示 -->
        <el-table-column v-if="isAdmin" label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" text bg @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" text bg @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
        <!-- 学生端显示选课/退课 -->
        <el-table-column v-if="!isAdmin" label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="enrolledIds.includes(row.id)"
              type="warning"
              text
              bg
              @click="handleUnenroll(row)"
            >
              退课
            </el-button>
            <el-button v-else type="primary" text bg @click="handleEnroll(row)">
              选课
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top: 10px; display: flex; justify-content: flex-end">
        <el-pagination
          v-model:current-page="params.page"
          v-model:page-size="params.pageSize"
          :total="total"
          background
          layout="total, prev, pager, next"
          @current-change="load"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="form.id ? '编辑课程' : '新增课程'"
      width="500"
    >
      <el-form
        ref="formRef"
        :rules="rules"
        :model="form"
        label-width="90px"
        style="width: 100%; padding-right: 30px; padding-top: 10px"
      >
        <el-form-item label="课程代码" prop="code">
          <el-input v-model="form.code" placeholder="例如：CS101" maxlength="50" />
        </el-form-item>
        <el-form-item label="课程名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入课程名称" maxlength="100" />
        </el-form-item>
        <el-form-item label="授课老师" prop="teacher">
          <el-input v-model="form.teacher" placeholder="请输入授课老师" maxlength="50" />
        </el-form-item>
        <el-form-item label="课程简介" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="请输入课程简介"
            maxlength="2000"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">正常</el-radio>
            <el-radio :value="0">停用</el-radio>
          </el-radio-group>
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
defineOptions({ name: 'Course' })

import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import {
  createCourseApi,
  deleteCourseApi,
  getCoursePageList,
  updateCourseApi
} from '@/api/course'
import {
  enrollCourseApi,
  getMyEnrollmentIds,
  unenrollCourseApi
} from '@/api/enrollment'
import { useUser } from '@/utils/user'

// 当前登录用户信息，用来判断是否管理员
const { userInfo } = useUser()
const isAdmin = computed(() => userInfo.value?.role === 'admin')

// 分页和搜索参数
const params = reactive({
  page: 1,
  pageSize: 10,
  keywords: ''
})

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const dialogVisible = ref(false)
const formRef = ref()
const formLoading = ref(false)
// 学生端保存已选课程 ID，用来切换“选课/退课”按钮
const enrolledIds = ref([])

// 新增/编辑共用的表单数据
const form = reactive({
  id: null,
  code: '',
  name: '',
  teacher: '',
  description: '',
  status: 1
})

// 表单校验规则：课程代码和名称必填，老师暂不做必填
const rules = {
  code: [
    { required: true, message: '请输入课程代码', trigger: 'blur' },
    { min: 1, max: 50, message: '课程代码长度为 1-50 个字符', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入课程名称', trigger: 'blur' },
    { min: 1, max: 100, message: '课程名称长度为 1-100 个字符', trigger: 'blur' }
  ]
}

// 把后端返回的 ISO 时间转成容易阅读的格式
const formatTime = (value) => {
  return value ? value.replace('T', ' ').slice(0, 19) : ''
}

// 重置表单，避免上一次编辑的数据残留
const resetForm = () => {
  Object.assign(form, {
    id: null,
    code: '',
    name: '',
    teacher: '',
    description: '',
    status: 1
  })
  formRef.value?.clearValidate()
}

// 加载课程分页数据
const load = async () => {
  loading.value = true
  try {
    const res = await getCoursePageList({
      page: params.page,
      page_size: params.pageSize,
      keywords: params.keywords
    })
    if (res.code === 200) {
      tableData.value = res.data?.list || []
      total.value = res.data?.total || 0
    }
  } finally {
    loading.value = false
  }
}

// 搜索时回到第一页，避免停留在不存在的页码
const handleSearch = () => {
  params.page = 1
  load()
}

// 学生端加载已选课程 ID
const loadEnrollments = async () => {
  if (isAdmin.value) return
  const res = await getMyEnrollmentIds()
  if (res.code === 200) enrolledIds.value = res.data || []
}

// 选课成功后再刷新已选列表，让按钮变成“退课”
const handleEnroll = async (row) => {
  const res = await enrollCourseApi(row.id)
  if (res.code === 200) {
    ElMessage.success('选课成功')
    loadEnrollments()
  }
}

// 退课前二次确认
const handleUnenroll = (row) => {
  ElMessageBox.confirm(`确认退选课程 [${row.name}] ？`, '确认退课', {
    type: 'warning'
  })
    .then(async () => {
      const res = await unenrollCourseApi(row.id)
      if (res.code === 200) {
        ElMessage.success('退课成功')
        loadEnrollments()
      }
    })
    .catch(() => {})
}

// 打开新增弹窗
const handleCreate = () => {
  resetForm()
  dialogVisible.value = true
}

// 打开编辑弹窗，并把当前行数据填入表单
const handleEdit = (row) => {
  resetForm()
  Object.assign(form, {
    id: row.id,
    code: row.code,
    name: row.name,
    teacher: row.teacher || '',
    description: row.description || '',
    status: row.status
  })
  dialogVisible.value = true
}

// 只提交后端需要的字段，避免把 id、create_time 等一起传过去
const buildPayload = () => ({
  code: form.code,
  name: form.name,
  teacher: form.teacher,
  description: form.description,
  status: form.status
})

// 保存课程：有 id 表示编辑，没有 id 表示新增
const handleSave = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  formLoading.value = true
  try {
    const payload = buildPayload()
    const res = form.id
      ? await updateCourseApi(form.id, payload)
      : await createCourseApi(payload)
    if (res.code === 200) {
      dialogVisible.value = false
      ElMessage.success(form.id ? '修改成功' : '新增成功')
      load()
    }
  } finally {
    formLoading.value = false
  }
}

// 删除前二次确认；如果当前页只有最后一条数据，删除后自动回到上一页
const handleDelete = (row) => {
  ElMessageBox.confirm(`确认删除课程 [${row.name}] ？`, '确认删除', {
    type: 'warning'
  })
    .then(async () => {
      const res = await deleteCourseApi(row.id)
      if (res.code === 200) {
        ElMessage.success('删除成功')
        if (tableData.value.length === 1 && params.page > 1) {
          params.page -= 1
        }
        load()
      }
    })
    .catch(() => {})
}

onMounted(() => {
  load()
  loadEnrollments()
})
</script>
