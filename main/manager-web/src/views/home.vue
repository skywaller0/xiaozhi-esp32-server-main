<template>
  <div class="welcome">
    <!-- 公共头部 -->
    <HeaderBar :devices="devices" />
    <el-main style="padding: 20px;display: flex;flex-direction: column;">
      <div>
        <section class="workspace-hero">
          <div class="workspace-intro">
            <div class="workspace-eyebrow">
              <span class="live-dot"></span>
              {{ $t('home.workspaceLabel') }}
            </div>
            <h1>
              {{ $t('home.greeting') }}<span v-if="userInfo.username">，{{ userInfo.username }}</span>
            </h1>
            <p>{{ $t('home.overviewDescription') }}</p>

            <div class="workspace-actions">
              <div class="search-container">
                <div class="search-wrapper">
                  <el-input
                    ref="searchInput"
                    v-model="search"
                    :placeholder="$t('header.searchPlaceholder')"
                    class="custom-search-input"
                    clearable
                    @keyup.enter.native="handleSearch"
                    @clear="handleSearchReset"
                    @focus="showSearchHistory"
                    @blur="hideSearchHistory"
                  >
                    <i slot="prefix" class="el-icon-search search-icon"></i>
                  </el-input>
                  <div v-if="showHistory && searchHistory.length > 0" class="search-history-dropdown">
                    <div class="search-history-header">
                      <span>{{ $t('header.searchHistory') }}</span>
                      <el-button type="text" size="small" class="clear-history-btn" @click="clearSearchHistory">
                        {{ $t('header.clearHistory') }}
                      </el-button>
                    </div>
                    <div class="search-history-list">
                      <div v-for="(item, index) in searchHistory" :key="index" class="search-history-item"
                        @click.stop="selectSearchHistory(item)">
                        <span class="history-text">{{ item }}</span>
                        <i class="el-icon-close clear-item-icon" @click.stop="removeSearchHistory(index)"></i>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <el-button icon="el-icon-plus" class="add-device-btn" @click="showAddDialog">
                {{ $t('home.addAgent') }}
              </el-button>
            </div>
          </div>

          <aside class="overview-panel">
            <div class="overview-header">
              <span>{{ $t('home.liveOverview') }}</span>
              <span class="system-status"><i></i> ONLINE</span>
            </div>
            <div class="overview-grid">
              <div class="overview-item overview-primary">
                <i class="el-icon-cpu"></i>
                <strong>{{ originalDevices.length }}</strong>
                <span>{{ $t('home.agentsTotal') }}</span>
              </div>
              <div class="overview-item">
                <i class="el-icon-monitor"></i>
                <strong>{{ totalDeviceCount }}</strong>
                <span>{{ $t('home.devicesTotal') }}</span>
              </div>
              <div class="overview-item">
                <i class="el-icon-time"></i>
                <strong>{{ activeAgentCount }}</strong>
                <span>{{ $t('home.activeToday') }}</span>
              </div>
            </div>
          </aside>
        </section>

        <section class="agent-workspace">
          <div class="section-heading">
            <div>
              <span class="section-kicker">AGENT WORKSPACE</span>
              <h2>{{ $t('home.agentWorkspace') }}</h2>
            </div>
            <span class="result-count">{{ devices.length }}</span>
          </div>

          <div class="device-list-container">
          <template v-if="isLoading">
            <div v-for="i in skeletonCount" :key="'skeleton-' + i" class="skeleton-item">
              <div class="skeleton-image"></div>
              <div class="skeleton-content">
                <div class="skeleton-line"></div>
                <div class="skeleton-line-short"></div>
              </div>
            </div>
          </template>

          <template v-else-if="devices.length">
            <DeviceItem v-for="item in devices" :key="item.agentId || item.id" :device="item" :feature-status="featureStatus"
              @configure="goToRoleConfig" @deviceManage="handleDeviceManage" @delete="handleDeleteAgent" 
              @chat-history="handleShowChatHistory" />
          </template>
          <div v-else class="empty-workspace">
            <span class="empty-icon"><i class="el-icon-cpu"></i></span>
            <h3>{{ $t('home.emptyTitle') }}</h3>
            <p>{{ $t('home.emptyDescription') }}</p>
            <el-button type="primary" icon="el-icon-plus" @click="showAddDialog">{{ $t('home.addAgent') }}</el-button>
          </div>
          </div>
        </section>
      </div>
      <AddWisdomBodyDialog :visible.sync="addDeviceDialogVisible" @confirm="handleWisdomBodyAdded" />
      <el-dialog
        :visible.sync="deleteAgentDialogVisible"
        :close-on-click-modal="!isDeletingAgent"
        :close-on-press-escape="!isDeletingAgent"
        :show-close="!isDeletingAgent"
        width="520px"
        append-to-body
        class="delete-agent-dialog"
        @closed="resetDeleteAgentDialog"
      >
        <template slot="title">
          <div class="delete-agent-title">
            <img src="@/assets/knowledge-base/level.png" class="delete-agent-title-icon" />
            <span>{{ $t('home.deleteConfirmTitle') }}</span>
          </div>
        </template>
        <div class="delete-agent-content">
          <i class="el-icon-warning-outline delete-agent-warning"></i>
          <div class="delete-agent-message">
            <div class="delete-agent-copy-guard" @copy.prevent @cut.prevent @contextmenu.prevent>
              {{ $t('home.confirmDeleteAgent', { agentName: deleteTargetAgentName }) }}
            </div>
            <div class="delete-agent-target delete-agent-copy-guard" @copy.prevent @cut.prevent @contextmenu.prevent>
              {{ deleteTargetAgentName }}
            </div>
            <el-input
              ref="deleteAgentConfirmInput"
              v-model="deleteAgentConfirmText"
              class="delete-agent-input"
              :placeholder="$t('home.deleteAgentNamePlaceholder')"
              clearable
              @paste.native.prevent="handleDeleteAgentPaste"
              @drop.native.prevent="handleDeleteAgentPaste"
              @contextmenu.native.prevent
              @keyup.enter.native="confirmDeleteAgent"
            />
            <div v-if="deleteAgentConfirmText && !isDeleteAgentNameMatched" class="delete-agent-helper">
              {{ $t('home.deleteAgentNameMismatch') }}
            </div>
          </div>
        </div>
        <span slot="footer" class="delete-agent-footer">
          <el-button class="delete-agent-cancel" :disabled="isDeletingAgent" @click="closeDeleteAgentDialog">{{ $t('button.cancel') }}</el-button>
          <el-button
            class="delete-agent-confirm"
            type="primary"
            :loading="isDeletingAgent"
            :disabled="!isDeleteAgentNameMatched"
            @click="confirmDeleteAgent"
          >
            {{ $t('button.ok') }}
          </el-button>
        </span>
      </el-dialog>
    </el-main>
    <el-footer>
      <version-footer />
    </el-footer>
    <chat-history-dialog :visible.sync="showChatHistory" :agent-id="currentAgentId" :agent-name="currentAgentName" />
  </div>

