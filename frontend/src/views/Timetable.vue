<template>
  <div>
    <el-card>
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <div style="font-size: 16px; font-weight: bold">我的课表</div>
          <el-select v-model="week" style="width: 120px">
            <el-option v-for="w in 20" :key="w" :label="`第 ${w} 周`" :value="w" />
          </el-select>
        </div>
      </template>

      <template v-if="schedules.length">
        <!-- 显示当前学生选的所有课程 -->
        <div class="course-tags">
          <el-tag v-for="course in courseList" :key="course.course_id" type="info">
            {{ course.course_name }} · {{ course.teacher || '老师待定' }}
          </el-tag>
        </div>

        <div class="timetable-wrap">
          <div class="timetable">
            <div class="corner" :style="{ gridColumn: 1, gridRow: 1 }">节次</div>
            <div
              v-for="day in 7"
              :key="`head-${day}`"
              class="head-cell"
              :style="{ gridColumn: day + 1, gridRow: 1 }"
            >
              {{ weekdayLabel(day) }}
            </div>

            <template v-for="section in 12" :key="`row-${section}`">
              <div
                class="section-cell"
                :style="{ gridColumn: 1, gridRow: section + 1 }"
              >
                第{{ section }}节
              </div>
              <div
                v-for="day in 7"
                :key="`cell-${day}-${section}`"
                class="grid-cell"
                :style="{ gridColumn: day + 1, gridRow: section + 1 }"
              ></div>
            </template>

            <div
              v-for="item in visibleSchedules"
              :key="item.id"
              class="course-block"
              :style="{
                gridColumn: item.weekday + 1,
                gridRow: `${item.start_section + 1} / span ${item.end_section - item.start_section + 1}`
              }"
            >
              <div class="course-name">{{ item.course_name }}</div>
              <div class="course-meta">{{ item.teacher || '老师待定' }}</div>
              <div class="course-meta">{{ item.classroom }}</div>
              <div class="course-meta">{{ weeksLabel(item) }}</div>
            </div>
          </div>
        </div>

        <el-empty
          v-if="!visibleSchedules.length"
          description="这一周没有课"
          :image-size="80"
        />
      </template>

      <el-empty v-else description="还没有选课，先去课程列表选课吧">
        <el-button type="primary" @click="router.push('/manager/course')">
          去选课
        </el-button>
      </el-empty>
    </el-card>
  </div>
</template>

<script setup>
defineOptions({ name: 'Timetable' })

import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getMyScheduleList } from '@/api/schedule'

const router = useRouter()
const schedules = ref([])
const week = ref(1)

const weekdayLabel = (day) =>
  ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日'][day] || ''
const weekTypeLabel = (type) => ['每周', '单周', '双周'][type] || ''
const weeksLabel = (item) => {
  const text =
    item.start_week === item.end_week
      ? `第 ${item.start_week} 周`
      : `${item.start_week}-${item.end_week} 周`
  return item.week_type === 0 ? text : `${text}（${weekTypeLabel(item.week_type)}）`
}

// 判断某个时间段在指定周是否显示
const weekMatches = (item, currentWeek) => {
  if (currentWeek < item.start_week || currentWeek > item.end_week) return false
  if (item.week_type === 1) return currentWeek % 2 === 1
  if (item.week_type === 2) return currentWeek % 2 === 0
  return true
}

// 去重出当前学生选的所有课程
const courseList = computed(() => {
  const map = new Map()
  schedules.value.forEach((item) => {
    if (!map.has(item.course_id)) {
      map.set(item.course_id, {
        course_id: item.course_id,
        course_name: item.course_name,
        teacher: item.teacher
      })
    }
  })
  return [...map.values()]
})

const visibleSchedules = computed(() =>
  schedules.value.filter((item) => weekMatches(item, week.value))
)

const load = async () => {
  const res = await getMyScheduleList()
  if (res.code === 200) schedules.value = res.data || []
}

onMounted(load)
</script>

<style scoped>
.course-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.timetable-wrap {
  overflow-x: auto;
}
.timetable {
  display: grid;
  grid-template-columns: 60px repeat(7, minmax(110px, 1fr));
  grid-template-rows: 40px repeat(12, 72px);
  min-width: 900px;
  border-left: 1px solid #ebeef5;
  border-top: 1px solid #ebeef5;
}
.corner,
.head-cell,
.section-cell,
.grid-cell {
  border-right: 1px solid #ebeef5;
  border-bottom: 1px solid #ebeef5;
  box-sizing: border-box;
}
.corner,
.head-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  font-weight: bold;
}
.section-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
  color: #909399;
  font-size: 12px;
}
.grid-cell {
  background: #fff;
}
.course-block {
  z-index: 2;
  margin: 3px;
  padding: 6px 8px;
  border-left: 3px solid #409eff;
  border-radius: 6px;
  background: #ecf5ff;
  overflow: hidden;
  font-size: 12px;
}
.course-name {
  margin-bottom: 4px;
  color: #409eff;
  font-weight: bold;
}
.course-meta {
  color: #606266;
  line-height: 18px;
}
</style>
