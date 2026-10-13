<template>
  <article class="device-item">
    <header class="agent-header">
      <div class="agent-identity">
        <span class="agent-avatar">{{ agentInitial }}</span>
        <div class="agent-title-group">
          <el-tooltip :content="device.agentName" placement="top" effect="light">
            <h3>{{ device.agentName }}</h3>
          </el-tooltip>
          <span :class="['agent-status', { online: isRecentlyActive }]">
            <i></i>{{ isRecentlyActive ? $t('device.online') : $t('device.offline') }}
          </span>
        </div>
      </div>
      <div class="device-actions">
        <el-tooltip effect="light" :content="device.systemPrompt" placement="top" popper-class="device-item-tooltip">
          <button type="button" class="icon-button" aria-label="查看系统提示词">
            <i class="el-icon-info"></i>
          </button>
        </el-tooltip>
        <button type="button" class="icon-button danger" aria-label="删除智能体" @click.stop="handleDelete">
          <i class="el-icon-delete"></i>
        </button>
      </div>
    </header>

    <div class="model-stack">
      <div class="model-row">
        <span class="model-icon language"><i class="el-icon-chat-dot-round"></i></span>
        <div>
          <small>{{ $t('home.languageModel') }}</small>
          <strong>{{ device.llmModelName || '-' }}</strong>
        </div>
      </div>
      <div class="model-row">
        <span class="model-icon voice"><i class="el-icon-headset"></i></span>
        <div>
          <small>{{ $t('home.voiceModel') }}</small>
          <strong>{{ device.ttsModelName || '-' }}<em v-if="device.ttsVoiceName"> · {{ device.ttsVoiceName }}</em></strong>
        </div>
      </div>
    </div>

    <div class="agent-actions">
      <button type="button" class="action-button primary" @click="handleConfigure">
        <i class="el-icon-setting"></i>{{ $t('home.configureRole') }}
      </button>
      <button type="button" class="action-button" @click="handleDeviceManage">
        <i class="el-icon-monitor"></i>{{ $t('home.deviceManagement') }}
        <span class="action-count">{{ device.deviceCount || 0 }}</span>
      </button>
      <button v-if="featureStatus.voiceprintRecognition" type="button" class="action-button" @click="handleVoicePrint">
        <i class="el-icon-microphone"></i>{{ $t('home.voiceprintRecognition') }}
      </button>
      <button type="button" :class="['action-button', { disabled: device.memModelId === 'Memory_nomem' }]"
        @click="handleChatHistory">
        <i class="el-icon-chat-line-round"></i>{{ $t('home.chatHistory') }}
      </button>
    </div>

    <footer class="agent-footer">
      <span class="last-active"><i class="el-icon-time"></i>{{ formattedLastConnectedTime }}</span>
      <el-tooltip v-if="tags.length" :content="tags.join('、')" placement="top" effect="light">
        <div class="tag-list">
          <span v-for="tag in tags.slice(0, 2)" :key="tag" class="agent-tag">{{ tag }}</span>
          <span v-if="tags.length > 2" class="agent-tag more">+{{ tags.length - 2 }}</span>
        </div>
      </el-tooltip>
    </footer>
  </article>
</template>

<script>
export default {
  name: 'DeviceItem',
  props: {
    device: { type: Object, required: true },
    featureStatus: {
      type: Object,
      default: () => ({
        voiceprintRecognition: false,
        voiceClone: false,
        knowledgeBase: false
      })
    }
  },
  computed: {
    agentInitial() {
      return String(this.device.agentName || 'A').trim().slice(0, 1).toUpperCase();
    },
    isRecentlyActive() {
      const lastTime = new Date(this.device.lastConnectedAt || 0).getTime();
      return Number.isFinite(lastTime) && Date.now() - lastTime <= 10 * 60 * 1000;
    },
    formattedLastConnectedTime() {
      if (!this.device.lastConnectedAt) return this.$t('home.noConversation');

      const lastTime = new Date(this.device.lastConnectedAt);
      const diffMinutes = Math.floor((Date.now() - lastTime.getTime()) / (1000 * 60));
      if (diffMinutes <= 1) return this.$t('home.justNow');
      if (diffMinutes < 60) return this.$t('home.minutesAgo', { minutes: diffMinutes });
      if (diffMinutes < 24 * 60) {
        return this.$t('home.hoursAgo', {
          hours: Math.floor(diffMinutes / 60),
          minutes: diffMinutes % 60
        });
      }
      return this.device.lastConnectedAt;
    },
    tags() {
      return Array.isArray(this.device.tags) ? this.device.tags.map((tag) => tag.tagName).filter(Boolean) : [];
    }
  },
  methods: {
    handleDelete() {
      this.$emit('delete', this.device);
    },
    handleConfigure() {
      this.$router.push({ path: '/role-config', query: { agentId: this.device.agentId } });
    },
    handleVoicePrint() {
      this.$router.push({ path: '/voice-print', query: { agentId: this.device.agentId } });
    },
    handleDeviceManage() {
      this.$router.push({ path: '/device-management', query: { agentId: this.device.agentId } });
    },
    handleChatHistory() {
      if (this.device.memModelId === 'Memory_nomem') return;
      this.$emit('chat-history', { agentId: this.device.agentId, agentName: this.device.agentName });
    }
  }
};
</script>