</template>

<script>
import Api from '@/apis/api';
import { mapState } from "vuex";
import AddWisdomBodyDialog from '@/components/AddWisdomBodyDialog.vue';
import ChatHistoryDialog from '@/components/ChatHistoryDialog.vue';
import DeviceItem from '@/components/DeviceItem.vue';
import HeaderBar from '@/components/HeaderBar.vue';
import VersionFooter from '@/components/VersionFooter.vue';
import featureManager from '@/utils/featureManager';

export default {
  name: 'HomePage',
  components: { DeviceItem, AddWisdomBodyDialog, HeaderBar, VersionFooter, ChatHistoryDialog },
  data() {
    return {
      addDeviceDialogVisible: false,
      devices: [],
      originalDevices: [],
      isSearching: false,
      searchRegex: null,
      isLoading: true,
      skeletonCount: localStorage.getItem('skeletonCount') || 8,
      showChatHistory: false,
      currentAgentId: '',
      currentAgentName: '',
      // 功能状态
      featureStatus: {
        voiceprintRecognition: false,
        voiceClone: false,
        knowledgeBase: false
      },
      search: "",
      showHistory: false,
      searchHistory: [],
      deleteAgentDialogVisible: false,
      deleteTargetAgentId: '',
      deleteTargetAgentName: '',
      deleteAgentConfirmText: '',
      isDeletingAgent: false,
    }
  },

  computed: {
    ...mapState({
      userInfo: (state) => state.userInfo,
    }),
    isDeleteAgentNameMatched() {
      return !!this.deleteTargetAgentName && this.deleteAgentConfirmText === this.deleteTargetAgentName;
    },
    totalDeviceCount() {
      return this.originalDevices.reduce((total, agent) => total + Number(agent.deviceCount || 0), 0);
    },
    activeAgentCount() {
      const oneDayAgo = Date.now() - 24 * 60 * 60 * 1000;
      return this.originalDevices.filter((agent) => {
        const timestamp = new Date(agent.lastConnectedAt || 0).getTime();
        return Number.isFinite(timestamp) && timestamp >= oneDayAgo;
      }).length;
    },
  },

  async mounted() {
    this.fetchAgentList();
    await this.loadFeatureStatus();
    // 从localStorage加载搜索历史
    this.loadSearchHistory();
  },

  methods: {
    // 加载功能状态
    async loadFeatureStatus() {
      await featureManager.waitForInitialization();
      const config = featureManager.getConfig();
      this.featureStatus = {
        voiceprintRecognition: config.voiceprintRecognition,
        voiceClone: config.voiceClone,
        knowledgeBase: config.knowledgeBase
      };
    },
    
    showAddDialog() {
      this.addDeviceDialogVisible = true
    },
    goToRoleConfig() {
      // 点击配置角色后跳转到角色配置页
      this.$router.push('/role-config')
    },
    handleWisdomBodyAdded(res) {
      this.fetchAgentList();
      this.addDeviceDialogVisible = false;
    },
    handleDeviceManage() {
      this.$router.push('/device-management');
    },
    handleSearchReset() {
      this.isSearching = false;
      // 直接将原始设备列表赋值给显示设备列表，避免重新加载数据
      this.devices = [...this.originalDevices];
    },

    // 搜索更新智能体列表
    handleSearchResult(filteredList) {
      this.devices = filteredList; // 更新设备列表
    },
    // 获取智能体列表
    fetchAgentList() {
      this.isLoading = true;
      Api.agent.getAgentList(({ data }) => {
        if (data?.data) {
          this.originalDevices = data.data.map(item => ({
            ...item,
            agentId: item.id
          }));

          // 动态设置骨架屏数量（可选）
          this.skeletonCount = Math.min(
            Math.max(this.originalDevices.length, 3), // 最少3个
            10 // 最多10个
          );

          this.handleSearchReset();
        }
        this.isLoading = false;
      }, (error) => {
        console.error('Failed to fetch agent list:', error);
        this.isLoading = false;
      });
    },
    // 删除智能体
    handleDeleteAgent(device) {
      const targetAgent = typeof device === 'object'
        ? device
        : this.devices.find((item) => item.agentId === device || item.id === device);
      const agentId = targetAgent?.agentId || targetAgent?.id;
      const agentName = targetAgent?.agentName || '';

      if (!agentId || !agentName) {
        this.$message.error(this.$t('home.deleteAgentMissingInfo'));
        return;
      }

      this.deleteTargetAgentId = agentId;
      this.deleteTargetAgentName = agentName;
      this.deleteAgentConfirmText = '';
      this.deleteAgentDialogVisible = true;
      this.$nextTick(() => {
        if (this.$refs.deleteAgentConfirmInput) {
          this.$refs.deleteAgentConfirmInput.focus();
        }
      });
    },
    handleDeleteAgentPaste() {
      this.$message.warning(this.$t('home.deleteAgentPasteForbidden'));
    },
    closeDeleteAgentDialog() {
      if (this.isDeletingAgent) return;
      this.deleteAgentDialogVisible = false;
    },
    resetDeleteAgentDialog() {
      this.deleteTargetAgentId = '';
      this.deleteTargetAgentName = '';
      this.deleteAgentConfirmText = '';
      this.isDeletingAgent = false;
    },
    confirmDeleteAgent() {
      if (!this.isDeleteAgentNameMatched || this.isDeletingAgent) return;

      this.isDeletingAgent = true;
      Api.agent.deleteAgent(this.deleteTargetAgentId, (res) => {
        this.isDeletingAgent = false;
        if (res.data.code === 0) {
          this.$message.success({
            message: this.$t('home.deleteSuccess'),
            showClose: true
          });
          this.deleteAgentDialogVisible = false;
          this.fetchAgentList(); // 刷新列表
        } else {
          this.$message.error({
            message: res.data.msg || this.$t('home.deleteFailed'),
            showClose: true
          });
        }
      });
    },
    handleShowChatHistory({ agentId, agentName }) {
      this.currentAgentId = agentId;
      this.currentAgentName = agentName;
      this.showChatHistory = true;
    },
    // 处理搜索
    handleSearch() {
      const searchValue = this.search.trim();

      // 如果搜索内容为空，触发重置事件
      if (!searchValue) {
        this.handleSearchReset();
        return;
      }

      // 保存搜索历史
      this.saveSearchHistory(searchValue);

      // 搜索完成后让输入框失去焦点，从而触发blur事件隐藏搜索历史
      if (this.$refs.searchInput) {
        this.$refs.searchInput.blur();
      }

      this.isSearching = true;
      this.isLoading = true;
      // 检测MAC地址格式：包含4个冒号
      const isMac = /^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$/.test(searchValue)
      const searchType = isMac ? 'mac' : 'name';
      Api.agent.searchAgent(searchValue, searchType, ({ data }) => {
        if (data?.data) {
          this.devices = data.data.map(item => ({
            ...item,
            agentId: item.id
          }));
        }
        this.isLoading = false;
      }, (error) => {
        console.error('搜索智能体失败:', error);
        this.isLoading = false;
        this.$message.error(this.$t('message.searchFailed'));
      });
    },

    // 显示搜索历史
    showSearchHistory() {
      this.showHistory = true;
    },

    // 隐藏搜索历史
    hideSearchHistory() {
      // 延迟隐藏，以便点击事件能够执行
      setTimeout(() => {
        this.showHistory = false;
      }, 200);
    },

    // 加载搜索历史
    loadSearchHistory() {
      try {
        const history = localStorage.getItem(this.SEARCH_HISTORY_KEY);
        if (history) {
          this.searchHistory = JSON.parse(history);
        }
      } catch (error) {
        console.error("加载搜索历史失败:", error);
        this.searchHistory = [];
      }
    },

    // 保存搜索历史
    saveSearchHistory(keyword) {
      if (!keyword || this.searchHistory.includes(keyword)) {
        return;
      }

      // 添加到历史记录开头
      this.searchHistory.unshift(keyword);

      // 限制历史记录数量
      if (this.searchHistory.length > this.MAX_HISTORY_COUNT) {
        this.searchHistory = this.searchHistory.slice(0, this.MAX_HISTORY_COUNT);
      }

      // 保存到localStorage
      try {
        localStorage.setItem(this.SEARCH_HISTORY_KEY, JSON.stringify(this.searchHistory));
      } catch (error) {
        console.error("保存搜索历史失败:", error);
      }
    },

    // 选择搜索历史项
    selectSearchHistory(keyword) {
      this.search = keyword;
      this.handleSearch();
    },

    // 移除单个搜索历史项
    removeSearchHistory(index) {
      this.searchHistory.splice(index, 1);
      try {
        localStorage.setItem(this.SEARCH_HISTORY_KEY, JSON.stringify(this.searchHistory));
      } catch (error) {
        console.error("更新搜索历史失败:", error);
      }
    },

    // 清空所有搜索历史
    clearSearchHistory() {
      this.searchHistory = [];
      try {
        localStorage.removeItem(this.SEARCH_HISTORY_KEY);
      } catch (error) {
        console.error("清空搜索历史失败:", error);
      }
    },
  }
}
</script>

