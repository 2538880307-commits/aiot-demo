<template>
  <div class="no-perm-page">
    <el-result icon="warning" title="暂无功能权限" sub-title="当前账号已登录，但未分配任何可访问模块，请联系管理员分配权限。" />
  </div>
</template>

<style scoped>
.no-perm-page {
  min-height: 60vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