<style lang="scss" scoped>
.device-item {
  width: 100%;
  padding: 20px;
  border: 1px solid var(--app-border);
  border-radius: 18px;
  background: #fff;
  box-shadow: var(--app-shadow-sm);
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;

  &:hover {
    border-color: #d5d9e4;
    box-shadow: 0 12px 28px rgba(16, 24, 40, 0.08);
    transform: translateY(-2px);
  }
}

.agent-header,
.agent-identity,
.device-actions,
.agent-actions,
.agent-footer,
.tag-list {
  display: flex;
  align-items: center;
}

.agent-header,
.agent-footer {
  justify-content: space-between;
}

.agent-identity {
  min-width: 0;
  gap: 11px;
}

.agent-avatar {
  width: 42px;
  height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 42px;
  border-radius: 13px;
  color: var(--app-primary);
  font-size: 16px;
  font-weight: 760;
  background: var(--app-primary-soft);
}

.agent-title-group {
  min-width: 0;
  text-align: left;
}

.agent-title-group h3 {
  max-width: 220px;
  margin: 0 0 5px;
  overflow: hidden;
  color: var(--app-text);
  font-size: 16px;
  font-weight: 720;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-status {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: #98a0b2;
  font-size: 10px;
  font-weight: 650;
}

.agent-status i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #b9bec9;
}

.agent-status.online {
  color: #088779;
}

.agent-status.online i {
  background: var(--app-accent);
  box-shadow: 0 0 0 3px rgba(16, 163, 148, 0.10);
}

.device-actions {
  gap: 6px;
}

.icon-button {
  width: 31px;
  height: 31px;
  border: 1px solid var(--app-border);
  border-radius: 9px;
  color: #7e8698;
  background: #fff;
  cursor: pointer;
  transition: all 0.18s ease;

  &:hover {
    border-color: #cfd4df;
    color: var(--app-primary);
    background: #f8f9fb;
  }

  &.danger:hover {
    border-color: #ffd4de;
    color: var(--app-danger);
    background: #fff4f6;
  }
}

.model-stack {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin: 18px 0;
}

.model-row {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 9px;
  padding: 11px;
  border: 1px solid #edf0f4;
  border-radius: 12px;
  background: #fafbfc;
  text-align: left;
}

.model-icon {
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 30px;
  border-radius: 9px;
  color: var(--app-primary);
  background: var(--app-primary-soft);
}

.model-icon.voice {
  color: #087c72;
  background: #eaf8f5;
}

.model-row > div {
  min-width: 0;
}

.model-row small,
.model-row strong {
  display: block;
}

.model-row small {
  margin-bottom: 3px;
  color: #98a0b2;
  font-size: 9px;
}

.model-row strong {
  overflow: hidden;
  color: var(--app-text);
  font-size: 11px;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.model-row em {
  color: #8b92a3;
  font-style: normal;
  font-weight: 500;
}

.agent-actions {
  flex-wrap: wrap;
  gap: 7px;
}

.action-button {
  min-height: 31px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 0 10px;
  border: 1px solid var(--app-border);
  border-radius: 9px;
  color: #5f687b;
  background: #fff;
  font-size: 11px;
  font-weight: 620;
  cursor: pointer;
  transition: all 0.18s ease;

  &:hover {
    border-color: #cbd1dc;
    color: var(--app-primary);
    background: #f8f9fb;
  }

  &.primary {
    border-color: var(--app-primary);
    color: #fff;
    background: var(--app-primary);
  }

  &.disabled {
    color: #a8adba;
    background: #f5f6f8;
    cursor: not-allowed;
  }
}

.action-count {
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  color: var(--app-primary);
  background: var(--app-primary-soft);
  font-size: 9px;
  line-height: 18px;
}

.agent-footer {
  min-height: 28px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid #eef0f4;
}

.last-active {
  color: #939aac;
  font-size: 10px;
}

.last-active i {
  margin-right: 5px;
}

.tag-list {
  max-width: 52%;
  gap: 4px;
  overflow: hidden;
}

.agent-tag {
  max-width: 88px;
  padding: 4px 7px;
  overflow: hidden;
  border-radius: 6px;
  color: #747c8e;
  background: #f2f3f6;
  font-size: 9px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-tag.more {
  flex: 0 0 auto;
}

@media (max-width: 460px) {
  .model-stack {
    grid-template-columns: 1fr;
  }
}
</style>

<style>
.device-item-tooltip {
  max-width: 420px !important;
  max-height: 60vh !important;
  overflow-y: auto !important;
  word-break: break-word;
}
</style>