<style lang="scss" scoped>
.welcome {
  min-width: 760px;
  min-height: 506px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: transparent;
  background-size: cover;
  /* 确保背景图像覆盖整个元素 */
  background-position: center;
  /* 从顶部中心对齐 */
  -webkit-background-size: cover;
  /* 兼容老版本WebKit浏览器 */
  -o-background-size: cover;
  /* 兼容老版本Opera浏览器 */
}

.add-device {
  height: 228px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 24px;
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at 86% 18%, rgba(20, 184, 166, 0.40), transparent 19rem),
    linear-gradient(128deg, #1b2140 0%, #30376d 52%, #4f51c8 100%);
  box-shadow: 0 22px 55px rgba(35, 39, 85, 0.20);
}

.add-device::after {
  content: "";
  position: absolute;
  width: 340px;
  height: 340px;
  right: -70px;
  top: -190px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 50%;
  box-shadow: 0 0 0 54px rgba(255, 255, 255, 0.035), 0 0 0 108px rgba(255, 255, 255, 0.025);
}

.add-device-bg {
  width: 100%;
  height: 100%;
  text-align: left;
  position: relative;
  z-index: 1;
  background: none;
  /* 确保背景图像覆盖整个元素 */
  background-position: center;
  /* 从顶部中心对齐 */
  -webkit-background-size: cover;
  /* 兼容老版本WebKit浏览器 */
  -o-background-size: cover;
  box-sizing: border-box;

  /* 兼容老版本Opera浏览器 */
  .hellow-text {
    margin-left: 75px;
    color: #fff;
    font-size: 31px;
    font-weight: 700;
    letter-spacing: 0;
  }

  .hi-hint {
    font-weight: 400;
    font-size: 12px;
    text-align: left;
    color: rgba(255, 255, 255, 0.58);
    margin-left: 75px;
    margin-top: 5px;
  }
}

