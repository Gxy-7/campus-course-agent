<template>
  <div>
    <el-card>
      <template #header>
        <div style="font-size: 16px; font-weight: bold">资料管理</div>
      </template>

      <div class="toolbar">
        <span>选择课程：</span>
        <el-select
          v-model="selectedCourseId"
          filterable
          placeholder="请选择课程"
          style="width: 280px"
          @change="loadDocuments"
        >
          <el-option
            v-for="course in courseOptions"
            :key="course.id"
            :label="`${course.code} - ${course.name}`"
            :value="course.id"
          />
        </el-select>

        <el-input
          v-model="docTitle"
          placeholder="资料标题（可选，默认文件名）"
          maxlength="150"
          style="width: 260px"
        />

        <el-upload
          :show-file-list="false"
          :http-request="handleUpload"
          :before-upload="beforeUpload"
          accept=".txt,.md,.pdf,.docx"
          :disabled="!selectedCourseId || uploading"
        >
          <el-button
            type="primary"
            :icon="Upload"
            :loading="uploading"
            :disabled="!selectedCourseId"
          >
            上传资料
          </el-button>
        </el-upload>

        <el-button
          :icon="Refresh"
          :loading="reindexing"
          @click="handleReindex"
        >
          重新入库
        </el-button>
      </div>

      <div class="hint">
        支持 .txt / .md / .pdf / .docx，单个文件不超过 20MB；扫描版 PDF 暂不支持。
      </div>

      <el-table
        :data="documents"
        v-loading="loading"
        style="width: 100%; margin-top: 14px"
        :header-cell-style="{ backgroundColor: '#f5f7fa', color: '#333' }"
      >
        <el-table-column prop="title" label="资料标题" min-width="180" show-overflow-tooltip />
        <el-table-column prop="course_name" label="课程" width="150" />
        <el-table-column prop="original_name" label="原始文件" min-width="200" show-overflow-tooltip />
        <el-table-column prop="file_type" label="类型" width="80" />
        <el-table-column prop="char_count" label="字符数" width="100" />
        <el-table-column prop="chunk_count" label="文本块" width="100" />
        <el-table-column prop="create_time" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.create_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" text bg @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="!loading && selectedCourseId && !documents.length"
        description="这门课还没有上传资料"
      />
    </el-card>
  </div>
</template>

<script setup>
defineOptions({ name: 'CourseDocs' })

import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Upload } from '@element-plus/icons-vue'
import { getCoursePageList } from '@/api/course'
import {
  deleteCourseDocApi,
  getCourseDocList,
  reindexCourseDocsApi,
  uploadCourseDocApi
} from '@/api/courseDoc'

const courseOptions = ref([])
const selectedCourseId = ref(null)
const documents = ref([])
const docTitle = ref('')
const loading = ref(false)
const uploading = ref(false)
const reindexing = ref(false)

const formatTime = (value) => {
  return value ? value.replace('T', ' ').slice(0, 19) : ''
}

// 先加载课程下拉，再加载第一门课的资料
const loadCourses = async () => {
  const res = await getCoursePageList({ page: 1, page_size: 100 })
  if (res.code === 200) {
    courseOptions.value = res.data?.list || []
    if (courseOptions.value.length) {
      selectedCourseId.value = courseOptions.value[0].id
      await loadDocuments()
    }
  }
}

const loadDocuments = async () => {
  if (!selectedCourseId.value) {
    documents.value = []
    return
  }
  loading.value = true
  try {
    const res = await getCourseDocList(selectedCourseId.value)
    if (res.code === 200) {
      documents.value = res.data || []
    }
  } finally {
    loading.value = false
  }
}

const beforeUpload = (file) => {
  const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
  const allowed = ['.txt', '.md', '.pdf', '.docx']
  if (!allowed.includes(ext)) {
    ElMessage.error('只支持 .txt / .md / .pdf / .docx 文件')
    return false
  }
  if (file.size > 20 * 1024 * 1024) {
    ElMessage.error('资料不能超过 20MB')
    return false
  }
  return true
}

const handleUpload = async ({ file }) => {
  if (!selectedCourseId.value) {
    ElMessage.warning('请先选择课程')
    return
  }

  uploading.value = true
  try {
    const res = await uploadCourseDocApi(
      file,
      selectedCourseId.value,
      docTitle.value.trim()
    )
    if (res.code === 200) {
      ElMessage.success(
        `上传成功，共切出 ${res.data.chunk_count} 个文本块`
      )
      docTitle.value = ''
      loadDocuments()
    }
  } finally {
    uploading.value = false
  }
}

const handleReindex = async () => {
  reindexing.value = true
  try {
    const res = await reindexCourseDocsApi()
    if (res.code === 200) {
      ElMessage.success(res.message || '重新入库完成')
    }
  } finally {
    reindexing.value = false
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(
    `确认删除资料 [${row.title}]？删除后对应的文本块也会删除。`,
    '确认删除',
    { type: 'warning' }
  )
    .then(async () => {
      const res = await deleteCourseDocApi(row.id)
      if (res.code === 200) {
        ElMessage.success('删除成功')
        loadDocuments()
      }
    })
    .catch(() => {})
}

onMounted(loadCourses)
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.hint {
  margin-top: 12px;
  color: #909399;
  font-size: 12px;
}
</style>
