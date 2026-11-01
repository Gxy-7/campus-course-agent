<template>
  <div>
    <el-card>
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <div style="font-size: 16px; font-weight: bold">学习计划</div>
          <el-button type="success" :icon="Plus" @click="handleCreate">
            新建计划
          </el-button>
        </div>
      </template>

      <div v-loading="loading">
        <div v-if="plans.length" class="plan-grid">
          <el-card v-for="plan in plans" :key="plan.id" shadow="hover">
            <div class="plan-head">
              <div class="plan-title">{{ plan.title }}</div>
              <el-tag :type="plan.status === 1 ? 'success' : 'primary'">
                {{ plan.status === 1 ? '已完成' : '进行中' }}
              </el-tag>
            </div>
            <div class="plan-goal">{{ plan.goal || '暂无学习目标' }}</div>
            <div class="plan-date">
              {{ plan.start_date }} 至 {{ plan.end_date }}
            </div>
            <div class="plan-actions">
              <el-button type="primary" text bg @click="handleEdit(plan)">
                编辑
              </el-button>
              <el-button type="danger" text bg @click="handleDelete(plan)">
                删除
              </el-button>
            </div>
          </el-card>
        </div>
        <el-empty v-else description="还没有学习计划，先新建一个吧" />
      </div>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="form.id ? '编辑计划' : '新建计划'"
      width="520"
    >
      <el-form
        ref="formRef"
        :rules="rules"
        :model="form"
        label-width="90px"
        style="padding-right: 20px"
      >
        <el-form-item label="计划标题" prop="title">
          <el-input v-model="form.title" placeholder="例如：期末复习计划" maxlength="100" />
        </el-form-item>
        <el-form-item label="学习目标" prop="goal">
          <el-input
            v-model="form.goal"
            type="textarea"
            :rows="3"
            placeholder="请输入学习目标"
            maxlength="2000"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="计划日期" required>
          <el-date-picker
            v-model="form.dateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="0">进行中</el-radio>
            <el-radio :value="1">已完成</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="formLoading" @click="handleSave">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
defineOptions({ name: 'StudyPlan' })

import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  createStudyPlanApi,
  deleteStudyPlanApi,
  getStudyPlanList,
  updateStudyPlanApi
} from '@/api/studyPlan'

const plans = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref()
const formLoading = ref(false)

// 日期范围用数组保存，提交时拆成 start_date / end_date
const form = reactive({
  id: null,
  title: '',
  goal: '',
  dateRange: [],
  status: 0
})

const rules = {
  title: [{ required: true, message: '请输入计划标题', trigger: 'blur' }]
}

// 加载当前学生的学习计划
const load = async () => {
  loading.value = true
  try {
    const res = await getStudyPlanList()
    if (res.code === 200) plans.value = res.data || []
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  Object.assign(form, {
    id: null,
    title: '',
    goal: '',
    dateRange: [],
    status: 0
  })
  formRef.value?.clearValidate()
}

const handleCreate = () => {
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (plan) => {
  resetForm()
  Object.assign(form, {
    id: plan.id,
    title: plan.title,
    goal: plan.goal || '',
    dateRange: [plan.start_date, plan.end_date],
    status: plan.status
  })
  dialogVisible.value = true
}

const buildPayload = () => ({
  title: form.title,
  goal: form.goal,
  start_date: form.dateRange[0],
  end_date: form.dateRange[1],
  status: form.status
})

const handleSave = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  if (!form.dateRange || form.dateRange.length !== 2) {
    return ElMessage.warning('请选择计划日期范围')
  }

  formLoading.value = true
  try {
    const payload = buildPayload()
    const res = form.id
      ? await updateStudyPlanApi(form.id, payload)
      : await createStudyPlanApi(payload)
    if (res.code === 200) {
      dialogVisible.value = false
      ElMessage.success(form.id ? '修改成功' : '新建成功')
      load()
    }
  } finally {
    formLoading.value = false
  }
}

const handleDelete = (plan) => {
  ElMessageBox.confirm(`确认删除计划 [${plan.title}] ？`, '确认删除', {
    type: 'warning'
  })
    .then(async () => {
      const res = await deleteStudyPlanApi(plan.id)
      if (res.code === 200) {
        ElMessage.success('删除成功')
        load()
      }
    })
    .catch(() => {})
}

onMounted(load)
</script>

<style scoped>
.plan-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}
.plan-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.plan-title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}
.plan-goal {
  min-height: 40px;
  margin-top: 12px;
  color: #606266;
  line-height: 20px;
}
.plan-date {
  margin-top: 12px;
  color: #909399;
  font-size: 13px;
}
.plan-actions {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