.hero-kicker {
  position: absolute;
  top: 24px;
  left: 75px;
  color: rgba(255, 255, 255, 0.52);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 2px;
}

.hero-metric {
  position: absolute;
  top: 55px;
  right: 72px;
  display: flex;
  flex-direction: column;
  text-align: right;
  color: #fff;

  strong { font-size: 44px; font-weight: 760; line-height: 1; }
  span { margin-top: 7px; color: rgba(255, 255, 255, 0.5); font-size: 9px; letter-spacing: 2px; }
}
.add-device-options {
  display: flex;
  margin-top: 14px;
  margin-left: 75px;
  align-items: center;
}

.add-device-btn {
  color: #fff;
  margin-left: 10px;
  height: 40px;
  border: 1px solid rgba(255, 255, 255, 0.20);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.14);
  box-shadow: none;
  backdrop-filter: blur(10px);
}

.search-container {
  width: 360px;
  margin-right: 5px;
}

.search-wrapper {
  position: relative;
}

.custom-search-input {
  &::v-deep .el-input__inner {
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.18);
    background: rgba(255, 255, 255, 0.95);
    box-shadow: 0 10px 24px rgba(13, 18, 52, 0.14);
  }
  &::v-deep .el-input__suffix {
    right: 10px;
  }
  &::v-deep .el-input__suffix-inner {
    display: flex;
    align-items: center;
    height: 100%;
    cursor: pointer;
  }
  .search-icon {
    font-size: 14px;
  }
}

