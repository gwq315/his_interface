<template>
  <el-container style="height: 100vh">
    <el-header style="background-color: #409eff; color: white; display: flex; align-items: center; padding: 0 20px;">
      <h1 style="margin: 0; font-size: 20px;">医院HIS系统接口文档管理系统</h1>
    </el-header>
    <el-container>
      <el-aside width="200px" style="background-color: #f5f5f5; border-right: 1px solid #e4e7ed;">
        <el-menu :default-active="activeMenu" router style="border-right: none;">
          <el-menu-item index="/projects">
            <el-icon>
              <Folder />
            </el-icon>
            <span>项目管理</span>
          </el-menu-item>
          <el-menu-item index="/">
            <el-icon>
              <Document />
            </el-icon>
            <span>接口列表</span>
          </el-menu-item>
          <!-- <el-menu-item index="/interfaces/add">
            <el-icon>
              <Plus />
            </el-icon>
            <span>新增接口</span>
          </el-menu-item> -->
          <el-menu-item index="/dictionaries">
            <el-icon>
              <Collection />
            </el-icon>
            <span>字典管理</span>
          </el-menu-item>
          <el-menu-item index="/documents">
            <el-icon>
              <FolderOpened />
            </el-icon>
            <span>文档/截图</span>
          </el-menu-item>

        </el-menu>
      </el-aside>
      <el-main style="padding: 20px;">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Document, Plus, Collection, Folder, FolderOpened } from '@element-plus/icons-vue'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>