.search-wrapper {
  position: relative;
}

.search-history-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e4e6ef;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  z-index: 1000;
  margin-top: 2px;
}

.search-history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 12px;
  color: #909399;
}

.clear-history-btn {
  color: #909399;
  font-size: 11px;
  padding: 0;
  height: auto;
}

.clear-history-btn:hover {
  color: #606266;
}

.search-history-list {
  max-height: 200px;
  overflow-y: auto;
}

.search-history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 12px;
  color: #606266;
}

.search-history-item:hover {
  background-color: #f5f7fa;
}

.search-wrapper {
  position: relative;
}

.search-history-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e4e6ef;
  border-radius: 10px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  z-index: 1000;
  margin-top: 6px;
}

.clear-history-btn {
  color: #909399;
  font-size: 12px;
  padding: 0;
  height: auto;
}

.clear-history-btn:hover {
  color: #606266;
}

.search-history-list {
  max-height: 200px;
  overflow-y: auto;
}

.search-history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 12px;
  color: #606266;
}

.search-history-item:hover {
  background-color: #f5f7fa;
}

.search-history-item:hover .clear-item-icon {
  visibility: visible;
}

.clear-item-icon:hover {
  color: #ff4949;
}

.clear-item-icon {
  font-size: 10px;
  color: #909399;
  visibility: hidden;
}

.device-list-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
  padding: 30px 0;
}

/* 在 DeviceItem.vue 的样式中 */
.device-item {
  margin: 0 !important;
  /* 避免冲突 */
  width: auto !important;
}

.footer {
  font-size: 12px;
  font-weight: 400;
  margin-top: auto;
  padding-top: 30px;
  color: #979db1;
  text-align: center;
  /* 居中显示 */
}

/* 骨架屏动画 */
@keyframes shimmer {
  100% {
    transform: translateX(100%);
  }
}

.skeleton-item {
  background: #fff;
  border: 1px solid var(--app-border);
  border-radius: 18px;
  padding: 20px;
  height: 120px;
  position: relative;
  overflow: hidden;
  margin-bottom: 20px;
}

@media (max-width: 980px) {
  .hero-metric { right: 38px; }
  .hero-kicker,
  .add-device-bg .hellow-text,
  .add-device-bg .hi-hint,
  .add-device-options { margin-left: 38px; left: auto; }
}

.skeleton-image {
  width: 80px;
  height: 80px;
  background: #f0f2f5;
  border-radius: 4px;
  float: left;
  position: relative;
  overflow: hidden;
}

.skeleton-content {
  margin-left: 100px;
}

.skeleton-line {
  height: 16px;
  background: #f0f2f5;
  border-radius: 4px;
  margin-bottom: 12px;
  width: 70%;
  position: relative;
  overflow: hidden;
}

.skeleton-line-short {
  height: 12px;
  background: #f0f2f5;
  border-radius: 4px;
  width: 50%;
}

.skeleton-item::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 50%;
  height: 100%;
  background: linear-gradient(90deg,
      rgba(255, 255, 255, 0),
      rgba(255, 255, 255, 0.3),
      rgba(255, 255, 255, 0));
  animation: shimmer 1.5s infinite;
}

.delete-agent-content {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.delete-agent-title {
  display: inline-flex;
  align-items: center;
  font-size: 18px;
  font-weight: 500;
  color: #2f3a5f;
}

.delete-agent-title-icon {
  width: 24px;
  height: 24px;
  margin-right: 8px;
}

.delete-agent-warning {
  color: #e6a23c;
  font-size: 24px;
  margin-top: 4px;
}

.delete-agent-message {
  flex: 1;
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
}

.delete-agent-target {
  margin-top: 14px;
  padding: 10px 12px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  background: #f5f7fa;
  color: #303133;
  font-weight: 600;
  word-break: break-all;
}

.delete-agent-copy-guard {
  user-select: none;
  -webkit-user-select: none;
}

.delete-agent-input {
  margin-top: 16px;
}

.delete-agent-input::v-deep .el-input__inner {
  height: 42px;
  border-color: #d8dce8;
  border-radius: 4px;
  background: #fff;
  color: #303133;
  font-size: 14px;
}

.delete-agent-helper {
  min-height: 18px;
  margin-top: 6px;
  color: #f56c6c;
  font-size: 12px;
}

.delete-agent-footer {
  display: inline-flex;
  gap: 10px;
}

.delete-agent-dialog::v-deep .el-dialog {
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.delete-agent-dialog::v-deep .el-dialog__header {
  padding: 16px 20px 12px;
  background: linear-gradient(135deg, #e2eeff, #edeafe);
  text-align: left;
}

.delete-agent-dialog::v-deep .el-dialog__headerbtn {
  top: 12px;
  right: 16px;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
}

.delete-agent-dialog::v-deep .el-dialog__headerbtn .el-dialog__close {
  font-size: 18px;
  color: #666;
  position: static;
  transform: none;
}

.delete-agent-dialog::v-deep .el-dialog__headerbtn:hover {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.18);
}

.delete-agent-dialog::v-deep .el-dialog__headerbtn:hover .el-dialog__close {
  color: #333;
}

.delete-agent-dialog::v-deep .el-dialog__body {
  padding: 28px 32px 20px;
}

.delete-agent-dialog::v-deep .el-dialog__footer {
  padding: 12px 32px 24px;
}

.delete-agent-cancel,
.delete-agent-confirm {
  min-width: 92px;
  height: 40px;
  padding: 0 20px;
  border-radius: 6px;
  font-size: 15px;
}

.delete-agent-cancel {
  color: #fff;
  background: #4d94f7;
  border: none;
}

.delete-agent-cancel:hover,
.delete-agent-cancel:focus {
  color: #fff;
  background: #4d94f7;
  opacity: 0.88;
}

.delete-agent-confirm {
  background: linear-gradient(to right, #4a7cfd, #8154fc);
  border: none;
}

.delete-agent-confirm:hover,
.delete-agent-confirm:focus {
  background: linear-gradient(to right, #4a7cfd, #8154fc);
  opacity: 0.88;
}

.delete-agent-confirm.is-disabled,
.delete-agent-confirm.is-disabled:hover,
.delete-agent-confirm.is-disabled:focus {
  background: linear-gradient(to right, #4a7cfd, #8154fc);
  border: none;
  opacity: 0.45;
}

/* Modern workspace */
.welcome > .el-main {
  width: min(1760px, 100%);
  margin: 0 auto;
  overflow-y: auto;
}

.workspace-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(360px, 0.8fr);
  gap: 18px;
  min-height: 258px;
}

.workspace-intro,
.overview-panel {
  border: 1px solid var(--app-border);
  border-radius: 22px;
  background: #fff;
  box-shadow: var(--app-shadow-sm);
}

.workspace-intro {
  padding: clamp(28px, 4vw, 48px);
  text-align: left;
  position: relative;
  overflow: hidden;
}

.workspace-intro::after {
  content: "";
  position: absolute;
  width: 260px;
  height: 260px;
  right: -110px;
  bottom: -150px;
  border: 42px solid var(--app-primary-soft);
  border-radius: 50%;
  opacity: 0.75;
  pointer-events: none;
}

.workspace-eyebrow,
.section-kicker {
  color: #8a91a3;
  font-size: 10px;
  font-weight: 750;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.workspace-eyebrow {
  display: flex;
  align-items: center;
  gap: 8px;
}

.live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--app-accent);
  box-shadow: 0 0 0 4px rgba(16, 163, 148, 0.10);
}

.workspace-intro h1 {
  margin: 18px 0 8px;
  color: var(--app-text);
  font-size: clamp(30px, 3vw, 44px);
  font-weight: 760;
  letter-spacing: -0.045em;
  line-height: 1.08;
}

.workspace-intro h1 span {
  color: var(--app-primary);
}

.workspace-intro > p {
  max-width: 620px;
  margin: 0;
  color: var(--app-text-secondary);
  font-size: 14px;
  line-height: 1.7;
}

.workspace-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 26px;
  position: relative;
  z-index: 1;
}

.workspace-actions .search-container {
  width: min(420px, 60vw);
  margin: 0;
}

.workspace-actions .custom-search-input::v-deep .el-input__inner {
  height: 42px;
  padding-left: 38px;
  border-color: var(--app-border);
  border-radius: 12px;
  background: #f8f9fb;
  box-shadow: none;
}

.workspace-actions .add-device-btn {
  height: 42px;
  margin: 0;
  padding: 0 18px;
  border-color: var(--app-primary);
  border-radius: 12px;
  color: #fff;
  background: var(--app-primary);
  box-shadow: 0 5px 12px rgba(70, 87, 232, 0.18);
}

.overview-panel {
  padding: 22px;
  color: #fff;
  background: #172033;
  box-shadow: 0 16px 36px rgba(23, 32, 51, 0.14);
}

.overview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: rgba(255, 255, 255, 0.56);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.system-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #79d9c8;
}

.system-status i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #45c7af;
  box-shadow: 0 0 10px rgba(69, 199, 175, 0.8);
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-top: 20px;
}

.overview-item {
  min-height: 84px;
  padding: 14px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 15px;
  background: rgba(255, 255, 255, 0.055);
  text-align: left;
  position: relative;
}

.overview-primary {
  grid-row: span 2;
  display: flex;
  min-height: 178px;
  flex-direction: column;
  justify-content: flex-end;
  background: linear-gradient(155deg, rgba(70, 87, 232, 0.74), rgba(70, 87, 232, 0.30));
}

.overview-item > i {
  position: absolute;
  top: 14px;
  right: 14px;
  color: rgba(255, 255, 255, 0.55);
  font-size: 17px;
}

.overview-item strong {
  display: block;
  font-size: 29px;
  font-weight: 720;
  letter-spacing: -0.04em;
}

.overview-primary strong {
  font-size: 48px;
}

.overview-item span {
  display: block;
  margin-top: 4px;
  color: rgba(255, 255, 255, 0.54);
  font-size: 10px;
}

.agent-workspace {
  padding-top: 30px;
}

.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: 0 2px;
  text-align: left;
}

.section-heading h2 {
  margin: 6px 0 0;
  color: var(--app-text);
  font-size: 23px;
  font-weight: 720;
  letter-spacing: -0.025em;
}

.result-count {
  min-width: 32px;
  height: 28px;
  padding: 0 10px;
  border: 1px solid var(--app-border);
  border-radius: 999px;
  color: var(--app-text-secondary);
  background: #fff;
  font-size: 12px;
  font-weight: 700;
  line-height: 26px;
  text-align: center;
}

.device-list-container {
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 16px;
  padding: 18px 0 34px;
}

.empty-workspace {
  grid-column: 1 / -1;
  display: flex;
  min-height: 280px;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  border: 1px dashed #d8dce6;
  border-radius: 20px;
  color: var(--app-text-secondary);
  background: rgba(255, 255, 255, 0.58);
}

.empty-icon {
  width: 58px;
  height: 58px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 18px;
  color: var(--app-primary);
  font-size: 24px;
  background: var(--app-primary-soft);
}

.empty-workspace h3 {
  margin: 16px 0 6px;
  color: var(--app-text);
  font-size: 17px;
}

.empty-workspace p {
  margin: 0 0 18px;
  font-size: 13px;
}

@media (max-width: 980px) {
  .workspace-hero {
    grid-template-columns: 1fr;
  }

  .overview-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .overview-primary {
    grid-row: auto;
    min-height: 110px;
  }

  .overview-primary strong {
    font-size: 32px;
  }
}
</style>
